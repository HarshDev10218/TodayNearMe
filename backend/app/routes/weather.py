from typing import Optional
from fastapi import APIRouter, Query, HTTPException, status

from app.core.config import settings
from app.models.weather import WeatherResponse
from app.services.weather_service import weather_service

router = APIRouter(prefix="/api", tags=["Weather"])


@router.get(
    "/weather",
    response_model=WeatherResponse,
    summary="Get current weather and short-range forecast",
    description=(
        "Returns normalized weather conditions, atmospheric parameters, hourly outlook, "
        "and 3-day forecast for the given coordinates. Defaults to Hyderabad if unspecified."
    ),
)
async def get_weather(
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
) -> WeatherResponse:
    # Handle partial coordinate input
    if (latitude is None and longitude is not None) or (latitude is not None and longitude is None):
        raise HTTPException(
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            detail="Both latitude and longitude must be provided together.",
        )

    # Use Hyderabad default coordinates if none provided
    target_lat = latitude if latitude is not None else settings.DEFAULT_HYDERABAD_LAT
    target_lon = longitude if longitude is not None else settings.DEFAULT_HYDERABAD_LON

    return await weather_service.get_weather(target_lat, target_lon)
