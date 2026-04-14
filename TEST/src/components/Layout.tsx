import { Outlet, useLocation } from "react-router-dom";
import { useEffect } from "react";
import CursorTrail from "@/components/airq/CursorTrail";
import Navbar from "@/components/airq/Navbar";
import Footer from "@/components/airq/Footer";

export default function Layout() {
    const location = useLocation();

    useEffect(() => {
        if (location.hash) {
            const id = location.hash.replace("#", "");
            setTimeout(() => {
                const el = document.getElementById(id);
                if (el) {
                    el.scrollIntoView({ behavior: "smooth" });
                }
            }, 100); 
        } else {
            // Instantly scroll to top when changing page without a hash fragment
            window.scrollTo(0, 0);
        }
    }, [location]);

    return (
        <div className="layout-wrapper">
            <CursorTrail />
            <Navbar />
            <main className="layout-main">
                <Outlet />
            </main>
            <Footer />
        </div>
    );
}
