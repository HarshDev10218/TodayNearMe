import React from 'react';
import { ShieldCheckIcon, AlertTriangleIcon, RotateCcwIcon } from './Icons';

/**
 * WeatherAlerts Component
 * Displays real-time official weather alerts from the backend (/api/alerts).
 * Handles loading, error, normal (no alerts), and active warning states
 * with transparent official source attribution.
 */
export function WeatherAlerts({ alertsData, isLoading, isRefreshing, error, onRefresh }) {
  // 1. Loading State (clean and calm)
  if (isLoading && !alertsData) {
    return (
      <section id="section-alerts" className="alerts-section card alert-card-normal" aria-labelledby="alerts-heading">
        <div className="section-title-bar">
          <div>
            <h2 id="alerts-heading" className="section-title">
              Official Weather Alerts
            </h2>
            <p className="section-subtitle">Connecting to meteorological alert service</p>
          </div>
        </div>
        <div className="alerts-status-box" role="status" aria-live="polite">
          <p className="alerts-status-text">Checking weather alerts...</p>
        </div>
      </section>
    );
  }

  // 2. Error State (graceful fallback without dashboard disruption)
  if (error && !alertsData) {
    return (
      <section id="section-alerts" className="alerts-section card alert-card-normal" aria-labelledby="alerts-heading">
        <div className="section-title-bar">
          <div>
            <h2 id="alerts-heading" className="section-title">
              Official Weather Alerts
            </h2>
            <p className="section-subtitle">Authoritative government meteorological warnings</p>
          </div>
        </div>
        <div className="alerts-status-box alerts-status-error" role="status">
          <p className="alerts-status-text">Weather alerts unavailable right now.</p>
          {onRefresh && (
            <button type="button" className="alerts-retry-btn" onClick={onRefresh}>
              Retry
            </button>
          )}
        </div>
      </section>
    );
  }

  // Fallback guard
  if (!alertsData) {
    return null;
  }

  const hasAlerts = alertsData.has_active_alerts && alertsData.alerts && alertsData.alerts.length > 0;
  const isCached = alertsData.cached;

  // Format timestamp for display
  const formatTime = (isoString) => {
    if (!isoString) return '';
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString('en-IN', { hour: 'numeric', minute: '2-digit', hour12: true });
    } catch {
      return isoString;
    }
  };

  return (
    <section
      id="section-alerts"
      className={`alerts-section card ${hasAlerts ? 'alert-card-warning' : 'alert-card-normal'}`}
      aria-labelledby="alerts-heading"
    >
      <div className="section-title-bar">
        <div>
          <h2 id="alerts-heading" className="section-title">
            Official Weather Alerts
          </h2>
          <p className="section-subtitle">
            Authoritative bulletins monitored via India Meteorological Department (IMD)
          </p>
        </div>

        <div className="alerts-header-actions">
          {isCached && (
            <span className="cached-badge" title="Served from 10-minute cache">
              Cached
            </span>
          )}
          {onRefresh && (
            <button
              type="button"
              className="weather-refresh-btn"
              onClick={onRefresh}
              disabled={isRefreshing}
              aria-label="Refresh weather alerts"
              title="Refresh weather alerts"
            >
              <RotateCcwIcon size={12} className={isRefreshing ? 'spin-icon' : ''} />
              <span>{isRefreshing ? 'Checking...' : 'Refresh'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Alert Content Box */}
      {!hasAlerts ? (
        // 3. Normal State: No Active Alerts (Quiet, reassuring, NOT an error)
        <div className="alert-content-box normal-box" role="status" aria-live="polite">
          <div className="alert-banner-line">
            <span className="status-badge badge-normal">
              <ShieldCheckIcon size={16} /> Normal Conditions
            </span>
            <span className="timestamp-note">
              Checked {formatTime(alertsData.checked_at) || 'recently'}
            </span>
          </div>

          <h3 className="alert-box-headline">No Active Weather Alerts</h3>
          <p className="alert-box-description">
            No active weather alerts were found for the selected location from the monitored IMD data source.
          </p>

          <div className="alert-source-footer">
            <span className="source-label">Source:</span>{' '}
            <span className="source-name">
              {alertsData.source_status || 'India Meteorological Department (IMD)'}
            </span>
          </div>
        </div>
      ) : (
        // 4. Active Alert State: Render Each Verified Alert
        <div className="active-alerts-container" role="alert" aria-live="assertive">
          {alertsData.alerts.map((alert) => (
            <div
              key={alert.id}
              className={`alert-content-box warning-box alert-severity-${alert.severity}`}
            >
              <div className="alert-banner-line">
                <span className={`status-badge badge-${alert.severity}`}>
                  <AlertTriangleIcon size={16} /> Warning • {alert.severity.toUpperCase()}
                </span>
                {alert.end_time && (
                  <span className="validity-tag">
                    Valid until <strong>{formatTime(alert.end_time)}</strong>
                  </span>
                )}
              </div>

              <h3 className="alert-box-headline warning-headline">{alert.title}</h3>

              {alert.area_desc && (
                <p className="alert-meta-areas">
                  <strong>Affected Area:</strong> {alert.area_desc}
                </p>
              )}

              <p className="alert-box-description warning-description">{alert.description}</p>

              <div className="alert-source-footer">
                <span className="source-label">Source:</span>{' '}
                <span className="source-name">
                  {alert.source || 'India Meteorological Department (IMD)'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
