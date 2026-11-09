from tools.hotel_tool import search_hotels

result = search_hotels.invoke({"city": "Goa", "minimum_stars": 4, "maximum_price_per_night": 5000})
print(result)
