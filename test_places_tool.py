from tools.places_tool import search_places

result = search_places.invoke({"city": "Kolkata", "minimum_rating": 4.0})
print(result)