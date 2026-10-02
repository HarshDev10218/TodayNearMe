import logging
import math
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.models.place import (
    CATEGORY_LABELS,
    PlaceItem,
    PlaceLocation,
    PlacesResponse,
)

logger = logging.getLogger(__name__)

# Overpass QL clause templates per category
# Using spatial bounding box filtering for high-performance index queries
CATEGORY_QUERY_TEMPLATES: Dict[str, str] = {
    "hospital": 'nwr["amenity"="hospital"]["name"]({bbox});',
    "pharmacy": 'nwr["amenity"="pharmacy"]["name"]({bbox});',
    "police": 'nwr["amenity"="police"]["name"]({bbox});',
    "atm": 'nwr["amenity"="atm"]({bbox});',
    "park": 'nwr["leisure"="park"]["name"]({bbox});',
    "college": 'nwr["amenity"~"college|university"]["name"]({bbox});',
    "government": 'nwr["office"="government"]["name"]({bbox});',
    "transport": 'nwr["railway"~"station|subway_entrance"]["name"]({bbox});',
    "petrol_station": 'nwr["amenity"="fuel"]["name"]({bbox});',
}

# Category search radii in meters (tuned for Hyderabad urban density)
CATEGORY_RADII_METERS: Dict[str, float] = {
    "hospital": 3000.0,
    "pharmacy": 2500.0,
    "police": 3500.0,
    "atm": 2000.0,
    "park": 3000.0,
    "college": 3500.0,
    "government": 3500.0,
    "transport": 3500.0,
    "petrol_station": 3000.0,
}


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """
    Calculate the great-circle distance between two points on the Earth's surface
    using the Haversine formula. Returns distance in rounded integer meters.
    """
    earth_radius_m = 6371000.0  # Mean radius of Earth in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return int(round(earth_radius_m * c))


def format_distance(distance_m: int) -> str:
    """Format distance into human-readable string (e.g. '850 m', '1.4 km')."""
    if distance_m < 1000:
        return f"{distance_m} m"
    return f"{distance_m / 1000.0:.1f} km"


def get_bounding_box(lat: float, lon: float, radius_m: float) -> str:
    """
    Compute an approximate bounding box (south, west, north, east) around coordinates.
    Overpass expects: 'south,west,north,east'
    """
    delta_lat = radius_m / 111320.0
    # Guard against division by near-zero cosine at poles
    cos_lat = max(math.cos(math.radians(lat)), 0.01)
    delta_lon = radius_m / (111320.0 * cos_lat)

    south = round(lat - delta_lat, 5)
    north = round(lat + delta_lat, 5)
    west = round(lon - delta_lon, 5)
    east = round(lon + delta_lon, 5)

    return f"{south},{west},{north},{east}"


def extract_address(tags: dict) -> Optional[str]:
    """Extract and format address from OpenStreetMap tags if present."""
    if not tags:
        return None

    # Check for direct full address
    if "addr:full" in tags:
        return tags["addr:full"].strip()

    parts = []
    if "addr:housenumber" in tags:
        parts.append(tags["addr:housenumber"].strip())
    if "addr:street" in tags:
        parts.append(tags["addr:street"].strip())
    if "addr:suburb" in tags:
        parts.append(tags["addr:suburb"].strip())
    elif "addr:neighbourhood" in tags:
        parts.append(tags["addr:neighbourhood"].strip())
    if "addr:city" in tags and tags["addr:city"].strip().lower() != "hyderabad":
        parts.append(tags["addr:city"].strip())

    if parts:
        return ", ".join(parts)

    return None


class BasePlacesProvider(ABC):
    """Abstract interface for external Places providers."""

    @abstractmethod
    async def fetch_places(
        self, latitude: float, longitude: float, category: str
    ) -> List[PlaceItem]:
        """Fetch and return normalized nearby places for the given category."""
        pass


class OpenStreetMapPlacesProvider(BasePlacesProvider):
    """
    Fetches real geographic POI data from OpenStreetMap via the public Overpass API.
    Uses bounding box range scans for fast execution and minimal upstream server burden.
    """

    OVERPASS_ENDPOINTS = [
        "https://lz4.overpass-api.de/api/interpreter",
        "https://z.overpass-api.de/api/interpreter",
        "https://overpass-api.de/api/interpreter",
    ]

    USER_AGENT = "TodayNearMe/1.0 (Hyderabad Local Utility App; contact@todaynearme.local)"

    async def fetch_places(
        self, latitude: float, longitude: float, category: str
    ) -> List[PlaceItem]:
        query_tmpl = CATEGORY_QUERY_TEMPLATES.get(category)
        if not query_tmpl:
            return []

        radius_m = CATEGORY_RADII_METERS.get(category, 3000.0)
        bbox = get_bounding_box(latitude, longitude, radius_m)
        category_clause = query_tmpl.format(bbox=bbox)

        # Build clean Overpass QL query with server-side limit of 15 to protect bandwidth.
        overpass_query = f"[out:json][timeout:12];\n{category_clause}\nout center tags 15;"

        headers = {
            "User-Agent": self.USER_AGENT,
            "Accept": "application/json",
        }

        last_error: Optional[str] = None
        raw_elements: Optional[List[dict]] = None

        for endpoint in self.OVERPASS_ENDPOINTS:
            try:
                async with httpx.AsyncClient(timeout=12.0) as client:
                    resp = await client.post(
                        endpoint,
                        data={"data": overpass_query},
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_elements = data.get("elements", [])
                        break
                    last_error = f"Upstream endpoint {endpoint} returned status {resp.status_code}"
            except httpx.TimeoutException:
                last_error = f"Timeout connecting to {endpoint}"
            except Exception as exc:  # pragma: no cover - upstream provider failure should be handled gracefully
                last_error = f"Failed connecting to {endpoint}: {exc}"

        if raw_elements is None:
            logger.warning(
                "Overpass provider failed for category=%s lat=%s lon=%s. last_error=%s",
                category,
                latitude,
                longitude,
                last_error,
            )
            return []

        places: List[PlaceItem] = []
        category_label = CATEGORY_LABELS.get(category, category.title())

        for el in raw_elements:
            tags = el.get("tags", {})
            osm_type = el.get("type", "node")
            osm_id = el.get("id")
            unique_id = f"osm-{osm_type}-{osm_id}"

            # Extract latitude and longitude
            place_lat = el.get("lat") or el.get("center", {}).get("lat")
            place_lon = el.get("lon") or el.get("center", {}).get("lon")
            if place_lat is None or place_lon is None:
                continue

            # Extract name
            name = tags.get("name") or tags.get("name:en")
            if not name:
                if category == "atm":
                    operator = tags.get("operator") or tags.get("brand")
                    name = f"{operator} ATM" if operator else "ATM"
                elif category == "petrol_station":
                    brand = tags.get("brand") or tags.get("operator")
                    name = f"{brand} Petrol Station" if brand else "Petrol Station"
                else:
                    continue

            name = name.strip()
            if not name:
                continue

            distance_m = calculate_haversine_distance(
                latitude, longitude, float(place_lat), float(place_lon)
            )
            address = extract_address(tags)

            places.append(
                PlaceItem(
                    id=unique_id,
                    name=name,
                    category=category,
                    category_label=category_label,
                    latitude=float(place_lat),
                    longitude=float(place_lon),
                    distance_m=distance_m,
                    distance_formatted=format_distance(distance_m),
                    address=address,
                    source="OpenStreetMap",
                )
            )

        places.sort(key=lambda p: p.distance_m)
        return places[:10]


class PlacesService:
    """
    Manages Nearby Places requests with in-memory caching and clean coordinate scoping.
    """

    def __init__(self, provider: Optional[BasePlacesProvider] = None):
        self._provider = provider or OpenStreetMapPlacesProvider()
        self._cache: Dict[str, Tuple[float, PlacesResponse]] = {}

    def _get_cache_key(self, latitude: float, longitude: float, category: str) -> str:
        """
        Group nearby coordinates to avoid redundant external queries.
        Rounding to 2 decimals (~1.1 km resolution) provides optimal cache hit rates.
        """
        return f"{round(latitude, 2)}:{round(longitude, 2)}:{category.lower()}"

    def _get_from_cache(self, key: str) -> Optional[PlacesResponse]:
        """Retrieve cached response if within TTL window."""
        if key in self._cache:
            timestamp, cached_res = self._cache[key]
            if time.time() - timestamp < settings.PLACES_CACHE_TTL_SECONDS:
                return cached_res.model_copy(update={"cached": True})
            del self._cache[key]
        return None

    def _save_to_cache(self, key: str, response: PlacesResponse) -> None:
        """Store response in cache with current timestamp."""
        self._cache[key] = (time.time(), response)

    async def get_nearby_places(
        self, latitude: float, longitude: float, category: str
    ) -> PlacesResponse:
        """
        Retrieve nearby places for coordinates and category.
        Checks cache first, then calls provider.
        """
        norm_cat = category.strip().lower()
        cache_key = self._get_cache_key(latitude, longitude, norm_cat)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        places = await self._provider.fetch_places(latitude, longitude, norm_cat)

        is_hyderabad_default = (
            abs(latitude - settings.DEFAULT_HYDERABAD_LAT) < 0.05
            and abs(longitude - settings.DEFAULT_HYDERABAD_LON) < 0.05
        )
        location_label = "Hyderabad (Default)" if is_hyderabad_default else "Current Location"
        category_label = CATEGORY_LABELS.get(norm_cat, norm_cat.title())

        response = PlacesResponse(
            places=places,
            location=PlaceLocation(
                latitude=latitude,
                longitude=longitude,
                label=location_label,
            ),
            category=norm_cat,
            category_label=category_label,
            count=len(places),
            source="© OpenStreetMap contributors",
            attribution_url="https://www.openstreetmap.org/copyright",
            cached=False,
        )

        self._save_to_cache(cache_key, response)
        return response


places_service = PlacesService()
