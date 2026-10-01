/**
 * Weather API Service
 * Communicates ONLY with our TodayNearMe FastAPI backend.
 * Never makes direct requests to external weather providers.
 */

export async function fetchWeather({ latitude, longitude } = {}) {
  let url = '/api/weather';

  if (
    latitude !== null &&
    latitude !== undefined &&
    longitude !== null &&
    longitude !== undefined
  ) {
    url += `?latitude=${encodeURIComponent(latitude)}&longitude=${encodeURIComponent(longitude)}`;
  }

  const response = await fetch(url, {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Weather service responded with status ${response.status}`);
  }

  return await response.json();
}
