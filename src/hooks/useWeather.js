import { useState, useEffect, useCallback } from 'react';
import { fetchWeather } from '../services/weatherApi';

/**
 * useWeather Hook
 * Fetches and manages real weather state through our FastAPI backend.
 * Automatically synchronizes with the Location Layer without determining coordinates itself.
 */
export function useWeather(location) {
  const [state, setState] = useState({
    weather: null,
    isLoading: true,
    error: null,
  });
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Synchronize with location updates
  useEffect(() => {
    let isMounted = true;

    const queryCoords =
      location?.mode === 'browser' &&
      location?.latitude !== null &&
      location?.longitude !== null
        ? { latitude: location.latitude, longitude: location.longitude }
        : { latitude: 17.385, longitude: 78.4867 };

    fetchWeather(queryCoords)
      .then((data) => {
        if (isMounted) {
          setState({
            weather: data,
            isLoading: false,
            error: null,
          });
        }
      })
      .catch(() => {
        if (isMounted) {
          setState((prev) => ({
            weather: prev.weather,
            isLoading: false,
            error: 'Weather unavailable right now.',
          }));
        }
      });

    return () => {
      isMounted = false;
    };
  }, [location]);

  // Explicit user-triggered refresh
  const refreshWeather = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const queryCoords =
        location?.mode === 'browser' &&
        location?.latitude !== null &&
        location?.longitude !== null
          ? { latitude: location.latitude, longitude: location.longitude }
          : { latitude: 17.385, longitude: 78.4867 };

      const data = await fetchWeather(queryCoords);
      setState({
        weather: data,
        isLoading: false,
        error: null,
      });
    } catch {
      setState((prev) => ({
        ...prev,
        error: 'Weather unavailable right now.',
      }));
    } finally {
      setIsRefreshing(false);
    }
  }, [location]);

  return {
    weather: state.weather,
    isLoading: state.isLoading,
    isRefreshing,
    error: state.error,
    refreshWeather,
  };
}
