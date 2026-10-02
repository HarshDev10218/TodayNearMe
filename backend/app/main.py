import os
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.routes.weather import router as weather_router
from app.routes.alerts import router as alerts_router
from app.routes.places import router as places_router
from app.routes.events import router as events_router
from app.routes.civic_updates import router as civic_updates_router

# Set up logging
logger = logging.getLogger(__name__)

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


# ============================================================================
# Static file serving for React SPA (production)
# ============================================================================

# Resolve dist directory: when running from 'cd backend', go up one level
DIST_DIR = Path(__file__).parent.parent.parent / "dist"

# Startup diagnostics
if os.environ.get("ENVIRONMENT") == "production" or os.environ.get("PORT"):
    logger.info(f"[STARTUP] DIST_DIR resolved to: {DIST_DIR.absolute()}")
    if DIST_DIR.exists():
        index_html = DIST_DIR / "index.html"
        logger.info(f"[STARTUP] index.html exists: {index_html.exists()}")
    else:
        logger.warning(f"[STARTUP] DIST_DIR does not exist: {DIST_DIR.absolute()}")


# Mount static assets from dist/assets with cache headers
if (DIST_DIR / "assets").exists():
    app.mount(
        "/assets",
        StaticFiles(directory=DIST_DIR / "assets"),
        name="assets"
    )
    logger.info("[STARTUP] Mounted /assets from dist/assets")
else:
    logger.warning(f"[STARTUP] dist/assets directory not found at {DIST_DIR / 'assets'}")


# Serve index.html for root path
@app.get("/")
async def serve_root():
    index_html = DIST_DIR / "index.html"
    if index_html.exists():
        return FileResponse(index_html, media_type="text/html")
    else:
        logger.error(f"[STARTUP] index.html not found at {index_html}")
        return {"error": "Frontend not built. Run 'npm run build' in repo root."}, 404


# SPA fallback: serve index.html for all unmatched routes (except /api/* and /docs/*)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Allow API and documentation routes to pass through to their handlers
    if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi.json"):
        return {"error": "Not found"}, 404
    
    # Serve index.html for all other routes (SPA client-side routing)
    index_html = DIST_DIR / "index.html"
    if index_html.exists():
        return FileResponse(index_html, media_type="text/html")
    else:
        return {"error": "Frontend not found"}, 404


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
