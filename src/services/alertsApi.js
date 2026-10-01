/**
 * Alerts API Service
 * Communicates ONLY with our TodayNearMe FastAPI backend (/api/alerts).
 * Never communicates directly with external alert providers.
 */

export async function fetchAlerts({ latitude, longitude } = {}) {
  let url = '/api/alerts';

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
    throw new Error(`Alerts service responded with status ${response.status}`);
  }

  return await response.json();
}
