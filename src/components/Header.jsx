import React from 'react';
import { LocationControl } from './LocationControl';
import { MapPinIcon, SearchIcon } from './Icons';
import { HYDERABAD_LOCALITIES } from '../data/localitiesData';

/**
 * Header Component
 * Contains branding, the unified Location Layer control (Default vs Browser GPS),
 * and quick locality/search controls.
 */
export function Header({ selectedLocality, onSelectLocality, searchQuery, onSearchChange }) {
  return (
    <header className="site-header" role="banner">
      <div className="header-inner container">
        {/* Top Brand & Location Row */}
        <div className="header-top-row">
          <div className="header-brand-block">
            <div className="brand-badge">
              <span className="brand-dot" aria-hidden="true" />
              <span className="brand-tag">HYD V1</span>
            </div>
            <div className="brand-text">
              <h1 className="site-title">TodayNearMe</h1>
              <p className="site-subtitle">Hyderabad Local Information Utility</p>
            </div>
          </div>

          {/* Location Layer Control */}
          <LocationControl />
        </div>

        {/* Secondary Navigation / Locality & Search Bar */}
        <div className="header-controls-row">
          {/* Locality Switcher */}
          <div className="location-control" role="group" aria-label="Hyderabad locality selection">
            <label htmlFor="locality-select" className="visually-hidden">
              Select Hyderabad Locality
            </label>
            <div className="select-wrapper">
              <MapPinIcon className="control-icon" size={15} />
              <select
                id="locality-select"
                className="locality-select"
                value={selectedLocality}
                onChange={(e) => onSelectLocality(e.target.value)}
                aria-label="Filter by Hyderabad area"
              >
                {HYDERABAD_LOCALITIES.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Quick utility search box */}
          <div className="header-search">
            <label htmlFor="global-search" className="visually-hidden">
              Search nearby places or public notices
            </label>
            <div className="search-input-wrapper">
              <SearchIcon className="control-icon" size={15} />
              <input
                id="global-search"
                type="search"
                className="header-search-input"
                placeholder="Search places or notices..."
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                autoComplete="off"
              />
              {searchQuery && (
                <button
                  type="button"
                  className="clear-search-btn"
                  onClick={() => onSearchChange('')}
                  aria-label="Clear search query"
                >
                  ×
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
