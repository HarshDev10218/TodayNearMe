import { useState, useEffect, useCallback } from 'react';
import { fetchAlerts } from '../services/alertsApi';

/**
 * useAlerts Hook
 * Fetches and manages real-time official weather alert state from our FastAPI backend (/api/alerts).
 * Automatically synchronizes with the Location Layer without determining coordinates itself.
 */
export function useAlerts(location) {
  const [state, setState] = useState({
    alertsData: null,
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

    fetchAlerts(queryCoords)
      .then((data) => {
        if (isMounted) {
          setState({
            alertsData: data,
            isLoading: false,
            error: null,
          });
        }
      })
      .catch(() => {
        if (isMounted) {
          setState((prev) => ({
            alertsData: prev.alertsData,
            isLoading: false,
            error: 'Weather alerts unavailable right now.',
          }));
        }
      });

    return () => {
      isMounted = false;
    };
  }, [location]);

  // Explicit user-triggered refresh
  const refreshAlerts = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const queryCoords =
        location?.mode === 'browser' &&
        location?.latitude !== null &&
        location?.longitude !== null
          ? { latitude: location.latitude, longitude: location.longitude }
          : { latitude: 17.385, longitude: 78.4867 };

      const data = await fetchAlerts(queryCoords);
      setState({
        alertsData: data,
        isLoading: false,
        error: null,
      });
    } catch {
      setState((prev) => ({
        ...prev,
        error: 'Weather alerts unavailable right now.',
      }));
    } finally {
      setIsRefreshing(false);
    }
  }, [location]);

  return {
    alertsData: state.alertsData,
    isLoading: state.isLoading,
    isRefreshing,
    error: state.error,
    refreshAlerts,
  };
}
