import requests
from dotenv import load_dotenv

load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="AIRQ Prediction API", description="FastAPI Migration for AQI Deteoriation System")

# API Configuration (Get free token at https://aqicn.org/data-platform/token/)
AQI_API_TOKEN = os.getenv("AQI_API_TOKEN", "demo") # "demo" gives limited access to some cities

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Models
try:
    rf_1h, rf_24h, metadata = load_models()
    FEATURES = metadata['features']
    CITIES_SUPPORTED = metadata['cities']
    IS_DUMMY = metadata.get('is_dummy', False)
    logger.info(f"Loaded {'DUMMY ' if IS_DUMMY else ''}Random Forest models successfully!")
except Exception as e:
    logger.error(f"Failed to load models: {e}")
    # Fallback to local paths if needed or re-raise
    raise e

# Load Dataset for Historical Data
try:
    CSV_PATH = os.path.join(os.path.dirname(__file__), 'india_aqi_v6_2024-2025.csv')
    df = pd.read_csv(CSV_PATH)
    # Convert datetime for filtering
    df['datetime_dt'] = pd.to_datetime(df['datetime'], errors='coerce')
    logger.info("Successfully loaded historical dataset.")
except Exception as e:
    logger.error(f"Failed to load dataset: {e}")
    df = pd.DataFrame()

# --- Helper Functions ---

def fetch_live_aqi(city: str):
    """Fetches real-time AQI and weather from WAQI API"""
    try:
        url = f"https://api.waqi.info/feed/{city}/?token={AQI_API_TOKEN}"
        resp = requests.get(url, timeout=5)
        res = resp.json()
        if res['status'] == 'ok':
            data = res['data']
            return {
                'aqi': float(data['aqi']),
                'temp': float(data['iaqi'].get('t', {}).get('v', 25)),
                'humidity': float(data['iaqi'].get('h', {}).get('v', 50)),
                'wind': float(data['iaqi'].get('w', {}).get('v', 10)),
                'time': data['time']['s']
            }
    except Exception as e:
        logger.error(f"Live API Fetch Error: {e}")
    return None

# --- Pydantic Models ---

class PredictionRequest(BaseModel):
    city: str = Field(..., example="Delhi")
    currentAqi: float
    aqi1h: float
    aqi24h: float
    temperature: float
    precipitation: float
    windSpeed: float
    hour: int
    month: int

class DataPoint(BaseModel):
    time: str
    aqi: float
    isPredicted: bool

class ForecastResponse(BaseModel):
    city: str
    data: List[DataPoint]

# --- Helper Functions ---

def get_aqi_category(aqi: float) -> str:
    if aqi <= 50:    return "Good"
    elif aqi <= 100: return "Satisfactory"
    elif aqi <= 200: return "Moderate"
    elif aqi <= 300: return "Poor"
    elif aqi <= 400: return "Very Poor"
    else:            return "Severe"

# --- API Routes ---

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "models_loaded": True,
        "is_dummy_model": IS_DUMMY,
        "cities": CITIES_SUPPORTED
    }

@app.post("/predict")
async def predict(req: PredictionRequest):
    try:
        # Construct dataframe dynamically matching trained features
        input_data = {
            'AQI':              [req.currentAqi],
            'Temperature_C':    [req.temperature],
            'Precipitation_mm': [req.precipitation],
            'WindSpeed_kmh':    [req.windSpeed],
            'hour':             [req.hour],
            'month':            [req.month],
            'AQI_lag1':         [req.aqi1h],
            'AQI_lag24':        [req.aqi24h],
            'city_Delhi':       [1 if req.city == 'Delhi' else 0],
            'city_Hyderabad':   [1 if req.city == 'Hyderabad' else 0],
            'city_Kolkata':     [1 if req.city == 'Kolkata' else 0],
            'city_Mumbai':      [1 if req.city == 'Mumbai' else 0],
        }

        # Check if city is one of the supported columns, if not, handle it
        # The trained model might only have 4 city columns. 
        # If city not in [Delhi, Hyderabad, Kolkata, Mumbai], all stay 0.

        input_df = pd.DataFrame(input_data)[FEATURES]

        pred_1h = round(float(rf_1h.predict(input_df)[0]), 1)
        pred_24h = round(float(rf_24h.predict(input_df)[0]), 1)

        return {
            'city': req.city,
            'oneHour': pred_1h,
            'twentyFourHour': pred_24h,
            'category_1h': get_aqi_category(pred_1h),
            'category_24h': get_aqi_category(pred_24h),
            'model_accuracy_1h': metadata.get('accuracy_1h', 0),
            'model_accuracy_24h': metadata.get('accuracy_24h', 0),
            'is_dummy_model': IS_DUMMY
        }
    except Exception as e:
        logger.exception("Error during prediction")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/forecast", response_model=ForecastResponse)
async def forecast(city: str = "Delhi"):
    """
    Returns 6 hours of historical data and 24 hours of prediction
    """
    try:
        if df.empty:
            raise HTTPException(status_code=503, detail="Dataset not available for historical data")

        # 1. Attempt Live Fetch from WAQI (The Internet)
        live_data = fetch_live_aqi(city)
        if live_data:
            logger.info(f"Using LIVE data from internet for {city}")
            current_aqi = live_data['aqi']
            current_temp = live_data['temp']
            current_wind = live_data['wind']
            current_time = pd.to_datetime(live_data['time'])
        else:
            logger.info(f"Using simulated data from CSV for {city} (Live API fallback)")
            city_data = df[df['city'] == city].sort_values(by='datetime_dt', ascending=False)
            if city_data.empty:
                raise HTTPException(status_code=404, detail=f"No data found for city: {city}")
            latest_row = city_data.iloc[0]
            current_aqi = float(latest_row['AQI'])
            current_temp = float(latest_row['Temperature_C'])
            current_wind = float(latest_row['WindSpeed_kmh'])
            current_time = latest_row['datetime_dt']

        # 2. Get Historical Context from CSV (last 6 points)
        city_hist = df[df['city'] == city].sort_values(by='datetime_dt', ascending=False)
        history_rows = city_hist.iloc[1:7][::-1] 
        
        data_points = []
        for _, h_row in history_rows.iterrows():
            data_points.append(DataPoint(
                time=(h_row['datetime_dt']).strftime("%H:%M"),
                aqi=float(h_row['AQI']),
                isPredicted=False
            ))
            
        # 3. Add the "Current" Point (Live or Simulated)
        data_points.append(DataPoint(
            time=current_time.strftime("%H:%M"),
            aqi=current_aqi,
            isPredicted=False
        ))

        # 4. Generate Predictions for next 24 hours
        def predict_point(aqi_val, hr, mon):
            # Simplified mock prediction logic for trend
            input_dict = {
                'AQI': [aqi_val], 'Temperature_C': [current_temp], 
                'Precipitation_mm': [0], 'WindSpeed_kmh': [current_wind],
                'hour': [hr], 'month': [mon], 'AQI_lag1': [aqi_val], 'AQI_lag24': [aqi_val],
                'city_Delhi': [1 if city == 'Delhi' else 0], 'city_Hyderabad': [1 if city == 'Hyderabad' else 0],
                'city_Kolkata': [1 if city == 'Kolkata' else 0], 'city_Mumbai': [1 if city == 'Mumbai' else 0],
            }
            idf = pd.DataFrame(input_dict)[FEATURES]
            p1 = rf_1h.predict(idf)[0]
            p24 = rf_24h.predict(idf)[0]
            return p1, p24

        hr, mon = current_time.hour, current_time.month
        p1, p24 = predict_point(current_aqi, hr, mon)
        
        # Build smooth trend
        base_time = current_time
        data_points.append(DataPoint(
            time=(base_time + timedelta(hours=1)).strftime("%H:%M"),
            aqi=round(float(p1), 1),
            isPredicted=True
        ))
        
        for h in range(4, 25, 4):
            ratio = (h - 1) / 23
            interpolated_aqi = p1 + (p24 - p1) * ratio
            data_points.append(DataPoint(
                time=(base_time + timedelta(hours=h)).strftime("%H:%M"),
                aqi=round(float(interpolated_aqi), 1),
                isPredicted=True
            ))

        return ForecastResponse(city=city, data=data_points)

        return ForecastResponse(city=city, data=data_points)

    except Exception as e:
        logger.exception("Error during forecast generation")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
