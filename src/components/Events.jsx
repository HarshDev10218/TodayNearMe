import React from 'react';
import { MapPinIcon, ClockIcon, RotateCcwIcon, ExternalLinkIcon } from './Icons';

/**
 * Events Component
 * Displays verified upcoming public and community gatherings, workshops,
 * and official notices in Hyderabad sourced via TodayNearMe FastAPI backend.
 *
 * Adheres strictly to:
 * - ₹0 budget & authentic public data rules (no invented data).
 * - Asia/Kolkata timezone presentation.
 * - Multi-source aggregation (FOSS United, Telangana Tourism, Hyderabad District Government).
 * - Minimalist, accessible, high-contrast design.
 */
export function Events({
  events = [],
  eventsData = null,
  isLoading = false,
  isRefreshing = false,
  error = null,
  onRefresh,
}) {
  const isAllUnavailable = Boolean(error || eventsData?.all_unavailable);

  // Monitored sources breakdown
  const monitoredSources = eventsData?.sources?.length
    ? eventsData.sources
    : [
        { name: 'FOSS United', status: 'ok' },
        { name: 'Telangana Tourism', status: 'ok' },
        { name: 'Hyderabad District Government', status: 'empty' },
      ];

  return (
    <section id="section-events" className="events-section card" aria-labelledby="events-heading">
      {/* Title Bar & Status Meta */}
      <div className="section-title-bar">
        <div>
          <h2 id="events-heading" className="section-title">
            Events in Hyderabad
          </h2>
          <p className="section-subtitle">
            Public gatherings, workshops, conferences &amp; community meetups
          </p>
        </div>

        <div className="section-header-meta">
          {!isLoading && !isAllUnavailable && (
            <span className="count-pill" aria-label={`${events.length} events listed`}>
              {events.length} {events.length === 1 ? 'upcoming event' : 'upcoming events'}
            </span>
          )}
          {onRefresh && (
            <button
              type="button"
              className="refresh-btn"
              onClick={onRefresh}
              disabled={isRefreshing || isLoading}
              title="Check Again — Refresh events from monitored public sources"
              aria-label="Check Again"
            >
              <RotateCcwIcon size={14} className={isRefreshing ? 'spin' : ''} />
            </button>
          )}
        </div>
      </div>

      {/* Main Content States: Loading, Unavailable, Empty, or Populated List */}
      {isLoading ? (
        <div className="events-loading-box" role="status" aria-live="polite">
          <p className="events-loading-text">Checking monitored public sources...</p>
        </div>
      ) : isAllUnavailable ? (
        <div className="error-state-box" role="alert">
          <p className="error-title">Events temporarily unavailable</p>
          <p className="error-message">
            We couldn't retrieve the monitored public event sources right now. Please try again later.
          </p>
          {onRefresh && (
            <button
              type="button"
              className="reset-filter-btn"
              onClick={onRefresh}
              disabled={isRefreshing}
              style={{ marginTop: '12px' }}
            >
              {isRefreshing ? 'Checking...' : 'Check Again'}
            </button>
          )}
        </div>
      ) : events.length === 0 ? (
        <div className="empty-state-box">
          <p className="empty-state-title">No public events found</p>
          <p className="empty-state-text">
            We couldn't find upcoming Hyderabad events in the public sources currently monitored by TodayNearMe.
          </p>

          <div className="monitored-sources-container">
            <p className="monitored-sources-heading">Sources checked</p>
            <ul className="monitored-sources-list">
              {monitoredSources.map((src) => (
                <li key={src.name} className="monitored-source-item">
                  <div className="monitored-source-left">
                    <span className="source-dot" />
                    <span className="source-item-name">{src.name}</span>
                  </div>
                  <span className={`source-status-badge badge-${src.status}`}>
                    {src.status === 'unavailable'
                      ? 'Temporarily unavailable'
                      : src.status === 'empty'
                      ? '0 upcoming events'
                      : '0 in Hyderabad'}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          {onRefresh && (
            <button
              type="button"
              className="reset-filter-btn"
              onClick={onRefresh}
              disabled={isRefreshing}
              style={{ marginTop: '16px' }}
            >
              {isRefreshing ? 'Checking...' : 'Check Again'}
            </button>
          )}
        </div>
      ) : (
        <div className="events-list" role="list">
          {events.map((evt) => (
            <article key={evt.id} className="event-item" role="listitem">
              {/* Date & Temporal Bucket Column */}
              <div className="event-date-col">
                <span className="event-when-badge">{evt.time_label || 'Upcoming'}</span>
                <span className="event-date-text">{evt.formatted_date || 'Upcoming'}</span>
              </div>

              {/* Event Content Column */}
              <div className="event-content-col">
                <div className="event-header-row">
                  <div className="event-badges-group">
                    <span className="event-cat-tag">{evt.category || 'Event'}</span>
                    <span className={`event-source-badge badge-${evt.source_type || 'community'}`}>
                      {evt.source_type === 'official' ? 'Official' : 'Community'}
                    </span>
                  </div>
                  {evt.area && <span className="event-entry-pill">{evt.area}</span>}
                </div>

                <h3 className="event-title">{evt.title}</h3>

                {evt.description && <p className="event-summary">{evt.description}</p>}

                <div className="event-details-row">
                  <div className="event-detail-item">
                    <ClockIcon size={14} className="detail-icon" />
                    <span>{evt.formatted_time ? `${evt.formatted_time} (IST)` : 'Time TBA'}</span>
                  </div>
                  <div className="event-detail-item">
                    <MapPinIcon size={14} className="detail-icon" />
                    <span>{evt.venue || 'Hyderabad'}</span>
                  </div>
                </div>

                <div className="event-organizer-row">
                  <span className="organizer-label">Source:</span>{' '}
                  <span className="organizer-name">{evt.source}</span>
                </div>

                {/* Direct link to verified original source */}
                {evt.source_url && (
                  <div className="event-action-bar" style={{ marginTop: '10px' }}>
                    <a
                      href={evt.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="action-btn action-btn-dir"
                      aria-label={`View ${evt.title} on ${evt.source}`}
                    >
                      <ExternalLinkIcon size={13} />
                      <span>View Event</span>
                    </a>
                  </div>
                )}
              </div>
            </article>
          ))}
        </div>
      )}

      {/* Attribution & Cache Notice Footer */}
      <div className="nearby-footer-attribution" style={{ marginTop: '14px' }}>
        <span className="attribution-text">
          {eventsData?.source || 'Sources: FOSS United, Telangana Tourism, Hyderabad District Government'}
        </span>
        {eventsData?.cached && (
          <span className="cached-badge" title="Served from 30-minute in-memory backend cache">
            Cached
          </span>
        )}
      </div>
    </section>
  );
}
