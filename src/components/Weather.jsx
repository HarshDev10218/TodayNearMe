import React from 'react';
import { CloudRainIcon, RotateCcwIcon } from './Icons';

/**
 * Weather Component
 * Displays real-time normalized weather metrics from our FastAPI backend,
 * with clean loading, error fallback, and manual refresh controls.
 */
export function Weather({ weather, isLoading, isRefreshing, error, onRefresh }) {
  // 1. Initial Loading State (clean and calm)
  if (isLoading && !weather) {
    return (
      <section id="section-weather" className="weather-section card" aria-labelledby="weather-heading">
        <div className="section-title-bar">
          <div>
            <h2 id="weather-heading" className="section-title">
              Local Weather
            </h2>
            <p className="section-subtitle">Connecting to TodayNearMe weather service</p>
          </div>
        </div>
        <div className="weather-status-box" role="status" aria-live="polite">
          <p className="weather-status-text">Loading weather...</p>
        </div>
      </section>
    );
  }

  // 2. Error State (graceful fallback without dashboard disruption)
  if (error && !weather) {
    return (
      <section id="section-weather" className="weather-section card" aria-labelledby="weather-heading">
        <div className="section-title-bar">
          <div>
            <h2 id="weather-heading" className="section-title">
              Local Weather
            </h2>
            <p className="section-subtitle">Real-time local meteorological data</p>
          </div>
        </div>
        <div className="weather-status-box weather-status-error" role="status">
          <p className="weather-status-text">Weather unavailable right now.</p>
          {onRefresh && (
            <button type="button" className="weather-retry-btn" onClick={onRefresh}>
              Retry
            </button>
          )}
        </div>
      </section>
    );
  }

  // Fallback safety guard if weather data is empty
  if (!weather || !weather.current) {
    return null;
  }

  const { current, hourly = [], forecast = [], location, observed_at, source, cached } = weather;

  // Normalized field fallbacks
  const temp = current.temperature ?? current.tempC ?? '--';
  const feelsLike = current.feels_like ?? current.feelsLikeC ?? temp;
  const tempHigh = current.temp_high ?? current.tempHighC ?? '--';
  const tempLow = current.temp_low ?? current.tempLowC ?? '--';
  const condition = current.condition || 'Clear';
  const rainProb = current.precipitation_probability ?? current.rainProbability ?? 0;
  const humidity = current.humidity ?? '--';
  const windSpeed = current.wind_speed ?? current.windSpeedKmh ?? '--';
  const windDir = current.wind_direction ?? 'WNW';
  const pressure = current.surface_pressure ?? current.pressureHpa ?? 1012;

  return (
    <section id="section-weather" className="weather-section card" aria-labelledby="weather-heading">
      <div className="section-title-bar">
        <div>
          <h2 id="weather-heading" className="section-title">
            {location?.label || 'Hyderabad Weather'}
          </h2>
          <p className="section-subtitle">
            Source: {source || 'Open-Meteo'} • Observed{' '}
            <span className="meta-time">{observed_at || 'Just now'}</span>
          </p>
        </div>

        <div className="weather-header-actions">
          {cached && (
            <span className="cached-badge" title="Served from 10-minute cache">
              Cached
            </span>
          )}
          <span className="live-indicator-tag" aria-label="Status: Current report">
            Live Data
          </span>
          {onRefresh && (
            <button
              type="button"
              className="weather-refresh-btn"
              onClick={onRefresh}
              disabled={isRefreshing}
              aria-label="Refresh weather data"
              title="Refresh weather data"
            >
              <RotateCcwIcon size={12} className={isRefreshing ? 'spin-icon' : ''} />
              <span>{isRefreshing ? 'Updating...' : 'Refresh'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Temperature & Primary Metrics Display */}
      <div className="weather-primary-display">
        <div className="temp-hero">
          <div className="temp-hero-main">
            <span className="temp-digit">{temp}°</span>
            <span className="temp-unit">C</span>
          </div>
          <div className="temp-hero-details">
            <span className="temp-condition">{condition}</span>
            <span className="temp-feels">Feels like {feelsLike}°C</span>
            <div className="temp-high-low">
              <span>H: {tempHigh}°C</span>
              <span className="temp-sep">/</span>
              <span>L: {tempLow}°C</span>
            </div>
          </div>
        </div>

        {/* Rain Probability Banner */}
        <div className="rain-probability-card" role="region" aria-label="Precipitation Probability">
          <div className="rain-header">
            <CloudRainIcon size={18} className="rain-icon" />
            <span className="rain-label">Precipitation Chance</span>
            <span className="rain-value">{rainProb}%</span>
          </div>
          <div className="rain-bar-track" aria-hidden="true">
            <div
              className="rain-bar-fill"
              style={{ width: `${Math.max(rainProb, 6)}%` }}
            />
          </div>
          <p className="rain-hint">
            {rainProb > 40
              ? 'Rain likely in the area. Keep an umbrella handy.'
              : 'Low precipitation chance for the next several hours.'}
          </p>
        </div>
      </div>

      {/* Secondary Metrics Grid */}
      <div className="weather-metrics-grid" role="list" aria-label="Additional weather parameters">
        <div className="metric-box" role="listitem">
          <span className="metric-title">Humidity</span>
          <span className="metric-val">{humidity}%</span>
          <span className="metric-sub">Relative moisture</span>
        </div>

        <div className="metric-box" role="listitem">
          <span className="metric-title">Wind</span>
          <span className="metric-val">
            {windSpeed} <small>km/h</small>
          </span>
          <span className="metric-sub">{windDir} direction</span>
        </div>

        <div className="metric-box" role="listitem">
          <span className="metric-title">Pressure</span>
          <span className="metric-val">
            {pressure} <small>hPa</small>
          </span>
          <span className="metric-sub">Atmospheric</span>
        </div>

        <div className="metric-box" role="listitem">
          <span className="metric-title">Precipitation</span>
          <span className="metric-val">{rainProb}%</span>
          <span className="metric-sub">Probability</span>
        </div>
      </div>

      {/* Hourly Forecast */}
      {hourly && hourly.length > 0 && (
        <div className="hourly-forecast-wrapper">
          <h3 className="subheading">Hourly Forecast</h3>
          <div className="hourly-scroll-strip" role="list" aria-label="Upcoming hourly forecast">
            {hourly.map((hour, idx) => (
              <div key={idx} className="hourly-item" role="listitem">
                <span className="hourly-time">{hour.time}</span>
                <span className="hourly-temp">{hour.temperature ?? hour.tempC}°</span>
                <span className="hourly-cond">{hour.condition}</span>
                <span className="hourly-rain" title="Precipitation probability">
                  <CloudRainIcon size={12} /> {hour.precipitation_probability ?? hour.rainProb ?? 0}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3-Day Forecast Table */}
      {forecast && forecast.length > 0 && (
        <div className="threeday-forecast-wrapper">
          <h3 className="subheading">3-Day Outlook</h3>
          <div className="forecast-table" role="table" aria-label="Three day outlook table">
            <div className="forecast-table-header" role="row">
              <span role="columnheader">Day</span>
              <span role="columnheader">Condition</span>
              <span role="columnheader">Rain Prob.</span>
              <span role="columnheader" className="text-right">Max / Min</span>
            </div>
            {forecast.map((item, idx) => (
              <div key={idx} className="forecast-table-row" role="row">
                <div className="forecast-day-col" role="cell">
                  <strong>{item.day}</strong>
                  <span className="forecast-date-sub">{item.date}</span>
                </div>
                <div className="forecast-cond-col" role="cell">
                  {item.condition}
                </div>
                <div className="forecast-rain-col" role="cell">
                  <span className="rain-badge">{item.rain_probability ?? item.rainProb ?? 0}%</span>
                </div>
                <div className="forecast-temp-col text-right" role="cell">
                  <span className="temp-high">{item.temp_max ?? item.tempMax}°</span>
                  <span className="temp-sep">/</span>
                  <span className="temp-low">{item.temp_min ?? item.tempMin}°</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
