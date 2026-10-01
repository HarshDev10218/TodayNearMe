import React, { useState } from 'react';
import { useLocation } from '../hooks/useLocation';
import { MapPinIcon, CrosshairIcon, RotateCcwIcon, InfoIcon } from './Icons';

/**
 * LocationControl Component
 * Displays current location status (default vs browser location),
 * provides explicit "Use my location" trigger, explains why location is needed,
 * and gracefully displays friendly fallback status.
 */
export function LocationControl() {
  const { location, requestLocation, resetToDefault, dismissError } = useLocation();
  const [showInfo, setShowInfo] = useState(false);

  const isBrowserMode = location.mode === 'browser';
  const hasCoordinates = location.latitude !== null && location.longitude !== null;

  return (
    <div className="location-control-panel" role="region" aria-label="Location control">
      <div className="location-info-row">
        <div className="location-text-block">
          <div className="location-primary-line">
            <MapPinIcon size={16} className="location-pin-icon" />
            <span className="location-city">{location.city}</span>
            {isBrowserMode ? (
              <span className="location-mode-badge mode-browser" title="Using coordinates from browser GPS">
                <span className="live-dot" aria-hidden="true" />
                Using your location
              </span>
            ) : (
              <span className="location-mode-badge mode-default" title="Default Hyderabad location">
                Default location
              </span>
            )}
          </div>
          <div className="location-sub-line">
            <span className="location-region">{location.state}, {location.country}</span>
            {isBrowserMode && hasCoordinates && (
              <span className="location-coords">
                • {location.latitude > 0 ? `${location.latitude}° N` : `${Math.abs(location.latitude)}° S`},{' '}
                {location.longitude > 0 ? `${location.longitude}° E` : `${Math.abs(location.longitude)}° W`}
                {location.accuracy && <span className="coords-acc"> (±{location.accuracy}m)</span>}
              </span>
            )}
          </div>
        </div>

        {/* Action button: Request location or Reset */}
        <div className="location-action-wrap">
          {!isBrowserMode ? (
            <button
              type="button"
              className="use-location-btn"
              onClick={requestLocation}
              disabled={location.isLoading}
              aria-label="Use my current browser location"
            >
              <CrosshairIcon size={14} className={location.isLoading ? 'spin-icon' : ''} />
              <span>{location.isLoading ? 'Detecting location...' : 'Use my location'}</span>
            </button>
          ) : (
            <button
              type="button"
              className="reset-location-btn"
              onClick={resetToDefault}
              aria-label="Reset back to default Hyderabad location"
            >
              <RotateCcwIcon size={13} />
              <span>Reset to default</span>
            </button>
          )}

          {/* Micro explanation toggle / note */}
          {!isBrowserMode && !location.isLoading && (
            <button
              type="button"
              className="location-why-btn"
              onClick={() => setShowInfo((prev) => !prev)}
              aria-expanded={showInfo}
              aria-label="Why is location needed?"
              title="Why does TodayNearMe need your location?"
            >
              <InfoIcon size={13} />
              <span className="why-text">Why needed?</span>
            </button>
          )}
        </div>
      </div>

      {/* Explanatory notice shown on user request */}
      {showInfo && !isBrowserMode && (
        <div className="location-privacy-note" role="note">
          <p>
            Your coordinates are only used in this browser session to pinpoint accurate local weather and nearby emergency services. They are never saved, tracked, or sent to a server.
          </p>
          <button
            type="button"
            className="dismiss-note-btn"
            onClick={() => setShowInfo(false)}
            aria-label="Close information"
          >
            Got it
          </button>
        </div>
      )}

      {/* Graceful fallback / error feedback */}
      {location.error && (
        <div className="location-error-alert" role="status" aria-live="polite">
          <span className="error-message">{location.error}</span>
          <button
            type="button"
            className="dismiss-error-btn"
            onClick={dismissError}
            aria-label="Dismiss location notice"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}
