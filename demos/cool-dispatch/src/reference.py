"""Independent reference air temperature from Open-Meteo (free, no key).
Recent and future dates use the forecast API; older dates use the ERA5 archive."""
from __future__ import annotations

from datetime import date, datetime

import httpx

FORECAST = "https://api.open-meteo.com/v1/forecast"
ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"


def hourly_air_temp(lat: float, lon: float, day: str, today: date | None = None) -> dict[str, float]:
    """Return {"YYYY-MM-DDTHH:00": temp_c} in the location's local time zone."""
    today = today or date.today()
    url = ARCHIVE if (today - date.fromisoformat(day)).days > 60 else FORECAST
    r = httpx.get(url, params={"latitude": lat, "longitude": lon, "hourly": "temperature_2m",
                               "timezone": "auto", "start_date": day, "end_date": day}, timeout=30)
    r.raise_for_status()
    h = r.json()["hourly"]
    return {t: v for t, v in zip(h["time"], h["temperature_2m"]) if v is not None}


def at(series: dict[str, float], departure: str) -> float | None:
    """Temperature at the departure's hour (local wall time 'YYYY-MM-DDTHH:MM')."""
    key = datetime.fromisoformat(departure[:16]).strftime("%Y-%m-%dT%H:00")
    return series.get(key)
