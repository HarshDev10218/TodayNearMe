/**
 * Events API Service
 * Communicates ONLY with our TodayNearMe FastAPI backend.
 * Queries /api/events for Hyderabad public and community gatherings.
 * Never directly accesses third-party event platforms or arbitrary external URLs.
 */

export async function fetchEvents(city = 'Hyderabad', options = {}) {
  const params = new URLSearchParams({ city });
  if (options.refresh) {
    params.set('refresh', 'true');
  }

  const url = `/api/events?${params.toString()}`;

  const response = await fetch(url, {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Events service responded with status ${response.status}`);
  }

  return await response.json();
}
