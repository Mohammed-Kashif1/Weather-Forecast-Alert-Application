"""Weather retrieval from OpenWeatherMap or local simulation data."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from .config import (
    API_BASE_URL, OPENWEATHER_API_KEY, REQUEST_TIMEOUT, DATA_DIR
)

class WeatherError(RuntimeError):
    """Raised when weather data cannot be retrieved or normalized."""

SAMPLE_PATH = DATA_DIR / "sample_weather.json"

def _sample_payload():
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    forecast = []
    temps = [27, 28, 30, 32, 34, 33, 31, 29]
    for i, temp in enumerate(temps):
        dt = now + timedelta(hours=3 * i)
        forecast.append({
            "dt": int(dt.timestamp()),
            "main": {"temp": temp, "humidity": min(98, 58 + i * 5)},
            "weather": [{"description": "light rain" if i in (3, 4) else "partly cloudy"}],
            "wind": {"speed": 3.2 + i * 0.2},
            "pop": 0.15 if i < 3 else (0.78 if i in (3, 4) else 0.25),
            "rain": {"3h": 1.2 if i in (3, 4) else 0.0},
        })
    return {
        "city": {"name": "Mumbai", "country": "IN"},
        "list": forecast,
        "current": {
            "temp": 29, "feels_like": 33, "humidity": 72,
            "weather": [{"description": "partly cloudy"}],
            "wind": {"speed": 4.1},
        },
    }

def ensure_sample_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SAMPLE_PATH.exists():
        SAMPLE_PATH.write_text(json.dumps(_sample_payload(), indent=2), encoding="utf-8")
    return SAMPLE_PATH

def _request_json(url, params):
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise WeatherError(f"Weather API request failed: {exc}") from exc
    except ValueError as exc:
        raise WeatherError("Weather API returned invalid JSON.") from exc

def _normalize_api(current_payload, forecast_payload, city):
    city_info = forecast_payload.get("city", {})
    current = current_payload
    weather = (current.get("weather") or [{}])[0]
    forecast = []
    for item in forecast_payload.get("list", []):
        item_weather = (item.get("weather") or [{}])[0]
        forecast.append({
            "datetime": datetime.fromtimestamp(item["dt"], timezone.utc).isoformat(),
            "temperature": item.get("main", {}).get("temp"),
            "feels_like": item.get("main", {}).get("feels_like"),
            "humidity": item.get("main", {}).get("humidity"),
            "description": item_weather.get("description", "unknown"),
            "wind_speed": item.get("wind", {}).get("speed"),
            "rain_probability": float(item.get("pop", 0) or 0) * 100,
            "rain_mm": (item.get("rain") or {}).get("3h", 0) or 0,
        })
    return {
        "city": city_info.get("name") or city,
        "country": city_info.get("country", ""),
        "current": {
            "temperature": current.get("main", {}).get("temp"),
            "feels_like": current.get("main", {}).get("feels_like"),
            "humidity": current.get("main", {}).get("humidity"),
            "description": weather.get("description", "unknown"),
            "wind_speed": current.get("wind", {}).get("speed"),
        },
        "forecast": forecast,
    }

def get_weather(city: str, mode: str = "simulation") -> dict:
    city = city.strip()
    if not city:
        raise WeatherError("City cannot be empty.")
    if mode == "simulation":
        ensure_sample_data()
        payload = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
        raw_current = payload["current"]
        raw_weather = (raw_current.get("weather") or [{}])[0]
        current = {
            "temperature": raw_current.get("temp"),
            "feels_like": raw_current.get("feels_like"),
            "humidity": raw_current.get("humidity"),
            "description": raw_weather.get("description", "unknown"),
            "wind_speed": (raw_current.get("wind") or {}).get("speed"),
        }
        forecast = []
        for item in payload.get("list", []):
            w = (item.get("weather") or [{}])[0]
            forecast.append({
                "datetime": datetime.fromtimestamp(item["dt"], timezone.utc).isoformat(),
                "temperature": item.get("main", {}).get("temp"),
                "feels_like": item.get("main", {}).get("feels_like"),
                "humidity": item.get("main", {}).get("humidity"),
                "description": w.get("description", "unknown"),
                "wind_speed": (item.get("wind") or {}).get("speed"),
                "rain_probability": float(item.get("pop", 0) or 0) * 100,
                "rain_mm": (item.get("rain") or {}).get("3h", 0) or 0,
            })
        return {"city": city, "country": "", "current": current, "forecast": forecast}
    if mode != "api":
        raise WeatherError("mode must be 'simulation' or 'api'.")
    if not OPENWEATHER_API_KEY:
        raise WeatherError("OPENWEATHER_API_KEY is missing. Add it to .env.")
    params = {"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"}
    current = _request_json(f"{API_BASE_URL}/weather", params)
    forecast = _request_json(f"{API_BASE_URL}/forecast", params)
    return _normalize_api(current, forecast, city)
