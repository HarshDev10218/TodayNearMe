/**
 * Civic Updates API Service
 * Communicates ONLY with the TodayNearMe FastAPI backend /api/civic-updates.
 * Never directly accesses official government websites.
 * ₹0 budget — no paid APIs.
 */

export async function fetchCivicUpdates(city = 'Hyderabad', options = {}) {
  const params = new URLSearchParams({ city });
  if (options.refresh) {
    params.set('refresh', 'true');
  }

  const url = `/api/civic-updates?${params.toString()}`;

  const response = await fetch(url, {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Civic updates service responded with status ${response.status}`);
  }

  return await response.json();
}
