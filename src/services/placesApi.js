/**
 * Places API Service
 * Communicates ONLY with our TodayNearMe FastAPI backend (/api/places).
 * Never communicates directly with external OpenStreetMap or Overpass services.
 */

export async function fetchPlaces({ latitude, longitude, category = 'hospital' } = {}) {
  const params = new URLSearchParams();

  if (
    latitude !== null &&
    latitude !== undefined &&
    longitude !== null &&
    longitude !== undefined
  ) {
    params.set('latitude', latitude);
    params.set('longitude', longitude);
  }

  if (category) {
    params.set('category', category);
  }

  const queryString = params.toString();
  const url = queryString ? `/api/places?${queryString}` : '/api/places';

  const response = await fetch(url, {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Places service responded with status ${response.status}`);
  }

  return await response.json();
}
