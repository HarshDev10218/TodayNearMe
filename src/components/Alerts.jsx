import React from 'react';
import { ShieldCheckIcon, AlertTriangleIcon, PhoneIcon } from './Icons';

/**
 * Alerts Component
 * Clearly separates normal information from urgent public warnings.
 * Includes a subtle state switcher so the user/architect can inspect both:
 * 1) 'No active alerts'
 * 2) 'Heavy rain warning'
 */
export function Alerts({ alertsState, isWarningSimulated, onToggleWarningSimulation }) {
  const current = isWarningSimulated ? alertsState.activeWarningState : alertsState.normalState;
  const isAlertActive = current.hasAlert;

  return (
    <section
      id="section-alerts"
      className={`alerts-section card ${isAlertActive ? 'alert-card-warning' : 'alert-card-normal'}`}
      aria-labelledby="alerts-heading"
    >
      <div className="section-title-bar">
        <div>
          <h2 id="alerts-heading" className="section-title">
            Public Safety &amp; Weather Alerts
          </h2>
          <p className="section-subtitle">
            Monitored via IMD Hyderabad, GHMC Disaster Cell &amp; TSDPS
          </p>
        </div>

        {/* State preview toggle for design & prototype inspection */}
        <div className="state-simulator-control">
          <span className="simulator-label">Preview State:</span>
          <button
            type="button"
            className={`simulator-toggle-btn ${!isWarningSimulated ? 'active' : ''}`}
            onClick={() => onToggleWarningSimulation(false)}
            aria-pressed={!isWarningSimulated}
          >
            Normal (No alerts)
          </button>
          <button
            type="button"
            className={`simulator-toggle-btn warning-toggle ${isWarningSimulated ? 'active' : ''}`}
            onClick={() => onToggleWarningSimulation(true)}
            aria-pressed={isWarningSimulated}
          >
            Heavy Rain Warning
          </button>
        </div>
      </div>

      {/* Alert Content Box */}
      {!isAlertActive ? (
        // Normal State
        <div className="alert-content-box normal-box" role="status" aria-live="polite">
          <div className="alert-banner-line">
            <span className="status-badge badge-normal">
              <ShieldCheckIcon size={16} /> {current.badge}
            </span>
            <span className="timestamp-note">{current.lastVerified}</span>
          </div>

          <h3 className="alert-box-headline">{current.headline}</h3>
          <p className="alert-box-description">{current.description}</p>

          <div className="normal-contact-bar">
            <span className="contact-prompt">Standard civic control:</span>
            {current.contacts.map((c, i) => (
              <span key={i} className="contact-chip">
                {c.name}: <strong>{c.number}</strong>
              </span>
            ))}
          </div>
        </div>
      ) : (
        // Active Warning State
        <div className="alert-content-box warning-box" role="alert" aria-live="assertive">
          <div className="alert-banner-line">
            <span className="status-badge badge-warning">
              <AlertTriangleIcon size={16} /> {current.badge}
            </span>
            <span className="validity-tag">
              Valid until <strong>{current.validUntil}</strong>
            </span>
          </div>

          <h3 className="alert-box-headline warning-headline">{current.headline}</h3>
          <p className="alert-meta-author">
            Issued by {current.issuedBy} • Effective from {current.validFrom}
          </p>

          <p className="alert-box-description warning-description">{current.summary}</p>

          {/* Affected Localities */}
          <div className="alert-affected-block">
            <h4 className="alert-subheading">Zones under weather advisory:</h4>
            <div className="affected-zones-chips" role="list">
              {current.affectedZones.map((zone, idx) => (
                <span key={idx} className="zone-pill" role="listitem">
                  {zone}
                </span>
              ))}
            </div>
          </div>

          {/* Advisory Guidelines */}
          <div className="alert-guidelines-block">
            <h4 className="alert-subheading">Recommended public precautions:</h4>
            <ul className="guidelines-list">
              {current.guidelines.map((guide, idx) => (
                <li key={idx}>{guide}</li>
              ))}
            </ul>
          </div>

          {/* Emergency Helpline Numbers */}
          <div className="alert-emergency-helplines">
            <h4 className="alert-subheading">Emergency Assistance Contacts:</h4>
            <div className="helplines-grid">
              {current.emergencyContacts.map((contact, idx) => (
                <a
                  key={idx}
                  href={`tel:${contact.tel}`}
                  className="helpline-card"
                  aria-label={`Call ${contact.label} at ${contact.tel}`}
                >
                  <PhoneIcon size={14} className="helpline-icon" />
                  <span className="helpline-name">{contact.label}</span>
                  <strong className="helpline-number">{contact.tel}</strong>
                </a>
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
