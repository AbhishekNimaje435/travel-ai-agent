"""Flight search tool: reads flights.json and filters/ranks flights."""

import json
import os
from datetime import datetime
from typing import Optional

from langchain_core.tools import tool

DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "data")
FLIGHTS_FILE_PATH = os.path.join(DATA_DIRECTORY, "flights.json")


def load_flights_from_json(file_path: str = FLIGHTS_FILE_PATH) -> list[dict]:
    """Load flight records from a JSON file.

    Args:
        file_path: Path to the flights JSON file.

    Returns:
        A list of flight dictionaries. Returns an empty list if the file
        is missing or cannot be parsed.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        print(f"Flights file not found at: {file_path}")
    except json.JSONDecodeError as decode_error:
        print(f"Could not parse flights file: {decode_error}")
    return []


def filter_flights_by_route(
    flights: list[dict],
    source_city: str,
    destination_city: str,
) -> list[dict]:
    """Return flights that match the source and destination city (case-insensitive)."""
    source_lower = source_city.strip().lower()
    destination_lower = destination_city.strip().lower()
    return [
        flight
        for flight in flights
        if flight["from"].lower() == source_lower
        and flight["to"].lower() == destination_lower
    ]


def shift_flight_to_date(flight: dict, travel_date: str) -> dict:
    """Move a scheduled flight to the travel date, keeping its departure time and duration.

    The dataset dates are from 2025, so the same flight schedule is assumed to
    operate on the traveler's date.

    Args:
        flight: A flight record from flights.json.
        travel_date: Target date in YYYY-MM-DD format.

    Returns:
        A copy of the flight with adjusted departure and arrival times.
    """
    original_departure = datetime.fromisoformat(flight["departure_time"])
    original_arrival = datetime.fromisoformat(flight["arrival_time"])
    target_date = datetime.fromisoformat(travel_date).date()

    new_departure = datetime.combine(target_date, original_departure.time())
    flight_duration = original_arrival - original_departure
    new_arrival = new_departure + flight_duration

    shifted_flight = dict(flight)
    shifted_flight["departure_time"] = new_departure.isoformat()
    shifted_flight["arrival_time"] = new_arrival.isoformat()
    shifted_flight["dataset_date"] = original_departure.date().isoformat()
    return shifted_flight


def select_flights_for_date(
    matching_flights: list[dict],
    travel_date: Optional[str],
) -> tuple[list[dict], str]:
    """Return the matching flights, scheduled on the travel date if one is given.

    Returns:
        A tuple of (flights, match type). Match type is "any" when no date is given,
        and "schedule" when the flights were moved to the travel date.
    """
    if not travel_date:
        return matching_flights, "any"

    scheduled_flights = [shift_flight_to_date(flight, travel_date) for flight in matching_flights]
    return scheduled_flights, "schedule"


def find_cheapest_flight(matching_flights: list[dict]) -> Optional[dict]:
    """Return the flight with the lowest price, or None if the list is empty."""
    if not matching_flights:
        return None
    return min(matching_flights, key=lambda flight: flight["price"])


def find_fastest_flight(matching_flights: list[dict]) -> Optional[dict]:
    """Return the flight with the shortest duration, or None if the list is empty."""
    if not matching_flights:
        return None

    def flight_duration_in_minutes(flight: dict) -> float:
        departure = datetime.fromisoformat(flight["departure_time"])
        arrival = datetime.fromisoformat(flight["arrival_time"])
        return (arrival - departure).total_seconds() / 60

    return min(matching_flights, key=flight_duration_in_minutes)


@tool
def search_flights(
    source_city: str,
    destination_city: str,
    travel_date: Optional[str] = None,
) -> dict:
    """Search flights between two Indian cities and suggest the cheapest and fastest options.

    If travel_date is given, the matching scheduled flights are shown on that date,
    keeping their departure times. The dataset dates are historical, so this is a schedule-based estimate.

    Args:
        source_city: Departure city, for example "Hyderabad".
        destination_city: Arrival city, for example "Goa".
        travel_date: Travel date in YYYY-MM-DD format, or None.

    Returns:
        A dictionary with the message, match type, flights, cheapest flight, and fastest flight.
    """
    try:
        all_flights = load_flights_from_json()
        matching_flights = filter_flights_by_route(all_flights, source_city, destination_city)

        if not matching_flights:
            return {
                "message": f"No flights found from {source_city} to {destination_city}.",
                "date_match": "none",
                "matching_flights": [],
                "cheapest_flight": None,
                "fastest_flight": None,
            }

        selected_flights, date_match = select_flights_for_date(matching_flights, travel_date)

        if date_match == "schedule":
            message = (
                f"Found {len(selected_flights)} scheduled flight(s) from {source_city} to "
                f"{destination_city}, adjusted to {travel_date}. Times come from the dataset schedule "
                f"and may differ from real bookings."
            )
        else:
            message = f"Found {len(selected_flights)} flight(s) from {source_city} to {destination_city}."

        return {
            "message": message,
            "date_match": date_match,
            "matching_flights": selected_flights,
            "cheapest_flight": find_cheapest_flight(selected_flights),
            "fastest_flight": find_fastest_flight(selected_flights),
        }
    except (KeyError, ValueError, TypeError) as error:
        return {"message": f"Error while searching flights: {error}"}