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
MAXIMUM_TOOL_ROUNDS = 8
MAXIMUM_ITEMS_PER_TOOL_OUTPUT = 5
GROQ_MAX_RETRIES = 5

AVAILABLE_TOOLS = [
    search_flights,
    search_hotels,
    search_places,
    get_weather_forecast,
    estimate_trip_budget,
]
TOOLS_BY_NAME = {tool.name: tool for tool in AVAILABLE_TOOLS}

# Keys in tool outputs that contain lists, which we shorten to save tokens
LIST_KEYS_IN_TOOL_OUTPUT = ("matching_flights", "ranked_hotels", "ranked_places", "daily_forecast")


def build_system_prompt() -> str:
    """Create the system prompt with today's date so the agent can resolve relative dates."""
    today = date.today().isoformat()
    return f"""You are an expert Indian travel planner. Today's date is {today}.

Your job is to plan a complete trip using the tools you have:
- search_flights: finds flights between two cities and gives the cheapest and fastest option.
- search_hotels: finds hotels in a city, filtered by stars and price.
- search_places: finds attractions in a city, filtered by type and rating.
- get_weather_forecast: gives the daily forecast for a city between two dates.
- estimate_trip_budget: calculates the total cost from flight price, hotel price, and number of days.

Tool usage rules:
1. Call each tool at most once for the same purpose. Do not repeat a tool call if you already have its result.
2. As soon as you have the flight, hotel, places, weather, and budget data, stop calling tools and write the final answer.
3. Never call a tool that is not needed for the trip plan.

Answer rules:
1. Use only the data returned by the tools. Never invent flights, hotels, places, prices, timings, or activities.
2. Flights in the dataset are one-way. Do not call a flight "round-trip" unless you searched for the return flight too.
3. Use the exact flight, hotel, and budget numbers from the tool output. Do not recalculate them yourself unless you show the calculation.
4. Places have only a name, city, type, and rating. Do not describe activities (like boat rides or treks) that the tool did not provide. Just mention the name, type, and rating.
5. Pick the cheapest flight unless the user asks for the fastest. Pick the top-rated hotel that meets the user's star and budget limits.
6. If the user does not give dates, state the assumed dates clearly at the top of the answer.
7. If a tool returns no data or an error, say so clearly and continue with what you have.
8. Pass travel_date (YYYY-MM-DD) to search_flights. If date_match is "schedule", tell the user that flight times come from the dataset schedule and may differ from real bookings, and use the adjusted departure time in the itinerary.
9. Never refuse to plan a trip because of dataset dates. Always plan for the dates the user requested.
10. Do not repeat the same place on different days. Each place appears only once in the itinerary.
11. If search_hotels returns closest alternatives instead of exact matches, clearly say that no hotel matched the exact filters and list the alternatives with their stars and price.

Final answer format:
1. Trip Summary (including assumed dates)
2. Flight Selected
3. Hotel Recommendation
4. Weather for Each Day
5. Day-wise Itinerary (2 to 3 places per day, using only tool data)
6. Budget Breakdown (use the budget tool output)
7. Reasoning: why these choices were made
"""


def create_chat_model() -> ChatGroq:
    """Create the Groq chat model and attach the travel tools to it."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing. Add it to the .env file.")

    chat_model = ChatGroq(
        model=GROQ_MODEL_NAME,
        temperature=0,
        api_key=api_key,
        max_retries=GROQ_MAX_RETRIES,
    )
    return chat_model.bind_tools(AVAILABLE_TOOLS)


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


def run_travel_agent(user_query: str) -> str:
    """Run the agent loop until the LLM gives a final answer without tool calls.

    Args:
        user_query: The traveler's request in natural language.

    Returns:
        The final trip plan as text.
    """
    chat_model = create_chat_model()
    conversation_messages = [
        SystemMessage(content=build_system_prompt()),
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