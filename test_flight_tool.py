from tools.flight_tool import search_flights

result = search_flights.invoke({"source_city": "Hyderabad", "destination_city": "Delhi"})
print(result)
