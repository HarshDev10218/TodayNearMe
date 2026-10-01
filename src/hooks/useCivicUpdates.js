import { useState, useEffect, useCallback } from 'react';
import { fetchCivicUpdates } from '../services/civicUpdatesApi';

/**
 * useCivicUpdates Hook
 * Fetches and manages live official civic notices and public updates for Hyderabad
 * through the TodayNearMe FastAPI backend /api/civic-updates.
 * Encapsulates loading, error, cache synchronization, and controlled refresh states.
 */
export function useCivicUpdates(city = 'Hyderabad') {
  const [state, setState] = useState({
    civicData: null,
    isLoading: true,
    error: null,
  });
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    let isMounted = true;

    fetchCivicUpdates(city)
      .then((data) => {
        if (isMounted) {
          setState({
            civicData: data,
            isLoading: false,
            error: null,
          });
        }
      })
      .catch(() => {
        if (isMounted) {
          setState((prev) => ({
            civicData: prev.civicData,
            isLoading: false,
            error: 'Civic updates are unavailable right now.',
          }));
        }
      });

    return () => {
      isMounted = false;
    };
  }, [city]);

  const refreshCivicUpdates = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const data = await fetchCivicUpdates(city, { refresh: true });
      setState({
        civicData: data,
        isLoading: false,
        error: null,
      });
    } catch {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: 'Civic updates are unavailable right now.',
      }));
    } finally {
      setIsRefreshing(false);
    }
  }, [city]);

  return {
    updates: state.civicData?.updates || [],
    civicData: state.civicData,
    isLoading: state.isLoading,
    isRefreshing,
    error: state.error,
    refreshCivicUpdates,
  };
}
