"use client";

import { Wind } from "lucide-react";

const footerLinks = [
  { label: "About", href: "#about" },
  { label: "Project Details", href: "#project" },
  { label: "Developer Credits", href: "#credits" },
];

import { useNavigate, useLocation } from "react-router-dom";

export default function Footer() {
  const navigate = useNavigate();
  const location = useLocation();

  const handleNav = (e: React.MouseEvent, href: string) => {
    e.preventDefault();
    const id = href.replace("#", "");

    if (location.pathname === "/") {
      const el = document.getElementById(id);
      if (el) {
        el.scrollIntoView({ behavior: "smooth" });
      }
    } else {
      navigate(`/${href}`);
    }
  };

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
              <a
                key={link.label}
                href={link.href}
                onClick={(e) => handleNav(e, link.href)}
                className="footer-link"
              >
                {link.label}
              </a>
            ))}
          </nav>

          {/* Copyright */}
          <div className="footer-copyright-group">
            <p className="footer-copyright">
              © 2026 AirQ. Developed by{" "}
              <a 
                href="#credits" 
                onClick={(e) => handleNav(e, "#credits")}
                className="footer-dev-credit"
              >
                <span>Pratham Kumar Gupta</span> & Team
              </a>
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
