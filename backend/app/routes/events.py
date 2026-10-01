from fastapi import APIRouter, Query, HTTPException, status

from app.models.event import EventResponse
from app.services.events_service import events_service

router = APIRouter(prefix="/api", tags=["Events"])


@router.get(
    "/events",
    response_model=EventResponse,
    summary="Get upcoming public events in Hyderabad",
    description=(
        "Returns verified upcoming public and community events (technology, workshops, "
        "cultural gatherings, official notices) happening in Hyderabad. Aggregated from "
        "monitored public sources: FOSS United, Telangana Tourism, and Hyderabad District Government."
    ),
)
async def get_events(
    city: str = Query(
        default="Hyderabad",
        description="Target city for public events (V1 strictly supports Hyderabad)",
    ),
    refresh: bool = Query(
        default=False,
        description="Bypass backend cache and force fresh query of monitored public sources",
    ),
) -> EventResponse:
    norm_city = city.strip()
    if norm_city.lower() != "hyderabad":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="V1 of TodayNearMe strictly serves Hyderabad events. Please specify city=Hyderabad.",
        )

    return await events_service.get_events(city="Hyderabad", refresh=refresh)
