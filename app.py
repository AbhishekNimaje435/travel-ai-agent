"""Streamlit app for the Agentic AI Travel Planning Assistant."""

import os
from datetime import date, timedelta

import streamlit as st
from dotenv import load_dotenv

from agent.travel_agent import DEFAULT_TEMPERATURE, GROQ_MODEL_NAME, run_travel_agent

load_dotenv()


def load_api_key_from_streamlit_secrets() -> None:
    """Copy GROQ_API_KEY from Streamlit secrets to environment variables (needed on Streamlit Cloud)."""
    try:
        if "GROQ_API_KEY" in st.secrets and not os.getenv("GROQ_API_KEY"):
            os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass


load_api_key_from_streamlit_secrets()

st.set_page_config(page_title="AI Travel Planner", page_icon="🧳", layout="centered")

CITY_OPTIONS = ["Delhi", "Mumbai", "Goa", "Bangalore", "Chennai", "Hyderabad", "Kolkata", "Jaipur"]
AMENITY_OPTIONS = ["wifi", "pool", "gym", "breakfast", "parking", "spa"]
INTEREST_OPTIONS = ["beach", "fort", "temple", "museum", "lake", "park", "market", "monument"]
FLIGHT_PREFERENCE_OPTIONS = ["Cheapest", "Fastest"]
TOOL_LABELS = {
    "search_flights": "🔍 Flight search (flights.json)",
    "search_hotels": "🏨 Hotel recommendations (hotels.json)",
    "search_places": "📍 Places discovery (places.json)",
    "get_weather_forecast": "⛅ Weather (Open-Meteo)",
    "estimate_trip_budget": "💼 Budget estimate",
}

st.title("🧳 AI Travel Planning Assistant")
st.caption("Flights, hotels, attractions, weather, and budget, planned by a LangChain agent powered by Groq.")

with st.sidebar:
    st.header("⚙️ Model settings")
    st.selectbox("LLM provider", ["Groq (free tier)"], disabled=True)
    st.text_input("Model", value=GROQ_MODEL_NAME, disabled=True)
    st.caption("API key is read from Streamlit Secrets, so it is not shown here.")
    temperature = st.slider(
        "Creativity (Temperature)", min_value=0.0, max_value=1.0, value=DEFAULT_TEMPERATURE, step=0.05
    )

    st.subheader("Agent tools")
    enabled_tool_names = [
        tool_name
        for tool_name, tool_label in TOOL_LABELS.items()
        if st.checkbox(tool_label, value=True, key=f"tool_{tool_name}")
    ]


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
    """Turn the form values into a natural language query for the agent."""
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

    query_lines.append(
        f"Hotel: at least {minimum_stars} stars, up to Rs {maximum_hotel_price} per night."
    )
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


with st.form("trip_form"):
    col_source, col_destination = st.columns(2)
    with col_source:
        source_city = st.selectbox("From", CITY_OPTIONS, index=CITY_OPTIONS.index("Hyderabad"))
    with col_destination:
        destination_city = st.selectbox("To", CITY_OPTIONS, index=CITY_OPTIONS.index("Goa"))

    col_start, col_end = st.columns(2)
    with col_start:
        start_date = st.date_input("Start date", value=date.today() + timedelta(days=7))
    with col_end:
        end_date = st.date_input("End date", value=date.today() + timedelta(days=9))

    col_travellers, col_flight = st.columns(2)
    with col_travellers:
        travellers = st.number_input("Number of travellers", min_value=1, max_value=10, value=1, step=1)
    with col_flight:
        flight_preference = st.selectbox("Flight preference", FLIGHT_PREFERENCE_OPTIONS, index=0)

    col_stars, col_hotel_price = st.columns(2)
    with col_stars:
        minimum_stars = st.slider("Minimum hotel stars", min_value=1, max_value=5, value=4)
    with col_hotel_price:
        maximum_hotel_price = st.number_input(
            "Max hotel price per night (Rs)", min_value=500, max_value=20000, value=7000, step=500
        )

    col_daily, col_total = st.columns(2)
    with col_daily:
        daily_local_expense = st.number_input(
            "Food & local travel (Rs/person/day)", min_value=0, max_value=10000, value=1500, step=100
        )
    with col_total:
        total_budget = st.number_input(
            "Total trip budget (Rs)", min_value=1000, max_value=500000, value=30000, step=1000
        )

    selected_amenities = st.multiselect("Hotel amenities", AMENITY_OPTIONS, default=["wifi"])
    selected_interests = st.multiselect("Interests", INTEREST_OPTIONS, default=["beach", "fort"])

    include_return_flight = st.checkbox("Include return flight", value=True)

    extra_requirements = st.text_area(
        "Anything else?",
        placeholder="For example: relaxed pace, prefer morning flights, vegetarian food",
    )

    submit_button = st.form_submit_button("🚀 Plan my trip")

if submit_button:
    if source_city == destination_city:
        st.error("Source and destination cities should be different.")
    elif end_date < start_date:
        st.error("End date start date se pehle nahi ho sakti.")
    elif not enabled_tool_names:
        st.error("Sidebar mein kam se kam ek tool enable karo.")
    else:
        user_query = build_user_query(
            source_city=source_city,
            destination_city=destination_city,
            start_date=start_date,
            end_date=end_date,
            travellers=int(travellers),
            flight_preference=flight_preference,
            include_return_flight=include_return_flight,
            minimum_stars=minimum_stars,
            maximum_hotel_price=int(maximum_hotel_price),
            daily_local_expense=int(daily_local_expense),
            total_budget=int(total_budget),
            amenities=selected_amenities,
            interests=selected_interests,
            extra_requirements=extra_requirements,
        )
        try:
            with st.spinner("Agent is searching flights, hotels, places, and weather..."):
                trip_plan = run_travel_agent(
                    user_query,
                    temperature=temperature,
                    enabled_tool_names=enabled_tool_names,
                )
            st.success("Your trip plan is ready!")
            st.markdown(trip_plan)
        except ValueError as configuration_error:
            st.error(f"Configuration error: {configuration_error}")
        except Exception as unexpected_error:
            st.error(
                "Trip plan generate nahi ho saka. Thodi der baad dobara try karo. "
                f"Details: {unexpected_error}"
            )