"""Budget estimation tool: adds flight, hotel, and per-day expenses into a trip total."""

from langchain_core.tools import tool

DEFAULT_DAILY_LOCAL_EXPENSE_RUPEES = 1500


def calculate_trip_budget(
    flight_price: float,
    hotel_price_per_night: float,
    number_of_nights: int,
    daily_local_expense: float = DEFAULT_DAILY_LOCAL_EXPENSE_RUPEES,
    number_of_days: int = 0,
) -> dict:
    """Calculate the total trip cost from its main components.

    Args:
        flight_price: Cost of the selected flight in rupees.
        hotel_price_per_night: Hotel price for one night in rupees.
        number_of_nights: Number of nights the traveler stays at the hotel.
        daily_local_expense: Food and local travel cost per day in rupees.
        number_of_days: Number of trip days used for local expenses.

    Returns:
        A dictionary with each cost component and the total.
    """
    hotel_total = hotel_price_per_night * number_of_nights
    local_total = daily_local_expense * number_of_days
    grand_total = flight_price + hotel_total + local_total

    return {
        "flight_cost": round(flight_price, 2),
        "hotel_cost": round(hotel_total, 2),
        "local_expense_cost": round(local_total, 2),
        "total_cost": round(grand_total, 2),
    }


@tool
def estimate_trip_budget(
    flight_price: float,
    hotel_price_per_night: float,
    number_of_days: int,
    daily_local_expense: float = DEFAULT_DAILY_LOCAL_EXPENSE_RUPEES,
) -> dict:
    """Estimate the total budget for a trip using the flight price, hotel price, and daily expenses.

    The number of hotel nights is calculated as number_of_days minus one, because
    a trip that lasts N days usually needs N minus one nights of accommodation.

    Args:
        flight_price: Cost of the selected flight in rupees.
        hotel_price_per_night: Hotel price for one night in rupees.
        number_of_days: Total number of trip days, for example 3.
        daily_local_expense: Food and local travel cost per day in rupees. Defaults to 1500.

    Returns:
        A dictionary with the message and the budget breakdown.
    """
    try:
        if number_of_days < 1:
            return {"message": "Trip must be at least 1 day long.", "budget_breakdown": None}

        number_of_nights = max(number_of_days - 1, 0)
        breakdown = calculate_trip_budget(
            flight_price=flight_price,
            hotel_price_per_night=hotel_price_per_night,
            number_of_nights=number_of_nights,
            daily_local_expense=daily_local_expense,
            number_of_days=number_of_days,
        )
        return {
            "message": f"Estimated budget for a {number_of_days}-day trip.",
            "budget_breakdown": breakdown,
        }
    except (TypeError, ValueError) as error:
        return {"message": f"Error while estimating budget: {error}", "budget_breakdown": None}