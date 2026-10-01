from .weather import router as weather_router
from .alerts import router as alerts_router
from .places import router as places_router
from .events import router as events_router

__all__ = ["weather_router", "alerts_router", "places_router", "events_router"]

