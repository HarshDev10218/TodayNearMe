import React, { useState, useMemo } from 'react';
import { SUPPORTED_PLACE_CATEGORIES } from '../hooks/usePlaces';
import { NavigationIcon, SearchIcon, MapPinIcon } from './Icons';

/**
 * Nearby Component
 * Displays real-time nearby public amenities and services sourced from OpenStreetMap
 * via the TodayNearMe FastAPI backend. Sorted strictly by proximity to user coordinates.
 */
export function Nearby({
  places = [],
  placesData = null,
  selectedCategory = 'hospital',
  onSelectCategory,
  isLoading = false,
  error = null,
  onRefresh,
}) {
  const [localSearch, setLocalSearch] = useState('');

  // Human-readable active category label
  const activeCategoryObj = SUPPORTED_PLACE_CATEGORIES.find((c) => c.id === selectedCategory);
  const activeCategoryLabel = activeCategoryObj ? activeCategoryObj.label : 'Places';

  // Filter returned places by local search refinement field if typed
  const filteredPlaces = useMemo(() => {
    if (!localSearch.trim()) {
      return places;
    }
    const query = localSearch.trim().toLowerCase();
    return places.filter((place) => {
      const nameMatch = place.name?.toLowerCase().includes(query);
      const addrMatch = place.address?.toLowerCase().includes(query);
      return nameMatch || addrMatch;
    });
  }, [places, localSearch]);

  return (
    <section id="section-nearby" className="nearby-section card" aria-labelledby="nearby-heading">
      {/* Title & Attribution Header */}
      <div className="section-title-bar">
        <div>
          <h2 id="nearby-heading" className="section-title">
            Nearby Public Places
          </h2>
          <p className="section-subtitle">
            Public amenities &amp; essential facilities near your location
          </p>
        </div>
        <div className="section-header-meta">
          {!isLoading && !error && (
            <span className="count-pill" aria-label={`${filteredPlaces.length} places found`}>
              {filteredPlaces.length} {activeCategoryLabel.toLowerCase()}
            </span>
          )}
        </div>
      </div>

      {/* Category Selection Bar */}
      <div
        className="category-filter-bar"
        role="tablist"
        aria-label="Filter nearby places by public category"
      >
        {SUPPORTED_PLACE_CATEGORIES.map((cat) => {
          const isActive = selectedCategory === cat.id;
          return (
            <button
              key={cat.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              className={`filter-pill-btn ${isActive ? 'active' : ''}`}
              onClick={() => {
                if (onSelectCategory) {
                  onSelectCategory(cat.id);
                }
              }}
            >
              {cat.label}
            </button>
          );
        })}
      </div>

      {/* Local Filter Field (shown when data is loaded) */}
      {!isLoading && !error && places.length > 0 && (
        <div className="nearby-search-field">
          <label htmlFor="nearby-filter-input" className="visually-hidden">
            Filter places by name or address
          </label>
          <div className="search-input-wrapper">
            <SearchIcon size={15} className="control-icon" />
            <input
              id="nearby-filter-input"
              type="search"
              className="nearby-filter-input"
              placeholder={`Filter ${activeCategoryLabel.toLowerCase()} by name or locality...`}
              value={localSearch}
              onChange={(e) => setLocalSearch(e.target.value)}
            />
            {localSearch && (
              <button
                type="button"
                className="clear-search-btn"
                onClick={() => setLocalSearch('')}
                aria-label="Clear nearby filter"
              >
                ×
              </button>
            )}
          </div>
        </div>
      )}

      {/* Content States: Loading, Error, Empty, or Places Grid */}
      {isLoading ? (
        <div className="nearby-loading-box" role="status" aria-live="polite">
          <p className="nearby-loading-text">
            Finding nearby {activeCategoryLabel.toLowerCase()}...
          </p>
        </div>
      ) : error ? (
        <div className="error-state-box" role="alert">
          <p className="error-title">Nearby places are unavailable right now.</p>
          <p className="error-message">
            Unable to connect to the public places service. Your weather and alerts continue working normally.
          </p>
          {onRefresh && (
            <button
              type="button"
              className="reset-filter-btn"
              onClick={onRefresh}
              style={{ marginTop: '10px' }}
            >
              Retry
            </button>
          )}
        </div>
      ) : filteredPlaces.length === 0 ? (
        <div className="empty-state-box">
          <p className="empty-state-title">
            No nearby {activeCategoryLabel.toLowerCase()} found.
          </p>
          <p className="empty-state-text">
            {localSearch
              ? 'No places matched your search query. Try clearing the filter.'
              : `No public ${activeCategoryLabel.toLowerCase()} were mapped within search radius for this location.`}
          </p>
          {localSearch ? (
            <button
              type="button"
              className="reset-filter-btn"
              onClick={() => setLocalSearch('')}
            >
              Clear Filter
            </button>
          ) : (
            <button
              type="button"
              className="reset-filter-btn"
              onClick={() => onSelectCategory && onSelectCategory('hospital')}
            >
              Show Hospitals
            </button>
          )}
        </div>
      ) : (
        <div className="places-grid" role="list">
          {filteredPlaces.map((place) => (
            <article key={place.id} className="place-card" role="listitem">
              <div className="place-card-top">
                <div className="place-badges-row">
                  <span className={`category-tag tag-${place.category}`}>
                    {place.category_label || activeCategoryLabel}
                  </span>
                  <span className="distance-badge" title="Approximate straight-line distance">
                    <MapPinIcon size={12} /> {place.distance_formatted}
                  </span>
                </div>
                <span className="place-source-tag">
                  {place.source}
                </span>
              </div>

              <h3 className="place-name">{place.name}</h3>

              {place.address && (
                <div className="place-address-block">
                  <p className="place-address">{place.address}</p>
                </div>
              )}

              {/* Action: Open in map view using verified coordinates */}
              <div className="place-actions">
                <a
                  href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
                    place.latitude + ',' + place.longitude
                  )}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="action-btn action-btn-dir"
                  aria-label={`View ${place.name} on map`}
                >
                  <NavigationIcon size={14} />
                  <span>View on Map</span>
                </a>
              </div>
            </article>
          ))}
        </div>
      )}

      {/* Attribution Footer (OpenStreetMap ODbL compliance) */}
      <div className="nearby-footer-attribution">
        <span className="attribution-text">
          Data ©{' '}
          <a
            href="https://www.openstreetmap.org/copyright"
            target="_blank"
            rel="noopener noreferrer"
            className="attribution-link"
          >
            OpenStreetMap contributors
          </a>{' '}
          (ODbL)
        </span>
        {placesData?.cached && (
          <span className="cached-badge" title="Served from 15-minute in-memory backend cache">
            Cached
          </span>
        )}
      </div>
    </section>
  );
}
