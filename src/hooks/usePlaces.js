import { useState, useEffect, useCallback, useRef } from 'react';
import { fetchPlaces } from '../services/placesApi';

/**
 * Supported categories configuration for UI controls and category mapping
 */
export const SUPPORTED_PLACE_CATEGORIES = [
  { id: 'hospital', label: 'Hospitals' },
  { id: 'pharmacy', label: 'Pharmacies' },
  { id: 'police', label: 'Police Stations' },
  { id: 'atm', label: 'ATMs' },
  { id: 'park', label: 'Parks' },
  { id: 'college', label: 'Colleges' },
  { id: 'government', label: 'Government' },
  { id: 'transport', label: 'Transit' },
  { id: 'petrol_station', label: 'Petrol Stations' },
];

/**
 * usePlaces Hook
 * Manages fetching, caching synchronization, and category switching
 * for Nearby Places using the TodayNearMe FastAPI backend.
 * Consumes the central Location Layer without duplicate geolocation logic.
 */
export function usePlaces(location) {
  const [selectedCategory, setSelectedCategory] = useState('hospital');
  const [state, setState] = useState({
    placesData: null,
    isLoading: true,
    error: null,
  });
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Keep track of active request parameters to prevent race conditions
  const activeRequestRef = useRef('');

  const getCoordinates = useCallback(() => {
    if (
      location?.mode === 'browser' &&
      location?.latitude !== null &&
      location?.longitude !== null
    ) {
      return { latitude: location.latitude, longitude: location.longitude };
    }
    return { latitude: 17.385, longitude: 78.4867 };
  }, [location]);

  // Fetch places whenever location or selected category changes
  useEffect(() => {
    let isMounted = true;
    const coords = getCoordinates();
    const requestId = `${coords.latitude}:${coords.longitude}:${selectedCategory}`;
    activeRequestRef.current = requestId;

    fetchPlaces({
      latitude: coords.latitude,
      longitude: coords.longitude,
      category: selectedCategory,
    })
      .then((data) => {
        if (isMounted && activeRequestRef.current === requestId) {
          setState({
            placesData: data,
            isLoading: false,
            error: null,
          });
        }
      })
      .catch(() => {
        if (isMounted && activeRequestRef.current === requestId) {
          setState((prev) => ({
            placesData: prev.placesData,
            isLoading: false,
            error: 'Nearby places are unavailable right now.',
          }));
        }
      });

    return () => {
      isMounted = false;
    };
  }, [getCoordinates, selectedCategory]);

  // Handle explicit category switching
  const selectCategory = useCallback((categoryId) => {
    setSelectedCategory((prev) => {
      if (prev === categoryId) return prev;
      return categoryId;
    });
    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
    }));
  }, []);

  // Explicit retry / refresh handler
  const refreshPlaces = useCallback(async () => {
    setIsRefreshing(true);
    const coords = getCoordinates();
    try {
      const data = await fetchPlaces({
        latitude: coords.latitude,
        longitude: coords.longitude,
        category: selectedCategory,
      });
      setState({
        placesData: data,
        isLoading: false,
        error: null,
      });
    } catch {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: 'Nearby places are unavailable right now.',
      }));
    } finally {
      setIsRefreshing(false);
    }
  }, [getCoordinates, selectedCategory]);

  return {
    places: state.placesData?.places || [],
    placesData: state.placesData,
    selectedCategory,
    selectCategory,
    isLoading: state.isLoading,
    isRefreshing,
    error: state.error,
    refreshPlaces,
  };
}
