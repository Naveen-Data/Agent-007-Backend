import json
from typing import Any, Dict

import httpx

from app.tools.base import ToolSpec


class WeatherTool(ToolSpec):

    def __init__(self):
        super().__init__()
        self.name = "weather"
        self.description = "Get current weather information for a location"

    def _run(self, location: str) -> str:
        """Get weather for a given location using wttr.in service"""
        try:
            # Clean and encode the location properly
            location = location.strip()
            if not location:
                return "Error: Location is required"

            # Use wttr.in - a free weather service that doesn't require API key
            url = f"https://wttr.in/{location}"
            params = {"format": "j1"}  # JSON format

            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                # Extract current weather
                current = data["current_condition"][0]
                weather_desc = current["weatherDesc"][0]["value"]
                temp_c = current["temp_C"]
                temp_f = current["temp_F"]
                humidity = current["humidity"]
                wind_speed = current["windspeedKmph"]
                wind_dir = current["winddir16Point"]

                # Get location info
                nearest_area = data["nearest_area"][0]
                area_name = nearest_area["areaName"][0]["value"]
                country = nearest_area["country"][0]["value"]

                result = f"Weather for {area_name}, {country}:\n"
                result += f"Condition: {weather_desc}\n"
                result += f"Temperature: {temp_c}°C ({temp_f}°F)\n"
                result += f"Humidity: {humidity}%\n"
                result += f"Wind: {wind_speed} km/h {wind_dir}\n"

                # Add today's forecast
                today = data["weather"][0]
                result += f"\nToday's forecast:\n"
                result += f"Max: {today['maxtempC']}°C | Min: {today['mintempC']}°C\n"

                return result

        except httpx.HTTPStatusError as e:
            return f"Error fetching weather data: HTTP {e.response.status_code}"
        except KeyError as e:
            return f"Error parsing weather data: Missing key {e}"
        except Exception as e:
            return f"Error getting weather: {str(e)}"
