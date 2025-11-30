# app/tools/weather.py
import logging
from typing import Any, Dict
from urllib.parse import quote

import httpx

from app.tools.base import ToolSpec

logger = logging.getLogger("app.tools.weather")


class WeatherTool(ToolSpec):
    def __init__(self):
        super().__init__()
        self.name = "weather"
        self.description = (
            "Get current weather information for a location (uses wttr.in)"
        )

    def _run(self, location: str) -> str:
        """Get weather for a given location using wttr.in service."""
        try:
            location = (location or "").strip()
            if not location:
                return "Error: Location is required"

            # Sanitize and URL-encode the location to avoid 404s on phrases like 'Hyderabad today'
            safe_loc = " ".join(
                part for part in location.split()
            )  # collapse whitespace
            url = f"https://wttr.in/{quote(safe_loc)}"
            params = {"format": "j1"}  # JSON format

            # Use httpx.request (no context-manager) to make mocking in tests simpler
            resp = httpx.request("GET", url, params=params, timeout=10.0)
            resp.raise_for_status()

            data = resp.json()

            # Defensive access to keys (KeyError handled below)
            current = data["current_condition"][0]
            weather_desc = current.get("weatherDesc", [{}])[0].get("value", "N/A")
            temp_c = current.get("temp_C", "N/A")
            temp_f = current.get("temp_F", "N/A")
            humidity = current.get("humidity", "N/A")
            wind_speed = current.get("windspeedKmph", "N/A")
            wind_dir = current.get("winddir16Point", "N/A")

            nearest_area = data.get("nearest_area", [{}])[0]
            area_name = nearest_area.get("areaName", [{}])[0].get("value", location)
            country = nearest_area.get("country", [{}])[0].get("value", "N/A")

            result_lines = [
                f"Weather for {area_name}, {country}:",
                f"Condition: {weather_desc}",
                f"Temperature: {temp_c}°C ({temp_f}°F)",
                f"Humidity: {humidity}%",
                f"Wind: {wind_speed} km/h {wind_dir}",
            ]

            # Today's forecast (defensive)
            today = data.get("weather", [{}])[0]
            maxtemp = today.get("maxtempC", "N/A")
            mintemp = today.get("mintempC", "N/A")
            result_lines.append("")
            result_lines.append("Today's forecast:")
            result_lines.append(f"Max: {maxtemp}°C | Min: {mintemp}°C")

            return "\n".join(result_lines)

        except httpx.HTTPStatusError as e:
            status = getattr(e.response, "status_code", "unknown")
            logger.error("Weather API HTTP error: %s (url=%s)", status, url)
            return f"Error fetching weather data: HTTP {status}"
        except KeyError as e:
            logger.exception("Error parsing weather data: missing key %s", e)
            return f"Error parsing weather data: Missing key {e}"
        except Exception as e:
            logger.exception("Unexpected error in WeatherTool: %s", e)
            return f"Error getting weather: {str(e)}"
