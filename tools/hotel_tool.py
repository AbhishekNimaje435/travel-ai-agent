"""Hotel recommendation tool: reads hotels.json and filters/ranks hotels."""

import json
import os
from typing import Optional

from langchain_core.tools import tool

DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "data")
HOTELS_FILE_PATH = os.path.join(DATA_DIRECTORY, "hotels.json")


def load_hotels_from_json(file_path: str = HOTELS_FILE_PATH) -> list[dict]:
    """Load hotel records from a JSON file.

    Args:
        file_path: Path to the hotels JSON file.

    Returns:
        A list of hotel dictionaries. Returns an empty list if the file
        is missing or cannot be parsed.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        print(f"Hotels file not found at: {file_path}")
    except json.JSONDecodeError as decode_error:
        print(f"Could not parse hotels file: {decode_error}")
    return []


def filter_hotels(
    hotels: list[dict],
    city: str,
    minimum_stars: int = 1,
    maximum_price_per_night: Optional[float] = None,
) -> list[dict]:
    """Return hotels in a city that meet the star and price limits.

    Args:
        hotels: All hotel records.
        city: City name, matched case-insensitively.
        minimum_stars: Lowest acceptable star rating.
        maximum_price_per_night: Highest acceptable price per night, or None for no limit.

    Returns:
        A list of hotels that match all the filters.
    """
    city_lower = city.strip().lower()
    filtered_hotels = []
    for hotel in hotels:
        if hotel["city"].lower() != city_lower:
            continue
        if hotel["stars"] < minimum_stars:
            continue
        if maximum_price_per_night is not None and hotel["price_per_night"] > maximum_price_per_night:
            continue
        filtered_hotels.append(hotel)
    return filtered_hotels


def rank_hotels(matching_hotels: list[dict]) -> list[dict]:
    """Sort hotels by stars (highest first), then by price (lowest first)."""
    return sorted(
        matching_hotels,
        key=lambda hotel: (-hotel["stars"], hotel["price_per_night"]),
    )


@tool
def search_hotels(
    city: str,
    minimum_stars: int = 1,
    maximum_price_per_night: Optional[float] = None,
) -> dict:
    """Find hotels in a city, filtered by minimum star rating and maximum price per night.

    Args:
        city: City name, for example "Goa".
        minimum_stars: Lowest acceptable star rating (1 to 5).
        maximum_price_per_night: Highest acceptable price per night in rupees, or None.

    Returns:
        A dictionary with the ranked hotel list and the top recommendation.
    """
    try:
        all_hotels = load_hotels_from_json()
        matching_hotels = filter_hotels(
            all_hotels, city, minimum_stars, maximum_price_per_night
        )

        if not matching_hotels:
            all_city_hotels = filter_hotels(all_hotels, city, minimum_stars=1)
            closest_hotels = rank_hotels(all_city_hotels)[:3]
            return {
                "message": (
                    f"No hotel in {city} matches {minimum_stars}+ stars and the price limit. "
                    "Showing the closest available hotels instead; treat them as alternatives."
                ),
                "ranked_hotels": closest_hotels,
                "top_recommendation": closest_hotels[0] if closest_hotels else None,
            }

        ranked_hotels = rank_hotels(matching_hotels)
        return {
            "message": f"Found {len(ranked_hotels)} hotel(s) in {city}.",
            "ranked_hotels": ranked_hotels,
            "top_recommendation": ranked_hotels[0],
        }
    except (KeyError, ValueError, TypeError) as error:
        return {"message": f"Error while searching hotels: {error}"}