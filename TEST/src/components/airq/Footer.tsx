"use client";

import { Wind } from "lucide-react";

const footerLinks = [
  { label: "About", href: "/about" },
  { label: "Project Details", href: "/about#project" },
  { label: "Developer Credits", href: "/about#credits" },
];

import { useNavigate, useLocation, Link } from "react-router-dom";

export default function Footer() {
  const location = useLocation();

  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-layout">
          {/* Brand */}
          <div className="footer-brand">
            <div className="footer-logo-icon">
              <Wind />
            </div>
            <span className="footer-brand-title">
              <span className="footer-brand-p1">Air</span>
              <span className="footer-brand-p2">Q</span>
            </span>
            <span className="footer-brand-subtitle">AI Air Quality Prediction</span>
          </div>

          {/* Links */}
          <nav className="footer-nav">
            {footerLinks.map((link) => (
              <Link
                key={link.label}
                to={link.href}
                className="footer-link"
              >
                {link.label}
              </Link>
            ))}
          </nav>

          {/* Copyright */}
          <div className="footer-copyright-group">
            <p className="footer-copyright">
              © 2026 AirQ. Developed by{" "}
              <Link 
                to="/about#credits" 
                className="footer-dev-credit"
              >
                <span>Pratham Kumar Gupta</span> & Team
              </Link>
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
