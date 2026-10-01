import React from 'react';
import { CalendarIcon, RotateCcwIcon, ExternalLinkIcon } from './Icons';

/**
 * CivicUpdates Component
 * Displays verified official civic notices and public updates from:
 *   - GHMC (Greater Hyderabad Municipal Corporation)
 *   - Hyderabad District Government (NIC / S3WaaS portal)
 *   - Government of Telangana (official state portal RSS — Hyderabad-relevant items only)
 *
 * Rules:
 * - No fabricated data. Source link takes user to the original official page.
 * - Official source label is always visible.
 * - Aggregator disclaimer always shown.
 * - ₹0 budget, no AI, no unofficial sources.
 */

/**
 * Converts a category string to a CSS class suffix.
 * e.g. "Public Safety" -> "public-safety"
 */
function categoryClass(category) {
  if (!category) return 'other';
  return category.toLowerCase().replace(/\s+/g, '-');
}

/**
 * Formats an ISO datetime string to a readable IST date.
 * e.g. "2026-09-22T00:00:00+05:30" -> "22 Sep 2026"
 */
function formatDate(isoStr) {
  if (!isoStr) return null;
  try {
    const d = new Date(isoStr);
    return d.toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      timeZone: 'Asia/Kolkata',
    });
  } catch {
    return null;
  }
}

export function CivicUpdates({
  updates = [],
  civicData = null,
  isLoading = false,
  isRefreshing = false,
  error = null,
  onRefresh,
}) {
  const isAllUnavailable = Boolean(error || civicData?.all_unavailable);

  const monitoredSources = civicData?.sources?.length
    ? civicData.sources
    : [
        { name: 'GHMC', status: 'ok' },
        { name: 'Hyderabad District Government', status: 'ok' },
        { name: 'Government of Telangana', status: 'ok' },
      ];

  const checkedAt = civicData?.checked_at
    ? new Date(civicData.checked_at).toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Asia/Kolkata',
        hour12: true,
      })
    : null;

  return (
    <section
      id="section-civic"
      className="card"
      aria-labelledby="civic-heading"
    >
      {/* Title Bar */}
      <div className="section-title-bar">
        <div>
          <h2 id="civic-heading" className="section-title">
            Civic Notices &amp; Public Updates
          </h2>
          <p className="section-subtitle">
            Official municipal notices, district advisories &amp; government announcements
          </p>
        </div>

        <div className="section-header-meta">
          {!isLoading && !isAllUnavailable && updates.length > 0 && (
            <span className="count-pill" aria-label={`${updates.length} notices listed`}>
              {updates.length} {updates.length === 1 ? 'notice' : 'notices'}
            </span>
          )}
          {onRefresh && (
            <button
              type="button"
              className="refresh-btn"
              onClick={onRefresh}
              disabled={isRefreshing || isLoading}
              title="Check Again — Refresh from monitored official sources"
              aria-label="Check Again"
            >
              <RotateCcwIcon size={14} className={isRefreshing ? 'spin' : ''} />
            </button>
          )}
        </div>
      </div>

      {/* Content States */}
      {isLoading ? (
        <div className="civic-loading-box" role="status" aria-live="polite">
          <p className="civic-loading-text">Checking official public sources...</p>
        </div>
      ) : isAllUnavailable ? (
        <div className="error-state-box" role="alert">
          <p className="error-title">Public updates temporarily unavailable</p>
          <p className="error-message">
            We couldn&apos;t retrieve the monitored official sources right now. Please try again later.
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
      ) : updates.length === 0 ? (
        <div className="empty-state-box">
          <p className="empty-state-title">No recent public updates found</p>
          <p className="empty-state-text">
            We couldn&apos;t find recent Hyderabad-relevant civic notices in the official public sources currently
            monitored by TodayNearMe.
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
                      ? 'No notices found'
                      : src.status === 'not_supported'
                      ? 'Not supported'
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
        <>
          <div className="civic-updates-list" role="list">
            {updates.map((item) => {
              const catClass = categoryClass(item.category);
              const pubDate = formatDate(item.published_at);
              const isStatewide = item.location === 'Telangana (Statewide)';

              return (
                <article
                  key={item.id}
                  className={`civic-update-item cat-${catClass}`}
                  role="listitem"
                >
                  {/* Top meta row */}
                  <div className="civic-update-meta-row">
                    <div className="civic-update-left-meta">
                      {/* Category tag */}
                      <span className="civic-cat-tag">{item.category}</span>

                      {/* Official source chip */}
                      <span className="civic-official-chip">
                        Official Government Source
                      </span>

                      {/* Statewide scope indicator */}
                      {isStatewide && (
                        <span className={`civic-location-scope scope-statewide`}>
                          Telangana-wide
                        </span>
                      )}
                    </div>

                    {/* Date */}
                    {pubDate && (
                      <div className="civic-update-date-row">
                        <CalendarIcon size={12} />
                        <time>{pubDate}</time>
                      </div>
                    )}
                  </div>

                  {/* Title */}
                  <h3 className="civic-update-title">{item.title}</h3>

                  {/* Summary — only if source provides it */}
                  {item.summary && (
                    <p className="civic-update-summary">{item.summary}</p>
                  )}

                  {/* Deadline badge */}
                  {item.deadline && (
                    <div>
                      <span className="civic-deadline-badge">
                        Deadline: {item.deadline}
                      </span>
                    </div>
                  )}

                  {/* Footer: source + view link */}
                  <div className="civic-update-footer">
                    <div className="civic-source-attribution">
                      Source:{' '}
                      <span className="civic-source-name-text">{item.source}</span>
                    </div>

                    <a
                      href={item.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="civic-view-link"
                      aria-label={`View official notice: ${item.title}`}
                    >
                      View official notice
                      <ExternalLinkIcon size={12} />
                    </a>
                  </div>
                </article>
              );
            })}
          </div>

          {/* Source status list (non-zero) */}
          {civicData?.sources && civicData.sources.some((s) => s.status !== 'ok') && (
            <div className="monitored-sources-container" style={{ marginTop: '14px' }}>
              <p className="monitored-sources-heading">Source status</p>
              <ul className="monitored-sources-list">
                {civicData.sources.map((src) => (
                  <li key={src.name} className="monitored-source-item">
                    <div className="monitored-source-left">
                      <span className="source-dot" />
                      <span className="source-item-name">{src.name}</span>
                    </div>
                    <span className={`source-status-badge badge-${src.status}`}>
                      {src.status === 'unavailable'
                        ? 'Temporarily unavailable'
                        : src.status === 'empty'
                        ? 'No notices found'
                        : src.status === 'not_supported'
                        ? 'Not supported'
                        : 'OK'}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Checked time */}
          {checkedAt && (
            <p className="civic-checked-at">
              Checked at {checkedAt} IST
              {civicData?.cached && ' (cached)'}
            </p>
          )}

          {/* Aggregator disclaimer */}
          <div className="civic-disclaimer">
            TodayNearMe aggregates publicly available information from official sources.
            Always verify important details on the original source before acting on them.
          </div>
        </>
      )}
    </section>
  );
}
