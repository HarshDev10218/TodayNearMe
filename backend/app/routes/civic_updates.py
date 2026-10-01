from fastapi import APIRouter, Query, HTTPException, status

from app.models.civic_update import CivicUpdatesResponse
from app.services.civic_updates_service import civic_updates_service

router = APIRouter(prefix="/api", tags=["Civic Updates"])


@router.get(
    "/civic-updates",
    response_model=CivicUpdatesResponse,
    summary="Get verified official civic notices and public updates for Hyderabad",
    description=(
        "Returns verified civic notices, municipal advisories, government announcements, and "
        "public updates relevant to Hyderabad. Aggregated strictly from official public sources: "
        "GHMC, Hyderabad District Government (NIC/S3WaaS), and Government of Telangana portal. "
        "₹0 budget — no paid APIs, no AI, no unofficial sources."
    ),
)
async def get_civic_updates(
    city: str = Query(
        default="Hyderabad",
        description="Target city for civic updates (V1 strictly supports Hyderabad)",
    ),
    refresh: bool = Query(
        default=False,
        description="Bypass backend cache and force fresh query of monitored official sources",
    ),
) -> CivicUpdatesResponse:
    norm_city = city.strip()
    if norm_city.lower() != "hyderabad":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="V1 of TodayNearMe strictly serves Hyderabad civic updates. Please specify city=Hyderabad.",
        )

    return await civic_updates_service.get_updates(city="Hyderabad", refresh=refresh)
