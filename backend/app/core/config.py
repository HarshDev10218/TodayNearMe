import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "TodayNearMe API"
    ENVIRONMENT: str = "development"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # CORS configuration for development
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Weather service settings
    WEATHER_PROVIDER: str = "open-meteo"
    WEATHER_API_BASE_URL: str = "https://api.open-meteo.com/v1"
    WEATHER_CACHE_TTL_SECONDS: int = 600  # 10 minutes cache

    # Hyderabad fallback coordinates
    DEFAULT_HYDERABAD_LAT: float = 17.3850
    DEFAULT_HYDERABAD_LON: float = 78.4867

    # Optional key for providers that require one
    WEATHER_API_KEY: str = ""

    # Alert service settings
    ALERT_PROVIDER: str = "official_imd"
    ALERT_CACHE_TTL_SECONDS: int = 600  # 10 minutes cache
    WEATHER_ALERT_API_KEY: str = ""
    WEATHER_ALERT_API_URL: str = "https://api.weatherapi.com/v1"

    # Places service settings
    PLACES_PROVIDER: str = "openstreetmap"
    PLACES_CACHE_TTL_SECONDS: int = 900  # 15 minutes cache
    PLACES_SEARCH_RADIUS_KM: float = 4.0  # ~4 km urban radius

    # Events service settings
    EVENTS_PROVIDER: str = "fossunited"
    EVENTS_CACHE_TTL_SECONDS: int = 1800  # 30 minutes cache
    TIMEZONE: str = "Asia/Kolkata"

    # Civic updates service settings
    CIVIC_UPDATES_CACHE_TTL_SECONDS: int = 1800  # 30 minutes cache

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
