"""Builds the natural language query that is sent to the travel agent."""

from datetime import date


def build_user_query(
    source_city: str,
    destination_city: str,
    start_date: date,
    end_date: date,
    travellers: int,
    flight_preference: str,
    include_return_flight: bool,
    minimum_stars: int,
    maximum_hotel_price: int,
    daily_local_expense: int,
    total_budget: int,
    amenities: list[str],
    interests: list[str],
    extra_requirements: str,
) -> str:
    """Turn the trip form values into a natural language query for the agent."""
    trip_days = (end_date - start_date).days + 1
    query_lines = [
        f"Plan a {trip_days}-day trip from {source_city} to {destination_city}.",
        f"Outbound travel date: {start_date.isoformat()}. Return date: {end_date.isoformat()}.",
        f"Number of travellers: {travellers}.",
        f"Flight preference: {flight_preference.lower()}.",
    ]

    if include_return_flight:
        query_lines.append(
            f"Include a return flight from {destination_city} to {source_city} on {end_date.isoformat()}."
        )
    else:
        query_lines.append("One-way trip only, no return flight.")

    query_lines.append(f"Hotel: at least {minimum_stars} stars, up to Rs {maximum_hotel_price} per night.")
    if amenities:
        query_lines.append(f"Hotel amenities required: {', '.join(amenities)}.")
    else:
        query_lines.append("No specific hotel amenities required.")

    if interests:
        query_lines.append(f"Attraction interests: {', '.join(interests)}.")
    else:
        query_lines.append("No specific attraction interests. Show the top-rated places.")

    query_lines.append(f"Food and local travel: Rs {daily_local_expense} per person per day.")
    query_lines.append(f"Total trip budget: Rs {total_budget} for all travellers.")

    if extra_requirements.strip():
        query_lines.append(f"Extra requirements from the user: {extra_requirements.strip()}")

    return "\n".join(query_lines)
