from typing import List, Optional
from pydantic import BaseModel, Field


class LocationCoordinates(BaseModel):
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    label: str = Field(default="Hyderabad (Default)", description="Location description")


class CurrentWeather(BaseModel):
    temperature: float = Field(..., description="Current temperature in Celsius")
    feels_like: float = Field(..., description="Apparent temperature in Celsius")
    condition: str = Field(..., description="Human-readable weather condition")
    condition_code: str = Field(default="clear", description="Normalized icon/code identifier")
    humidity: int = Field(..., ge=0, le=100, description="Relative humidity percentage")
    wind_speed: float = Field(..., ge=0, description="Wind speed in km/h")
    wind_direction: str = Field(default="WNW", description="Compass wind direction (e.g. SW, WNW)")
    precipitation_probability: int = Field(..., ge=0, le=100, description="Chance of precipitation percentage")
    surface_pressure: float = Field(..., description="Atmospheric surface pressure in hPa")
    temp_high: float = Field(..., description="Today's forecasted maximum temperature in Celsius")
    temp_low: float = Field(..., description="Today's forecasted minimum temperature in Celsius")


class HourlyForecastItem(BaseModel):
    time: str = Field(..., description="Formatted hour (e.g. '10 PM')")
    temperature: float = Field(..., description="Temperature in Celsius")
    condition: str = Field(..., description="Weather condition for this hour")
    precipitation_probability: int = Field(..., ge=0, le=100, description="Rain probability percentage")


class DailyForecastItem(BaseModel):
    day: str = Field(..., description="Day label (e.g. 'Today', 'Tomorrow', 'Saturday')")
    date: str = Field(..., description="Formatted short date (e.g. 'Thu, Oct 1')")
    condition: str = Field(..., description="Forecast condition")
    temp_max: float = Field(..., description="Max temperature in Celsius")
    temp_min: float = Field(..., description="Min temperature in Celsius")
    rain_probability: int = Field(..., ge=0, le=100, description="Max rain probability percentage")


class WeatherResponse(BaseModel):
    location: LocationCoordinates
    current: CurrentWeather
    hourly: List[HourlyForecastItem]
    forecast: List[DailyForecastItem]
    observed_at: str = Field(..., description="ISO 8601 or formatted observation timestamp")
    source: str = Field(default="Open-Meteo", description="Source provider identifier")
    cached: bool = Field(default=False, description="Whether this response was served from cache")
