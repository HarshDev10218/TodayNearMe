import React, { useState, useCallback, useEffect, createContext, useContext } from 'react';

/**
 * Default location model for TodayNearMe (Hyderabad, Telangana, India)
 */
export const DEFAULT_LOCATION = {
  mode: 'default', // 'default' | 'browser'
  city: 'Hyderabad',
  state: 'Telangana',
  country: 'India',
  latitude: null,
  longitude: null,
  permission: 'unknown', // 'unknown' | 'granted' | 'denied' | 'unavailable'
  accuracy: null,
  error: null,
  isLoading: false
};

const LocationContext = createContext(null);

/**
 * Internal hook logic for managing location state
 */
export function useLocationState() {
  const [location, setLocation] = useState(DEFAULT_LOCATION);

  // Passive permission status detection (does NOT trigger browser prompt)
  useEffect(() => {
    if (typeof navigator !== 'undefined' && navigator.permissions?.query) {
      navigator.permissions
        .query({ name: 'geolocation' })
        .then((permissionStatus) => {
          if (permissionStatus.state === 'denied') {
            setLocation((prev) => ({ ...prev, permission: 'denied' }));
          } else if (permissionStatus.state === 'granted') {
            setLocation((prev) => ({
              ...prev,
              permission: prev.mode === 'browser' ? 'granted' : prev.permission
            }));
          }

          permissionStatus.onchange = () => {
            if (permissionStatus.state === 'denied') {
              setLocation((prev) => ({
                ...prev,
                mode: 'default',
                latitude: null,
                longitude: null,
                permission: 'denied'
              }));
            }
          };
        })
        .catch(() => {
          // Permissions API query optional/unsupported; safe fallback
        });
    }
  }, []);

  /**
   * Request browser coordinates via standard Geolocation API.
   * Only called on explicit user action.
   */
  const requestLocation = useCallback(() => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      setLocation((prev) => ({
        ...prev,
        mode: 'default',
        latitude: null,
        longitude: null,
        permission: 'unavailable',
        error: 'Geolocation is not supported by this browser. Using Hyderabad as default.',
        isLoading: false
      }));
      return;
    }

    setLocation((prev) => ({
      ...prev,
      isLoading: true,
      error: null
    }));

    const options = {
      enableHighAccuracy: false,
      timeout: 10000,
      maximumAge: 300000 // 5 minutes cached location is acceptable
    };

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude, accuracy } = position.coords;
        setLocation({
          mode: 'browser',
          city: 'Hyderabad',
          state: 'Telangana',
          country: 'India',
          latitude: Number(latitude.toFixed(5)),
          longitude: Number(longitude.toFixed(5)),
          accuracy: accuracy ? Math.round(accuracy) : null,
          permission: 'granted',
          error: null,
          isLoading: false
        });
      },
      (err) => {
        let permissionStatus = 'unavailable';
        let friendlyMessage = 'Unable to obtain current location. Using Hyderabad as default.';

        if (err.code === 1) {
          // PERMISSION_DENIED
          permissionStatus = 'denied';
          friendlyMessage = 'Location permission was denied. Using Hyderabad as default.';
        } else if (err.code === 2) {
          // POSITION_UNAVAILABLE
          permissionStatus = 'unavailable';
          friendlyMessage = 'Location signal is unavailable. Using Hyderabad as default.';
        } else if (err.code === 3) {
          // TIMEOUT
          permissionStatus = 'unavailable';
          friendlyMessage = 'Location request timed out. Using Hyderabad as default.';
        }

        setLocation((prev) => ({
          ...prev,
          mode: 'default',
          latitude: null,
          longitude: null,
          permission: permissionStatus,
          error: friendlyMessage,
          isLoading: false
        }));
      },
      options
    );
  }, []);

  /**
   * Reset back to default Hyderabad location
   */
  const resetToDefault = useCallback(() => {
    setLocation({
      ...DEFAULT_LOCATION,
      error: null,
      isLoading: false
    });
  }, []);

  /**
   * Dismiss temporary notice / error message
   */
  const dismissError = useCallback(() => {
    setLocation((prev) => ({
      ...prev,
      error: null
    }));
  }, []);

  return {
    location,
    requestLocation,
    resetToDefault,
    dismissError
  };
}

/**
 * LocationProvider component to wrap app or page
 * Uses React.createElement to keep useLocation.js purely standard JavaScript
 */
export function LocationProvider({ children }) {
  const value = useLocationState();
  return React.createElement(LocationContext.Provider, { value }, children);
}

/**
 * Hook to consume location state & actions anywhere in the component tree
 */
export function useLocation() {
  const context = useContext(LocationContext);
  if (!context) {
    throw new Error('useLocation must be used within a LocationProvider');
  }
  return context;
}
