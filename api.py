"""FastAPI backend: exposes the travel agent as a JSON API and serves the frontend."""

import json
import os
from datetime import date
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field, model_validator

from agent.query_builder import build_user_query

from tools.budget_tool import calculate_trip_budget

load_dotenv()
from agent.travel_agent import (
    ALL_TOOL_NAMES,
    AVAILABLE_GROQ_MODELS,
    DEFAULT_TEMPERATURE,
    run_travel_agent,
    run_travel_agent_json,
)
BASE_DIRECTORY = Path(__file__).parent
FRONTEND_DIRECTORY = BASE_DIRECTORY / "frontend"
HOTELS_FILE_PATH = BASE_DIRECTORY / "data" / "hotels.json"
PLACES_FILE_PATH = BASE_DIRECTORY / "data" / "places.json"

app = FastAPI(title="AI Travel Planner API")


class TripRequest(BaseModel):
    """Trip details sent by the frontend form."""

    source_city: str
    destination_city: str
    start_date: date
    end_date: date
    travellers: int = Field(default=1, ge=1, le=10)
    flight_preference: str = "Cheapest"
    include_return_flight: bool = True
    minimum_stars: int = Field(default=4, ge=1, le=5)
    maximum_hotel_price: int = Field(default=7000, ge=500, le=20000)
    daily_local_expense: int = Field(default=1500, ge=0, le=10000)
    total_budget: int = Field(default=30000, ge=1000, le=500000)
    amenities: list[str] = []
    interests: list[str] = []
    extra_requirements: str = ""
    model_name: str = AVAILABLE_GROQ_MODELS[0]
    temperature: float = Field(default=DEFAULT_TEMPERATURE, ge=0.0, le=1.0)
    enabled_tools: list[str] = ALL_TOOL_NAMES

    @model_validator(mode="after")
    def check_cities_and_dates(self):
        """Reject trips with the same source and destination, or an end date before the start date."""
        if self.source_city == self.destination_city:
            raise ValueError("Source and destination cities should be different.")
        if self.end_date < self.start_date:
            raise ValueError("End date start date se pehle nahi ho sakti.")
        return self


CHAT_HISTORY_LIMIT = 10
CHAT_SYSTEM_PROMPT = (
    "You are a friendly travel assistant for India and world travel. "
    "Answer travel questions briefly, in under 150 words. "
    "You do not have live prices, live flight data, or booking access. "
    "If the user asks for live prices or bookings, say that and suggest checking the airline or hotel website."
)


class ChatMessage(BaseModel):
    """One message in the chat history."""

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1000)


class ChatRequest(BaseModel):
    """Chat history sent by the frontend."""

    messages: list[ChatMessage] = Field(min_length=1, max_length=CHAT_HISTORY_LIMIT)
    model_name: str = AVAILABLE_GROQ_MODELS[0]


def load_hotels() -> list[dict]:
    """Read all hotels from hotels.json. Returns an empty list if the file cannot be read."""
    try:
        with open(HOTELS_FILE_PATH, "r", encoding="utf-8") as hotels_file:
            return json.load(hotels_file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def load_places() -> list[dict]:
    """Read all places from places.json. Returns an empty list if the file cannot be read."""
    try:
        with open(PLACES_FILE_PATH, "r", encoding="utf-8") as places_file:
            return json.load(places_file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


@app.get("/api/health")
def health_check() -> dict:
    """Simple check that the backend is running."""
    return {"status": "ok"}


@app.get("/api/options")
def get_options() -> dict:
    """Return the models and tools the frontend can offer in its settings."""
    return {"models": AVAILABLE_GROQ_MODELS, "tools": ALL_TOOL_NAMES}


@app.get("/api/cities")
def get_cities() -> dict:
    """Return the list of cities that appear in hotels.json, for the filter dropdown."""
    cities = sorted({hotel["city"] for hotel in load_hotels()})
    return {"cities": cities}


@app.get("/api/hotels")
def search_hotels_api(
    city: str = Query(..., min_length=2),
    min_stars: int = Query(default=1, ge=1, le=5),
    max_price: int = Query(default=20000, ge=0),
    sort_by: str = Query(default="stars", pattern="^(stars|price_low|price_high)$"),
) -> dict:
    """Return hotels in a city, filtered by stars and maximum price per night."""
    city_lower = city.strip().lower()
    matching_hotels = [
        hotel
        for hotel in load_hotels()
        if hotel["city"].lower() == city_lower
        and hotel["stars"] >= min_stars
        and hotel["price_per_night"] <= max_price
    ]

    if sort_by == "price_low":
        matching_hotels.sort(key=lambda hotel: hotel["price_per_night"])
    elif sort_by == "price_high":
        matching_hotels.sort(key=lambda hotel: hotel["price_per_night"], reverse=True)
    else:
        matching_hotels.sort(key=lambda hotel: (-hotel["stars"], hotel["price_per_night"]))

    return {"city": city, "count": len(matching_hotels), "hotels": matching_hotels}


@app.get("/api/place-options")
def get_place_options() -> dict:
    """Return the cities and attraction types available in places.json, for the filter dropdowns."""
    places = load_places()
    cities = sorted({place["city"] for place in places})
    types = sorted({place["type"] for place in places})
    return {"cities": cities, "types": types}


@app.get("/api/places")
def search_places_api(
    city: str = Query(..., min_length=2),
    place_type: str = Query(default="all"),
    min_rating: float = Query(default=0.0, ge=0.0, le=5.0),
    sort_by: str = Query(default="rating", pattern="^(rating|name)$"),
) -> dict:
    """Return places in a city, filtered by type and minimum rating."""
    city_lower = city.strip().lower()
    type_lower = place_type.strip().lower()

    matching_places = [
        place
        for place in load_places()
        if place["city"].lower() == city_lower
        and (type_lower == "all" or place["type"].lower() == type_lower)
        and place["rating"] >= min_rating
    ]

    if sort_by == "name":
        matching_places.sort(key=lambda place: place["name"])
    else:
        matching_places.sort(key=lambda place: place["rating"], reverse=True)

    return {"city": city, "count": len(matching_places), "places": matching_places}


@app.get("/api/itinerary")
def build_itinerary(
    city: str = Query(..., min_length=2),
    days: int = Query(default=3, ge=1, le=7),
    interests: str = Query(default=""),
    min_rating: float = Query(default=4.0, ge=0.0, le=5.0),
    places_per_day: int = Query(default=2, ge=1, le=3),
    hotel_stars: int = Query(default=4, ge=1, le=5),
    max_hotel_price: int = Query(default=7000, ge=500, le=20000),
    flight_price: int = Query(default=0, ge=0),
    daily_local_expense: int = Query(default=1500, ge=0),
) -> dict:
    """Build a day-wise itinerary from local data only (no LLM call)."""
    city_lower = city.strip().lower()
    wanted_types = {type_name.strip().lower() for type_name in interests.split(",") if type_name.strip()}

    candidate_places = [
        place
        for place in load_places()
        if place["city"].lower() == city_lower
        and place["rating"] >= min_rating
        and (not wanted_types or place["type"].lower() in wanted_types)
    ]
    candidate_places.sort(key=lambda place: place["rating"], reverse=True)

    # Each place is used only once, so the itinerary never repeats a place
    needed_place_count = days * places_per_day
    selected_places = candidate_places[:needed_place_count]

    itinerary_days = []
    for day_number in range(1, days + 1):
        start_index = (day_number - 1) * places_per_day
        day_places = selected_places[start_index : start_index + places_per_day]
        itinerary_days.append({"day": day_number, "places": day_places})

    matching_hotels = [
        hotel
        for hotel in load_hotels()
        if hotel["city"].lower() == city_lower
        and hotel["stars"] >= hotel_stars
        and hotel["price_per_night"] <= max_hotel_price
    ]
    matching_hotels.sort(key=lambda hotel: (-hotel["stars"], hotel["price_per_night"]))
    top_hotel = matching_hotels[0] if matching_hotels else None

    budget = None
    if top_hotel:
        budget = calculate_trip_budget(
            flight_price=flight_price,
            hotel_price_per_night=top_hotel["price_per_night"],
            number_of_nights=max(days - 1, 0),
            daily_local_expense=daily_local_expense,
            number_of_days=days,
        )

    messages = []
    if len(selected_places) < needed_place_count:
        messages.append(
            f"Only {len(selected_places)} places found, {needed_place_count} were needed. "
            "Try lowering the rating or changing the interests."
        )
    if top_hotel is None:
        messages.append("No hotel matched these filters in this city, so hotel cost is not included.")
    if flight_price == 0:
        messages.append("No flight cost was entered, so the total does not include a flight.")

    return {
        "city": city,
        "days": itinerary_days,
        "hotel": top_hotel,
        "budget": budget,
        "messages": messages,
    }


@app.post("/api/plan")
def create_trip_plan(request: TripRequest) -> dict:
    """Run the travel agent for the given trip details and return the plan text."""
    user_query = build_user_query(
        source_city=request.source_city,
        destination_city=request.destination_city,
        start_date=request.start_date,
        end_date=request.end_date,
        travellers=request.travellers,
        flight_preference=request.flight_preference,
        include_return_flight=request.include_return_flight,
        minimum_stars=request.minimum_stars,
        maximum_hotel_price=request.maximum_hotel_price,
        daily_local_expense=request.daily_local_expense,
        total_budget=request.total_budget,
        amenities=request.amenities,
        interests=request.interests,
        extra_requirements=request.extra_requirements,
    )
    try:
        plan_text = run_travel_agent(
            user_query,
            model_name=request.model_name,
            temperature=request.temperature,
            enabled_tool_names=request.enabled_tools,
        )
    except ValueError as configuration_error:
        raise HTTPException(status_code=400, detail=str(configuration_error))
    except Exception as unexpected_error:
        raise HTTPException(
            status_code=500,
            detail=f"Trip plan generate nahi ho saka: {unexpected_error}",
        )
    return {"plan": plan_text}

@app.post("/api/plan/json")
def create_trip_plan_json(request: TripRequest) -> dict:
    """Run the travel agent and return the trip plan as structured JSON."""
    user_query = build_user_query(
        source_city=request.source_city,
        destination_city=request.destination_city,
        start_date=request.start_date,
        end_date=request.end_date,
        travellers=request.travellers,
        flight_preference=request.flight_preference,
        include_return_flight=request.include_return_flight,
        minimum_stars=request.minimum_stars,
        maximum_hotel_price=request.maximum_hotel_price,
        daily_local_expense=request.daily_local_expense,
        total_budget=request.total_budget,
        amenities=request.amenities,
        interests=request.interests,
        extra_requirements=request.extra_requirements,
    )
    try:
        trip_json = run_travel_agent_json(
            user_query,
            model_name=request.model_name,
            temperature=request.temperature,
            enabled_tool_names=request.enabled_tools,
        )
    except ValueError as configuration_error:
        raise HTTPException(status_code=400, detail=str(configuration_error))
    except Exception as unexpected_error:
        raise HTTPException(
            status_code=500,
            detail=f"Trip JSON could not be generated: {unexpected_error}",
        )
    return {"trip": trip_json}


@app.post("/api/chat")
def chat_with_ai(request: ChatRequest) -> dict:
    """Answer a travel question with the Groq model. No tools are used, so it is cheap."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is missing on the server.")

    if request.messages[-1].role != "user":
        raise HTTPException(status_code=400, detail="The last message must be from the user.")

    conversation = [SystemMessage(content=CHAT_SYSTEM_PROMPT)]
    for message in request.messages[-CHAT_HISTORY_LIMIT:]:
        if message.role == "user":
            conversation.append(HumanMessage(content=message.content))
        else:
            conversation.append(AIMessage(content=message.content))

    chat_model = ChatGroq(
        model=request.model_name,
        temperature=0.4,
        api_key=api_key,
        max_retries=2,
        max_tokens=400,
    )

    try:
        ai_response = chat_model.invoke(conversation)
    except Exception as chat_error:
        raise HTTPException(status_code=500, detail=f"Chat reply could not be generated: {chat_error}")

    return {"reply": ai_response.content}


app.mount("/static", StaticFiles(directory=FRONTEND_DIRECTORY), name="static")


@app.get("/")
def serve_frontend() -> FileResponse:
    """Serve the main HTML page."""
    return FileResponse(FRONTEND_DIRECTORY / "index.html")