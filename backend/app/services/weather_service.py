import time
from datetime import datetime
from typing import Dict, Tuple, Optional
import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.models.weather import (
    LocationCoordinates,
    CurrentWeather,
    HourlyForecastItem,
    DailyForecastItem,
    WeatherResponse,
)

# WMO Weather interpretation codes (WMO code -> (Description, Normalized Code))
WMO_CODE_MAP: Dict[int, Tuple[str, str]] = {
    0: ("Clear Sky", "clear"),
    1: ("Mainly Clear", "mainly-clear"),
    2: ("Partly Cloudy", "partly-cloudy"),
    3: ("Overcast", "overcast"),
    45: ("Foggy", "fog"),
    48: ("Depositing Rime Fog", "fog"),
    51: ("Light Drizzle", "drizzle"),
    53: ("Moderate Drizzle", "drizzle"),
    55: ("Dense Drizzle", "drizzle"),
    56: ("Light Freezing Drizzle", "drizzle"),
    57: ("Dense Freezing Drizzle", "drizzle"),
    61: ("Slight Rain", "rain"),
    63: ("Moderate Rain", "rain"),
    65: ("Heavy Rain", "heavy-rain"),
    66: ("Light Freezing Rain", "rain"),
    67: ("Heavy Freezing Rain", "heavy-rain"),
    71: ("Slight Snow", "snow"),
    73: ("Moderate Snow", "snow"),
    75: ("Heavy Snow", "snow"),
    77: ("Snow Grains", "snow"),
    80: ("Slight Rain Showers", "rain-showers"),
    81: ("Moderate Rain Showers", "rain-showers"),
    82: ("Violent Rain Showers", "heavy-rain"),
    85: ("Slight Snow Showers", "snow"),
    86: ("Heavy Snow Showers", "snow"),
    95: ("Thunderstorm", "thunderstorm"),
    96: ("Thunderstorm with Slight Hail", "thunderstorm"),
    99: ("Thunderstorm with Heavy Hail", "thunderstorm"),
}


def get_weather_condition(code: int) -> Tuple[str, str]:
    """Return human-readable condition and icon code for a WMO weather code."""
    return WMO_CODE_MAP.get(code, ("Fair", "partly-cloudy"))


def degrees_to_compass(degrees: float) -> str:
    """Convert degrees (0-360) to 16-point compass direction."""
    val = int((degrees / 22.5) + 0.5)
    directions = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
    ]
    return directions[val % 16]


class WeatherService:
    """
    Handles fetching, caching, and normalizing weather data from Open-Meteo.
    Keeps provider-specific implementation isolated from routes and frontend.
    """

    def __init__(self):
        # In-memory cache mapping key -> (timestamp, WeatherResponse)
        self._cache: Dict[str, Tuple[float, WeatherResponse]] = {}

    def _get_cache_key(self, latitude: float, longitude: float) -> str:
        """
        Group nearby coordinates to avoid redundant external queries.
        Rounding to 2 decimals (~1.1 km resolution) provides optimal caching.
        """
        return f"{round(latitude, 2)}:{round(longitude, 2)}"

    def _get_from_cache(self, key: str) -> Optional[WeatherResponse]:
        """Retrieve cached response if within TTL window."""
        if key in self._cache:
            timestamp, cached_response = self._cache[key]
            if time.time() - timestamp < settings.WEATHER_CACHE_TTL_SECONDS:
                # Return a copy with cached flag marked True
                return cached_response.model_copy(update={"cached": True})
            else:
                del self._cache[key]
        return None

    def _save_to_cache(self, key: str, response: WeatherResponse) -> None:
        """Store response in cache with current timestamp."""
        self._cache[key] = (time.time(), response)

    async def get_weather(self, latitude: float, longitude: float) -> WeatherResponse:
        """
        Fetch weather for coordinates. Checks cache first, then calls Open-Meteo API.
        """
        cache_key = self._get_cache_key(latitude, longitude)
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        url = f"{settings.WEATHER_API_BASE_URL}/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m,surface_pressure",
            "hourly": "temperature_2m,precipitation_probability,weather_code",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "Asia/Kolkata",
            "wind_speed_unit": "kmh",
            "forecast_days": 3,
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(url, params=params)
                res.raise_for_status()
                data = res.json()
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Weather service request timed out. Please try again shortly."
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=502,
                detail="Upstream weather provider returned an error."
            )
        except Exception:
            raise HTTPException(
                status_code=503,
                detail="Weather service is temporarily unavailable."
            )

        # Parse and normalize raw provider data
        normalized = self._normalize_open_meteo_response(latitude, longitude, data)
        self._save_to_cache(cache_key, normalized)
        return normalized

    def _normalize_open_meteo_response(
        self, latitude: float, longitude: float, raw: dict
    ) -> WeatherResponse:
        """Map Open-Meteo structure into our internal WeatherResponse model."""
        current = raw.get("current", {})
        daily = raw.get("daily", {})
        hourly = raw.get("hourly", {})

        weather_code = current.get("weather_code", 0)
        condition, condition_code = get_weather_condition(weather_code)

        # High/low from daily forecast for today
        daily_max_temps = daily.get("temperature_2m_max", [current.get("temperature_2m", 0.0)])
        daily_min_temps = daily.get("temperature_2m_min", [current.get("temperature_2m", 0.0)])
        daily_rain_probs = daily.get("precipitation_probability_max", [0])

        temp_high = daily_max_temps[0] if daily_max_temps else current.get("temperature_2m", 0.0)
        temp_low = daily_min_temps[0] if daily_min_temps else current.get("temperature_2m", 0.0)
        current_rain_prob = daily_rain_probs[0] if daily_rain_probs else 0

        # Compass direction
        wind_deg = current.get("wind_direction_10m", 0)
        wind_dir = degrees_to_compass(wind_deg)

        # Location label
        is_hyderabad_default = (
            abs(latitude - settings.DEFAULT_HYDERABAD_LAT) < 0.05
            and abs(longitude - settings.DEFAULT_HYDERABAD_LON) < 0.05
        )
        location_label = "Hyderabad (Default)" if is_hyderabad_default else "Current Location"

        # Normalized Current Weather
        current_weather = CurrentWeather(
            temperature=round(float(current.get("temperature_2m", 0.0)), 1),
            feels_like=round(float(current.get("apparent_temperature", 0.0)), 1),
            condition=condition,
            condition_code=condition_code,
            humidity=int(current.get("relative_humidity_2m", 0)),
            wind_speed=round(float(current.get("wind_speed_10m", 0.0)), 1),
            wind_direction=wind_dir,
            precipitation_probability=int(current_rain_prob),
            surface_pressure=round(float(current.get("surface_pressure", 1013.0)), 1),
            temp_high=round(float(temp_high), 1),
            temp_low=round(float(temp_low), 1),
        )

        # Normalized Hourly forecast (next 8 hours from current timestamp)
        hourly_times = hourly.get("time", [])
        hourly_temps = hourly.get("temperature_2m", [])
        hourly_rains = hourly.get("precipitation_probability", [])
        hourly_codes = hourly.get("weather_code", [])

        hourly_items = []
        current_time_str = current.get("time", "")

        # Find starting index around current time
        start_idx = 0
        if current_time_str and current_time_str in hourly_times:
            start_idx = hourly_times.index(current_time_str)

        # Extract 8 hourly intervals
        for i in range(start_idx, min(start_idx + 8, len(hourly_times))):
            t_str = hourly_times[i]
            try:
                dt = datetime.fromisoformat(t_str)
                # Formatted hour like '10 PM' or '9 AM'
                formatted_hour = dt.strftime("%I %p").lstrip("0")
            except Exception:
                formatted_hour = t_str[-5:]

            h_code = hourly_codes[i] if i < len(hourly_codes) else 0
            h_cond, _ = get_weather_condition(h_code)
            h_temp = hourly_temps[i] if i < len(hourly_temps) else 0.0
            h_rain = hourly_rains[i] if i < len(hourly_rains) else 0

            hourly_items.append(
                HourlyForecastItem(
                    time=formatted_hour,
                    temperature=round(float(h_temp), 1),
                    condition=h_cond,
                    precipitation_probability=int(h_rain),
                )
            )

        # Normalized 3-Day Forecast
        daily_times = daily.get("time", [])
        daily_codes = daily.get("weather_code", [])
        daily_items = []

        day_labels = ["Today", "Tomorrow", "Day After"]
        for idx in range(min(3, len(daily_times))):
            d_time = daily_times[idx]
            try:
                dt = datetime.fromisoformat(d_time)
                date_formatted = dt.strftime("%a, %b %d")
                if idx < len(day_labels):
                    day_label = day_labels[idx]
                else:
                    day_label = dt.strftime("%A")
            except Exception:
                date_formatted = d_time
                day_label = day_labels[idx] if idx < len(day_labels) else "Upcoming"

            d_code = daily_codes[idx] if idx < len(daily_codes) else 0
            d_cond, _ = get_weather_condition(d_code)
            max_t = daily_max_temps[idx] if idx < len(daily_max_temps) else temp_high
            min_t = daily_min_temps[idx] if idx < len(daily_min_temps) else temp_low
            rain_p = daily_rain_probs[idx] if idx < len(daily_rain_probs) else 0

            daily_items.append(
                DailyForecastItem(
                    day=day_label,
                    date=date_formatted,
                    condition=d_cond,
                    temp_max=round(float(max_t), 1),
                    temp_min=round(float(min_t), 1),
                    rain_probability=int(rain_p),
                )
            )

        return WeatherResponse(
            location=LocationCoordinates(
                latitude=latitude,
                longitude=longitude,
                label=location_label,
            ),
            current=current_weather,
            hourly=hourly_items,
            forecast=daily_items,
            observed_at=current.get("time", datetime.now().isoformat()),
            source="Open-Meteo (Public Meteorological Service)",
            cached=False,
        )


weather_service = WeatherService()
