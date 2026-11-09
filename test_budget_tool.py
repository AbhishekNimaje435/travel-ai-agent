from tools.budget_tool import estimate_trip_budget

result = estimate_trip_budget.invoke(
    {
        "flight_price": 2907,
        "hotel_price_per_night": 1232,
        "number_of_days": 3,
    }
)
print(result)
