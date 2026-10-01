from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes.weather import router as weather_router
from app.routes.alerts import router as alerts_router
from app.routes.places import router as places_router
from app.routes.events import router as events_router
from app.routes.civic_updates import router as civic_updates_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Backend API service for TodayNearMe — Hyderabad Local Utility",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(weather_router)
app.include_router(alerts_router)
app.include_router(places_router)
app.include_router(events_router)
app.include_router(civic_updates_router)



@app.get(
    "/health",
    tags=["Health"],
    summary="Service Health Check",
    description="Returns the current operational status of the TodayNearMe API.",
)
async def health_check():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
