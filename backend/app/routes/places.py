from typing import Optional
from fastapi import APIRouter, Query, HTTPException, status

from app.core.config import settings
from app.models.place import CATEGORY_LABELS, PlacesResponse
from app.services.places_service import places_service

router = APIRouter(prefix="/api", tags=["Nearby Places"])

ALLOWED_CATEGORIES = list(CATEGORY_LABELS.keys())


@router.get(
    "/places",
    response_model=PlacesResponse,
    summary="Get nearby public amenities and essential places",
    description=(
        "Returns nearby essential public places (hospitals, pharmacies, police stations, "
        "ATMs, parks, transit, etc.) sourced from OpenStreetMap and sorted by distance. "
        "Coordinates default to Hyderabad if omitted."
    ),
)
async def get_nearby_places(
    latitude: Optional[float] = Query(
        default=None,
        ge=-90.0,
        le=90.0,
        description="Latitude in decimal degrees (-90.0 to 90.0)",
    ),
    longitude: Optional[float] = Query(
        default=None,
        ge=-180.0,
        le=180.0,
        description="Longitude in decimal degrees (-180.0 to 180.0)",
    ),
    category: str = Query(
        default="hospital",
        description=f"Controlled category type. Allowed: {', '.join(ALLOWED_CATEGORIES)}",
    ),
) -> PlacesResponse:
    # Validate coordinate pairing
    if (latitude is None and longitude is not None) or (latitude is not None and longitude is None):
        raise HTTPException(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            detail="Both latitude and longitude must be provided together.",
        )

    # Validate category against controlled whitelist
    norm_category = category.strip().lower()
    if norm_category not in ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid category '{category}'. "
                f"Allowed categories are: {', '.join(ALLOWED_CATEGORIES)}"
            ),
        )

    # Use Hyderabad default coordinates if none provided
    target_lat = latitude if latitude is not None else settings.DEFAULT_HYDERABAD_LAT
    target_lon = longitude if longitude is not None else settings.DEFAULT_HYDERABAD_LON

    return await places_service.get_nearby_places(target_lat, target_lon, norm_category)
