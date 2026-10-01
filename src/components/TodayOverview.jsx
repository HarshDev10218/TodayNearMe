import React from 'react';
import { useLocation } from '../hooks/useLocation';
import { SunIcon, ShieldCheckIcon, AlertTriangleIcon, InfoIcon, ClockIcon } from './Icons';

const todayDate = new Date();
const formattedCurrentDate = new Intl.DateTimeFormat('en-IN', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
  year: 'numeric'
}).format(todayDate);
const isoDateString = todayDate.toISOString().slice(0, 10);

/**
 * TodayOverview Component
 * Summarizes the day at a glance: Date, Location, Day Brief, and quick status tiles.
 */
export function TodayOverview({ weather, alertsState, civicCount, selectedLocalityName, onNavigateSection }) {
  const { location } = useLocation();
  const hasWarning = alertsState.hasAlert;

  const locationDisplay = location.mode === 'browser'
    ? `${location.city} (Current Location)`
    : `${location.city}, ${location.state}`;

  return (
    <section className="overview-section card" aria-labelledby="overview-heading">
      <div className="overview-header">
        <div className="overview-meta">
          <span className={`location-pill ${location.mode === 'browser' ? 'location-pill-live' : ''}`}>
            {locationDisplay}
          </span>
          <span className="meta-separator">•</span>
          <time className="overview-date" dateTime={isoDateString}>
            {formattedCurrentDate}
          </time>
        </div>
        <div className="overview-context-scope">
          <span className="scope-label">Focus Area:</span>{' '}
          <strong className="scope-value">
            {location.mode === 'browser' && location.latitude !== null
              ? `${selectedLocalityName} • GPS Active`
              : selectedLocalityName}
          </strong>
        </div>
      </div>

      <div className="overview-body">
        <h2 id="overview-heading" className="overview-title">
          Today's City Brief
        </h2>
        <p className="overview-summary">
          Hyderabad is experiencing a warm day with partly cloudy skies and a low rain probability (15%). Air quality remains in the Moderate band (AQI 76). Major arterial roads and metro rail corridors report normal operations. Note scheduled HMWS&amp;SB water pipeline maintenance in parts of Central Zone.
        </p>

        {/* Glance Status Grid */}
        <div className="glance-grid" role="list" aria-label="Key indicators for today">
          <div className="glance-item" role="listitem">
            <div className="glance-icon-wrap glance-icon-weather" aria-hidden="true">
              <SunIcon size={18} />
            </div>
            <div className="glance-info">
              <span className="glance-label">Weather Glance</span>
              <span className="glance-value">
                {weather?.current
                  ? `${weather.current.temperature ?? weather.current.tempC}°C • ${weather.current.condition}`
                  : 'Updating weather...'}
              </span>
              <span className="glance-subtext">
                {weather?.current
                  ? `${weather.current.precipitation_probability ?? weather.current.rainProbability ?? 0}% rain chance`
                  : 'Connecting to live service'}
              </span>
            </div>
          </div>

          <div
            className={`glance-item ${hasWarning ? 'glance-item-warning' : 'glance-item-ok'}`}
            role="listitem"
          >
            <div className="glance-icon-wrap" aria-hidden="true">
              {hasWarning ? <AlertTriangleIcon size={18} /> : <ShieldCheckIcon size={18} />}
            </div>
            <div className="glance-info">
              <span className="glance-label">Alert Status</span>
              <span className="glance-value">
                {hasWarning ? 'Active Weather Warning' : 'Normal Conditions'}
              </span>
              <span className="glance-subtext">
                {hasWarning ? 'Heavy rain advisory in effect' : 'No emergency alerts'}
              </span>
            </div>
          </div>

          <div className="glance-item" role="listitem">
            <div className="glance-icon-wrap glance-icon-civic" aria-hidden="true">
              <InfoIcon size={18} />
            </div>
            <div className="glance-info">
              <span className="glance-label">Public Notices</span>
              <span className="glance-value">{civicCount} Notices Active</span>
              <span className="glance-subtext">Water maintenance &amp; transit</span>
            </div>
          </div>

          <div className="glance-item" role="listitem">
            <div className="glance-icon-wrap glance-icon-clock" aria-hidden="true">
              <ClockIcon size={18} />
            </div>
            <div className="glance-info">
              <span className="glance-label">Essential Care</span>
              <span className="glance-value">24/7 Units Operational</span>
              <span className="glance-subtext">NIMS, Osmania, Apollo open</span>
            </div>
          </div>
        </div>

        {/* Quick jump navigation for swift mobile access */}
        <nav className="quick-jump-nav" aria-label="Jump to section">
          <span className="quick-jump-label">Jump to:</span>
          <div className="quick-jump-buttons">
            <button
              type="button"
              className="quick-jump-btn"
              onClick={() => onNavigateSection('section-weather')}
            >
              Weather
            </button>
            <button
              type="button"
              className="quick-jump-btn"
              onClick={() => onNavigateSection('section-alerts')}
            >
              Alerts
            </button>
            <button
              type="button"
              className="quick-jump-btn"
              onClick={() => onNavigateSection('section-nearby')}
            >
              Nearby Places
            </button>
            <button
              type="button"
              className="quick-jump-btn"
              onClick={() => onNavigateSection('section-events')}
            >
              Events
            </button>
            <button
              type="button"
              className="quick-jump-btn"
              onClick={() => onNavigateSection('section-civic')}
            >
              Civic Updates
            </button>
          </div>
        </nav>
      </div>
    </section>
  );
}
