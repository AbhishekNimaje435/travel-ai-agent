from tools.weather_tool import get_weather_forecast

result = get_weather_forecast.invoke(
    {
        "city": "Goa",
        "start_date": "2026-11-10",
        "end_date": "2026-11-12",
    }
)
print(result)
