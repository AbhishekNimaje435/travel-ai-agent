"""Streamlit app for the Agentic AI Travel Planning Assistant."""

from datetime import date, timedelta

import streamlit as st

from agent.travel_agent import run_travel_agent

st.set_page_config(page_title="AI Travel Planner", page_icon="🧳", layout="centered")

st.title("🧳 AI Travel Planning Assistant")
st.caption("Flights, hotels, attractions, weather, and budget, planned by a LangChain agent powered by Groq.")

CITY_OPTIONS = ["Delhi", "Mumbai", "Goa", "Bangalore", "Chennai", "Hyderabad", "Kolkata", "Jaipur"]


def build_user_query(
    source_city: str,
    destination_city: str,
    start_date: date,
    end_date: date,
    minimum_stars: int,
    maximum_budget: int,
) -> str:
    """Turn the form values into a natural language query for the agent."""
    trip_days = (end_date - start_date).days + 1
    return (
        f"Plan a {trip_days}-day trip from {source_city} to {destination_city}. "
        f"Travel dates: {start_date.isoformat()} to {end_date.isoformat()}. "
        f"Hotel must be at least {minimum_stars} stars. "
        f"Hotel price should be within Rs {maximum_budget} per night if possible. "
        f"Keep the overall budget low."
    )


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

    col_stars, col_budget = st.columns(2)
    with col_stars:
        minimum_stars = st.slider("Minimum hotel stars", min_value=1, max_value=5, value=4)
    with col_budget:
        maximum_budget = st.number_input(
            "Max hotel price per night (Rs)", min_value=500, max_value=20000, value=5000, step=500
        )

    submit_button = st.form_submit_button("Plan my trip")

if submit_button:
    if source_city == destination_city:
        st.error("Source and destination cities should be different.")
    elif end_date < start_date:
        st.error("End date start date se pehle nahi ho sakti.")
    else:
        user_query = build_user_query(
            source_city, destination_city, start_date, end_date, minimum_stars, maximum_budget
        )
        try:
            with st.spinner("Agent is searching flights, hotels, places, and weather..."):
                trip_plan = run_travel_agent(user_query)
            st.success("Your trip plan is ready!")
            st.markdown(trip_plan)
        except ValueError as configuration_error:
            st.error(f"Configuration error: {configuration_error}")
        except Exception as unexpected_error:
            st.error(
                "Trip plan generate nahi ho saka. Thodi der baad dobara try karo. "
                f"Details: {unexpected_error}"
            )