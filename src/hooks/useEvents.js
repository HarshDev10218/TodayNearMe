import { useState, useEffect, useCallback } from 'react';
import { fetchEvents } from '../services/eventsApi';

/**
 * useEvents Hook
 * Fetches and manages real public events in Hyderabad through our FastAPI backend.
 * Encapsulates loading, error, caching synchronization, and controlled refresh states.
 */
export function useEvents(city = 'Hyderabad') {
  const [state, setState] = useState({
    eventsData: null,
    isLoading: true,
    error: null,
  });
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    let isMounted = true;

    fetchEvents(city)
      .then((data) => {
        if (isMounted) {
          setState({
            eventsData: data,
            isLoading: false,
            error: null,
          });
        }
      })
      .catch(() => {
        if (isMounted) {
          setState((prev) => ({
            eventsData: prev.eventsData,
            isLoading: false,
            error: 'Events are unavailable right now.',
          }));
        }
      });

    return () => {
      isMounted = false;
    };
  }, [city]);

  const refreshEvents = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const data = await fetchEvents(city, { refresh: true });
      setState({
        eventsData: data,
        isLoading: false,
        error: null,
      });
    } catch {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: 'Events are unavailable right now.',
      }));
    } finally {
      setIsRefreshing(false);
    }
  }, [city]);

  return {
    events: state.eventsData?.events || [],
    eventsData: state.eventsData,
    isLoading: state.isLoading,
    isRefreshing,
    error: state.error,
    refreshEvents,
  };
}
