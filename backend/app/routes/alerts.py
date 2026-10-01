from typing import Optional
from fastapi import APIRouter, Query, HTTPException, status

from app.core.config import settings
from app.models.alert import AlertResponse
from app.services.alert_service import alert_service

router = APIRouter(prefix="/api", tags=["Weather Alerts"])


@router.get(
    "/alerts",
    response_model=AlertResponse,
    summary="Get official weather alerts for location",
    description=(
        "Returns active meteorological warnings and safety advisories for the given coordinates "
        "originating from official government meteorological authorities (IMD). "
        "Defaults to Hyderabad fallback if coordinates are omitted."
    ),
)
async def get_alerts(
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
) -> AlertResponse:
    # Validate paired coordinate input
    if (latitude is None and longitude is not None) or (latitude is not None and longitude is None):
        raise HTTPException(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            detail="Both latitude and longitude must be provided together.",
        )

    # Use Hyderabad default coordinates if none provided
    target_lat = latitude if latitude is not None else settings.DEFAULT_HYDERABAD_LAT
    target_lon = longitude if longitude is not None else settings.DEFAULT_HYDERABAD_LON

    return await alert_service.get_alerts(target_lat, target_lon)
