"""Weather lookup tool: fetches daily forecasts from the free Open-Meteo API."""

from typing import Optional

import requests
from langchain_core.tools import tool

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 10

# Coordinates for the cities present in the datasets
CITY_COORDINATES = {
    "delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "goa": (15.2993, 74.1240),
    "bangalore": (12.9716, 77.5946),
    "chennai": (13.0827, 80.2707),
    "hyderabad": (17.3850, 78.4867),
    "kolkata": (22.5726, 88.3639),
    "jaipur": (26.9124, 75.7873),
}

# Open-Meteo WMO weather codes mapped to readable descriptions
WEATHER_CODE_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    80: "Rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
}


def get_city_coordinates(city: str) -> Optional[tuple[float, float]]:
    """Return (latitude, longitude) for a known city, or None if the city is not supported."""
    return CITY_COORDINATES.get(city.strip().lower())


def fetch_daily_forecast(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
) -> dict:
    """Call Open-Meteo and return the raw daily forecast response.

    Args:
        latitude: Latitude of the location.
        longitude: Longitude of the location.
        start_date: First date in YYYY-MM-DD format.
        end_date: Last date in YYYY-MM-DD format.

    Returns:
        The JSON response from Open-Meteo as a dictionary.

    Raises:
        requests.RequestException: If the network call fails or Open-Meteo returns an error.
    """
    query_parameters = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode",
        "timezone": "auto",
        "start_date": start_date,
        "end_date": end_date,
    }
    response = requests.get(
        OPEN_METEO_FORECAST_URL,
        params=query_parameters,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def parse_daily_forecast(raw_forecast: dict) -> list[dict]:
    """Convert Open-Meteo's column-based daily data into one dictionary per day."""
    daily_data = raw_forecast["daily"]
    forecast_days = []
    for index, date in enumerate(daily_data["time"]):
        weather_code = daily_data["weathercode"][index]
        forecast_days.append(
            {
                "date": date,
                "max_temperature_c": daily_data["temperature_2m_max"][index],
                "min_temperature_c": daily_data["temperature_2m_min"][index],
                "rain_probability_percent": daily_data["precipitation_probability_max"][index],
                "condition": WEATHER_CODE_DESCRIPTIONS.get(weather_code, "Unknown"),
            }
        )
    return forecast_days


@tool
def get_weather_forecast(city: str, start_date: str, end_date: str) -> dict:
    """Get the daily weather forecast for a city between two dates.

    Args:
        city: City name, for example "Goa". Supported cities: Delhi, Mumbai, Goa, Bangalore, Chennai, Hyderabad, Kolkata, Jaipur.
        start_date: First travel date in YYYY-MM-DD format.
        end_date: Last travel date in YYYY-MM-DD format.

    Returns:
        A dictionary with the message and a list of daily forecasts.
    """
    coordinates = get_city_coordinates(city)
    if coordinates is None:
        return {"message": f"Weather data is not available for {city}.", "daily_forecast": []}

    latitude, longitude = coordinates
    try:
        raw_forecast = fetch_daily_forecast(latitude, longitude, start_date, end_date)
        daily_forecast = parse_daily_forecast(raw_forecast)
        return {
            "message": f"Weather forecast for {city} from {start_date} to {end_date}.",
            "daily_forecast": daily_forecast,
        }
    except requests.HTTPError as http_error:
        return {
            "message": f"Open-Meteo could not return a forecast for these dates. Forecasts are usually available only about 16 days ahead. Details: {http_error}",
            "daily_forecast": [],
        }
    except requests.RequestException as network_error:
        return {"message": f"Network error while fetching weather: {network_error}", "daily_forecast": []}
    except (KeyError, ValueError, TypeError) as parse_error:
        return {"message": f"Error while reading weather data: {parse_error}", "daily_forecast": []}
