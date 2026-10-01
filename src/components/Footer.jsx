import React from 'react';
import { PhoneIcon } from './Icons';

const currentYear = new Date().getFullYear();

/**
 * Footer Component
 * Provides emergency telephone directory, civic disclaimer, and version indicator.
 */
export function Footer() {
  return (
    <footer className="site-footer" role="contentinfo">
      <div className="container footer-inner">
        {/* Quick Emergency Numbers Strip */}
        <div className="emergency-strip" aria-label="Hyderabad Emergency Numbers">
          <span className="emergency-strip-title">Emergency Helplines:</span>
          <div className="emergency-chips-row">
            <a href="tel:108" className="emergency-chip" aria-label="Ambulance Emergency 108">
              <PhoneIcon size={12} />
              <span>Medical / Ambulance: <strong>108</strong></span>
            </a>
            <a href="tel:100" className="emergency-chip" aria-label="Police Helpline 100">
              <PhoneIcon size={12} />
              <span>Police: <strong>100</strong></span>
            </a>
            <a href="tel:101" className="emergency-chip" aria-label="Fire Emergency 101">
              <PhoneIcon size={12} />
              <span>Fire &amp; Rescue: <strong>101</strong></span>
            </a>
            <a href="tel:04021111111" className="emergency-chip" aria-label="GHMC Disaster Cell 040-21111111">
              <PhoneIcon size={12} />
              <span>GHMC Monsoon/Disaster: <strong>040-21111111</strong></span>
            </a>
            <a href="tel:1091" className="emergency-chip" aria-label="Women Helpline 1091">
              <PhoneIcon size={12} />
              <span>Women Helpline: <strong>1091</strong></span>
            </a>
          </div>
        </div>

        {/* Footer Bottom Info */}
        <div className="footer-bottom">
          <div className="footer-brand-meta">
            <p className="footer-title">
              <strong>TodayNearMe</strong> — Hyderabad Local Information Utility (V1)
            </p>
            <p className="footer-description">
              A free, non-commercial public information interface. Curates public weather data, civic notices, and essential community amenities for residents of Hyderabad and Secunderabad.
            </p>
          </div>
          <div className="footer-credits">
            <p className="footer-note">Designed for high legibility, low bandwidth, and phone accessibility.</p>
            <p className="footer-copy">© {currentYear} TodayNearMe. Public civic utility prototype.</p>
          </div>
        </div>
      </div>
    </footer>
  );
}
