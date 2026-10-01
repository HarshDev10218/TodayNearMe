import React, { useState } from 'react';
import { Header } from '../components/Header';
import { TodayOverview } from '../components/TodayOverview';
import { Weather } from '../components/Weather';
import { WeatherAlerts } from '../components/WeatherAlerts';
import { Nearby } from '../components/Nearby';
import { Events } from '../components/Events';
import { CivicUpdates } from '../components/CivicUpdates';
import { Footer } from '../components/Footer';

// Location, Weather, Alerts, Places, and Events Layers
import { useLocation } from '../hooks/useLocation';
import { useWeather } from '../hooks/useWeather';
import { useAlerts } from '../hooks/useAlerts';
import { usePlaces } from '../hooks/usePlaces';
import { useEvents } from '../hooks/useEvents';
import { useCivicUpdates } from '../hooks/useCivicUpdates';

// Static datasets for location locality display
import { HYDERABAD_LOCALITIES } from '../data';


/**
 * HomePage Component
 * Orchestrates the modular sections of TodayNearMe.
 * Weather and Alerts layers consume live, normalized data from our FastAPI backend,
 * driven automatically by the Location Layer.
 */
export function HomePage() {
  const [selectedLocality, setSelectedLocality] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Consume central Location Layer
  const { location } = useLocation();

  // Consume live Weather Layer (driven by current location or Hyderabad fallback)
  const {
    weather,
    isLoading: isWeatherLoading,
    isRefreshing: isWeatherRefreshing,
    error: weatherError,
    refreshWeather,
  } = useWeather(location);

  // Consume live Weather Alerts Layer (driven by current location or Hyderabad fallback)
  const {
    alertsData,
    isLoading: isAlertsLoading,
    isRefreshing: isAlertsRefreshing,
    error: alertsError,
    refreshAlerts,
  } = useAlerts(location);

  // Consume live Nearby Places Layer (driven by current location or Hyderabad fallback)
  const {
    places: nearbyPlaces,
    placesData,
    selectedCategory,
    selectCategory,
    isLoading: isPlacesLoading,
    error: placesError,
    refreshPlaces,
  } = usePlaces(location);

  // Consume live Events Layer (strictly Hyderabad public events from /api/events)
  const {
    events,
    eventsData: liveEventsData,
    isLoading: isEventsLoading,
    isRefreshing: isEventsRefreshing,
    error: eventsError,
    refreshEvents,
  } = useEvents('Hyderabad');

  // Consume live Civic Updates Layer (/api/civic-updates — Hyderabad official sources)
  const {
    updates: civicUpdates,
    civicData: liveCivicData,
    isLoading: isCivicLoading,
    isRefreshing: isCivicRefreshing,
    error: civicError,
    refreshCivicUpdates,
  } = useCivicUpdates('Hyderabad');

  // Find human-readable name of currently selected locality
  const currentLocalityObj = HYDERABAD_LOCALITIES.find((l) => l.id === selectedLocality);
  const selectedLocalityName = currentLocalityObj ? currentLocalityObj.name : 'All Hyderabad';

  // Smooth scroll handler for quick jump links
  const handleNavigateSection = (sectionId) => {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <div className="app-shell">
      {/* 1. Header with Location Layer */}
      <Header
        selectedLocality={selectedLocality}
        onSelectLocality={setSelectedLocality}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />

      {/* Main Content Sections */}
      <main id="main-content" className="main-content container" tabIndex="-1">
        {/* 2. Today Overview */}
        <TodayOverview
          weather={weather}
          alertsState={{
            hasAlert: alertsData?.has_active_alerts ?? false,
          }}
          civicCount={liveCivicData?.count ?? 0}
          selectedLocalityName={selectedLocalityName}
          onNavigateSection={handleNavigateSection}
        />

        {/* 4. Alerts (Live official warnings from /api/alerts) */}
        <WeatherAlerts
          alertsData={alertsData}
          isLoading={isAlertsLoading}
          isRefreshing={isAlertsRefreshing}
          error={alertsError}
          onRefresh={refreshAlerts}
        />

        {/* 3. Weather (Live data from FastAPI backend) */}
        <Weather
          weather={weather}
          isLoading={isWeatherLoading}
          isRefreshing={isWeatherRefreshing}
          error={weatherError}
          onRefresh={refreshWeather}
        />

        {/* 5. Nearby Places (Live data from /api/places & OpenStreetMap) */}
        <Nearby
          places={nearbyPlaces}
          placesData={placesData}
          selectedCategory={selectedCategory}
          onSelectCategory={selectCategory}
          isLoading={isPlacesLoading}
          error={placesError}
          onRefresh={refreshPlaces}
        />


        {/* Two-column layout for Events and Civic updates */}
        <div className="dual-section-grid">
          {/* 6. Events (Live verified public & community events from /api/events) */}
          <Events
            events={events}
            eventsData={liveEventsData}
            isLoading={isEventsLoading}
            isRefreshing={isEventsRefreshing}
            error={eventsError}
            onRefresh={refreshEvents}
          />

          {/* 7. Civic Updates (Live data from /api/civic-updates) */}
          <CivicUpdates
            updates={civicUpdates}
            civicData={liveCivicData}
            isLoading={isCivicLoading}
            isRefreshing={isCivicRefreshing}
            error={civicError}
            onRefresh={refreshCivicUpdates}
          />
        </div>
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}

export default HomePage;
