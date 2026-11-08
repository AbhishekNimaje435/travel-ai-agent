"""Travel planning agent: Groq LLM that decides which travel tools to call."""

import json
import os
from datetime import date

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq

from tools.budget_tool import estimate_trip_budget
from tools.flight_tool import search_flights
from tools.hotel_tool import search_hotels
from tools.places_tool import search_places
from tools.weather_tool import get_weather_forecast

load_dotenv()

GROQ_MODEL_NAME = "openai/gpt-oss-20b"
AVAILABLE_GROQ_MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
]
DEFAULT_TEMPERATURE = 0.2
MAXIMUM_TOOL_ROUNDS = 12
MAXIMUM_ITEMS_PER_TOOL_OUTPUT = 5
GROQ_MAX_RETRIES = 5

JSON_OUTPUT_INSTRUCTIONS = """
Return ONLY a valid JSON object. No markdown, no code fences, no text before or after.
Use this exact structure:
{
  "trip_summary": {"source": "", "destination": "", "start_date": "", "end_date": "", "travellers": 0},
  "flight": {"flight_id": "", "airline": "", "departure": "", "arrival": "", "price": 0, "note": ""},
  "hotel": {"hotel_id": "", "name": "", "stars": 0, "price_per_night": 0, "amenities": [], "nights": 0},
  "weather": [{"date": "", "max_c": 0, "min_c": 0, "rain_percent": 0, "condition": ""}],
  "itinerary": [{"day": 1, "date": "", "places": [{"name": "", "type": "", "rating": 0}]}],
  "budget": {"flight": 0, "hotel": 0, "local_expenses": 0, "total": 0, "budget_limit": 0, "within_budget": true},
  "messages": []
}
Use only data returned by the tools. If a value is unknown, use null or an empty list. Numbers must be numbers, not strings.
"""

TOOLS_BY_NAME = {
    "search_flights": search_flights,
    "search_hotels": search_hotels,
    "search_places": search_places,
    "get_weather_forecast": get_weather_forecast,
    "estimate_trip_budget": estimate_trip_budget,
}
ALL_TOOL_NAMES = list(TOOLS_BY_NAME.keys())

TOOL_DESCRIPTIONS = {
    "search_flights": "- search_flights: finds one-way flights between two cities, with cheapest and fastest options. Accepts travel_date.",
    "search_hotels": "- search_hotels: finds hotels in a city, filtered by minimum stars and maximum price per night. Each hotel has an amenities list.",
    "search_places": "- search_places: finds attractions in a city, filtered by type and minimum rating.",
    "get_weather_forecast": "- get_weather_forecast: gives the daily forecast for a city between two dates.",
    "estimate_trip_budget": "- estimate_trip_budget: calculates the total cost from flight price, hotel price per night, number of days, and daily local expense.",
}

LIST_KEYS_IN_TOOL_OUTPUT = ("matching_flights", "ranked_hotels", "ranked_places", "daily_forecast")


def build_system_prompt(enabled_tool_names: list[str]) -> str:
    """Create the system prompt with today's date and only the enabled tools."""
    today = date.today().isoformat()
    tool_descriptions = "\n".join(TOOL_DESCRIPTIONS[tool_name] for tool_name in enabled_tool_names)
    return f"""You are an expert Indian travel planner. Today's date is {today}.

Tools enabled for this request:
{tool_descriptions}
Do not call any tool that is not in this list.

Tool usage rules:
1. Call each tool at most once for the same purpose. Do not repeat a call if you already have its result.
2. Stop calling tools as soon as you have the data you need, then write the final answer.
3. For the outbound flight, call search_flights with source_city, destination_city, and travel_date.
4. If the user asks for a return flight, call search_flights once more with source and destination swapped and travel_date set to the return date.
5. Choose the flight by the user's preference: cheapest_flight for "cheapest", fastest_flight for "fastest".
6. Call search_places only once, without place_type. If the user lists attraction interests, pick only the returned places whose type matches those interests. Never call search_places more than once.

Answer rules:
1. Use only tool data. Never invent flights, hotels, places, prices, timings, or activities.
2. Flights in the dataset are one-way. Do not call a flight round-trip unless both legs were searched.
3. Travellers: flight cost = flight price × number of travellers × number of flights (2 if return flight is included). Hotel rooms = travellers divided by 2, rounded up. Local expense = daily amount per person × travellers × days.
4. For estimate_trip_budget, pass flight_price as the total flight cost for all travellers and legs, hotel_price_per_night as hotel price × rooms, and daily_local_expense as the daily amount per person × travellers.
5. Compare the final total with the user's total budget. If it is over budget, say so clearly and suggest one or two cheaper options. Never hide an over-budget total.
6. If the user asked for hotel amenities, recommend only hotels whose amenities list contains every requested amenity. If none match, say which amenity is missing and show the closest option, as described in rule 10.
7. Use the user's star and price limits when calling search_hotels.
8. Places have only a name, type, and rating. Do not describe activities the tool did not provide.
9. Each place appears only once in the itinerary. Plan 2 to 3 places per day.
10. If search_hotels returns closest alternatives instead of exact matches, clearly say that no hotel matched the exact filters and list the alternatives with their stars and price.
11. Use the travel dates the user gave. If search_flights returns date_match "schedule", say that flight times come from the dataset schedule and may differ from real bookings. Never refuse a trip because of dataset dates.
12. Follow the user's extra requirements when the tools allow it. If you cannot, say so.
13. If a tool returns an error or no data, say so clearly and continue with what you have.

Final answer format:
1. Trip Summary (dates, travellers, preferences)
2. Flight Selected (outbound, and return if requested)
3. Hotel Recommendation
4. Weather for Each Day (if the weather tool is not enabled, write "Weather tool is turned off")
5. Day-wise Itinerary
6. Budget Breakdown (show the calculation and compare it with the user's total budget)
7. Reasoning: why these choices were made
"""


def create_chat_model(
    model_name: str,
    temperature: float,
    enabled_tool_names: list[str],
) -> ChatGroq:
    """Create the Groq chat model and attach only the enabled tools."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing. Add it to the .env file or Streamlit Secrets.")

    chat_model = ChatGroq(
        model=model_name,
        temperature=temperature,
        api_key=api_key,
        max_retries=GROQ_MAX_RETRIES,
    )
    enabled_tools = [TOOLS_BY_NAME[tool_name] for tool_name in enabled_tool_names]
    return chat_model.bind_tools(enabled_tools)


def shorten_tool_result(tool_result):
    """Keep only the first few items of list fields so the LLM receives fewer tokens."""
    if isinstance(tool_result, dict):
        for key in LIST_KEYS_IN_TOOL_OUTPUT:
            if isinstance(tool_result.get(key), list):
                tool_result[key] = tool_result[key][:MAXIMUM_ITEMS_PER_TOOL_OUTPUT]
    return tool_result


def run_tool_call(tool_call: dict) -> str:
    """Run one tool requested by the LLM and return its result as a JSON string."""
    tool_name = tool_call["name"]
    tool_arguments = tool_call["args"]

    selected_tool = TOOLS_BY_NAME.get(tool_name)
    if selected_tool is None:
        return json.dumps({"message": f"Unknown tool requested: {tool_name}"})

    try:
        tool_result = selected_tool.invoke(tool_arguments)
    except Exception as tool_error:
        tool_result = {"message": f"Tool {tool_name} failed: {tool_error}"}

    tool_result = shorten_tool_result(tool_result)
    return json.dumps(tool_result, default=str, ensure_ascii=False)


def run_travel_agent(
    user_query: str,
    model_name: str = GROQ_MODEL_NAME,
    temperature: float = DEFAULT_TEMPERATURE,
    enabled_tool_names: list[str] | None = None,
) -> str:
    """Run the agent loop until the LLM gives a final answer without tool calls.

    Args:
        user_query: The traveler's request in natural language.
        model_name: Groq model to use, for example "openai/gpt-oss-20b".
        temperature: LLM creativity, between 0 (strict) and 1 (creative).
        enabled_tool_names: Tools the agent may use. None means all tools.

    Returns:
        The final trip plan as text.
    """
    if enabled_tool_names is None:
        enabled_tool_names = ALL_TOOL_NAMES
    if not enabled_tool_names:
        raise ValueError("At least one tool must be enabled.")
    unknown_tools = [tool_name for tool_name in enabled_tool_names if tool_name not in TOOLS_BY_NAME]
    if unknown_tools:
        raise ValueError(f"Unknown tools: {unknown_tools}")

    chat_model = create_chat_model(model_name, temperature, enabled_tool_names)
    conversation_messages = [
        SystemMessage(content=build_system_prompt(enabled_tool_names)),
        HumanMessage(content=user_query),
    ]

    for _ in range(MAXIMUM_TOOL_ROUNDS):
        ai_response = chat_model.invoke(conversation_messages)
        conversation_messages.append(ai_response)

        if not ai_response.tool_calls:
            return ai_response.content

        for tool_call in ai_response.tool_calls:
            tool_output = run_tool_call(tool_call)
            conversation_messages.append(
                ToolMessage(content=tool_output, tool_call_id=tool_call["id"])
            )

    return "The agent could not finish the plan within the allowed number of steps. Please try a simpler query."


def run_travel_agent_json(
    user_query: str,
    model_name: str = GROQ_MODEL_NAME,
    temperature: float = DEFAULT_TEMPERATURE,
    enabled_tool_names: list[str] | None = None,
) -> dict:
    """Run the agent and return the trip plan as a Python dictionary (parsed JSON).

    Raises:
        ValueError: If the model's answer is not valid JSON even after one retry.
    """
    if enabled_tool_names is None:
        enabled_tool_names = ALL_TOOL_NAMES

    chat_model = create_chat_model(model_name, temperature, enabled_tool_names)
    conversation_messages = [
        SystemMessage(content=build_system_prompt(enabled_tool_names) + JSON_OUTPUT_INSTRUCTIONS),
        HumanMessage(content=user_query),
    ]

    # Step 1: let the agent use tools and build the plan
    final_text = ""
    for _ in range(MAXIMUM_TOOL_ROUNDS):
        ai_response = chat_model.invoke(conversation_messages)
        conversation_messages.append(ai_response)

        if not ai_response.tool_calls:
            final_text = ai_response.content
            break

        for tool_call in ai_response.tool_calls:
            tool_output = run_tool_call(tool_call)
            conversation_messages.append(
                ToolMessage(content=tool_output, tool_call_id=tool_call["id"])
            )

    # Step 2: parse the JSON, with one retry if it is invalid
    for attempt in range(2):
        cleaned_text = final_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            if attempt == 1:
                break
            conversation_messages.append(
                HumanMessage(content="Your last answer was not valid JSON. Return only the JSON object again.")
            )
            final_text = chat_model.invoke(conversation_messages).content

    raise ValueError("The agent did not return valid JSON. Please try again.")