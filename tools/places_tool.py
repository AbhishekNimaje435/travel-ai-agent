"""Places discovery tool: reads places.json and recommends attractions."""

import json
import os
from typing import Optional

from langchain_core.tools import tool

DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "data")
PLACES_FILE_PATH = os.path.join(DATA_DIRECTORY, "places.json")


def load_places_from_json(file_path: str = PLACES_FILE_PATH) -> list[dict]:
    """Load place records from a JSON file.

    Args:
        file_path: Path to the places JSON file.

    Returns:
        A list of place dictionaries. Returns an empty list if the file
        is missing or cannot be parsed.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        print(f"Places file not found at: {file_path}")
    except json.JSONDecodeError as decode_error:
        print(f"Could not parse places file: {decode_error}")
    return []


def filter_places(
    places: list[dict],
    city: str,
    place_type: Optional[str] = None,
    minimum_rating: float = 0.0,
) -> list[dict]:
    """Return places in a city that match the optional type and rating filters.

    Args:
        places: All place records.
        city: City name, matched case-insensitively.
        place_type: Attraction type such as "temple", "beach", or "fort". None means any type.
        minimum_rating: Lowest acceptable rating.

    Returns:
        A list of matching places.
    """
    city_lower = city.strip().lower()
    type_lower = place_type.strip().lower() if place_type else None
    filtered_places = []
    for place in places:
        if place["city"].lower() != city_lower:
            continue
        if type_lower and place["type"].lower() != type_lower:
            continue
        if place["rating"] < minimum_rating:
            continue
        filtered_places.append(place)
    return filtered_places


def rank_places(matching_places: list[dict]) -> list[dict]:
    """Sort places by rating, highest first."""
    return sorted(matching_places, key=lambda place: place["rating"], reverse=True)


@tool
def search_places(
    city: str,
    place_type: Optional[str] = None,
    minimum_rating: float = 0.0,
) -> dict:
    """Find tourist attractions in a city, optionally filtered by type and minimum rating.

    Args:
        city: City name, for example "Jaipur".
        place_type: Attraction type such as "temple", "beach", "fort", "park", "museum", "lake", or "market". Leave empty for all types.
        minimum_rating: Lowest acceptable rating (0 to 5).

    Returns:
        A dictionary with the ranked list of places and the top recommendations.
    """
    try:
        all_places = load_places_from_json()
        matching_places = filter_places(all_places, city, place_type, minimum_rating)

        if not matching_places:
            return {
                "message": f"No places found in {city} with the given filters.",
                "ranked_places": [],
                "top_recommendations": [],
            }

        ranked_places = rank_places(matching_places)
        return {
            "message": f"Found {len(ranked_places)} place(s) in {city}.",
            "ranked_places": ranked_places,
            "top_recommendations": ranked_places[:3],
        }
    except (KeyError, ValueError, TypeError, AttributeError) as error:
        return {"message": f"Error while searching places: {error}"}
