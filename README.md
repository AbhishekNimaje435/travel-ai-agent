# AI Travel Planning Assistant

An agentic AI travel planner built with **LangChain**, **Groq (LLM)**, and **Streamlit**. The agent takes a natural language trip request, decides which tools to call, and returns a complete plan with flight, hotel, attractions, weather forecast, and budget estimate.

## Problem Statement

Planning a trip means switching between flight, hotel, and attraction websites, comparing inconsistent information, and building an itinerary by hand. This project automates that workflow with an AI agent that uses real tools and data to create a structured, budget-aware plan.

## Business Use Cases

- Self-service trip planning for travel websites and apps (MakeMyTrip, ClearTrip, Ixigo style)
- Quick itinerary drafts for travel agencies
- Budget-focused recommendations for travelers
- Reduced customer support workload through automated answers

## Features

- Natural language trip requests (source, destination, dates, hotel stars, budget)
- Flight search with cheapest and fastest options
- Hotel recommendation filtered by stars and price per night
- Attraction discovery filtered by type and rating
- Live weather forecast using the free Open-Meteo API (no API key needed)
- Budget estimate combining flight, hotel, and daily expenses
- Streamlit web interface

## Project Structure

```
travel_ai_agent/
├── agent/
│   └── travel_agent.py      # Groq LLM agent with tool-calling loop
├── tools/
│   ├── flight_tool.py       # Flight search (flights.json)
│   ├── hotel_tool.py        # Hotel recommendation (hotels.json)
│   ├── places_tool.py       # Attraction discovery (places.json)
│   ├── weather_tool.py      # Weather forecast (Open-Meteo API)
│   └── budget_tool.py       # Trip budget estimation
├── data/
│   ├── flights.json
│   ├── hotels.json
│   └── places.json
├── app.py                   # Streamlit app
├── requirements.txt
└── README.md
```

## Setup Instructions

**1. Clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/travel-ai-agent.git
cd travel-ai-agent
```

**2. Create and activate a virtual environment**

```bash
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Add your Groq API key**

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free key from https://console.groq.com.

**5. Run the Streamlit app**

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Tech Stack

- Python 3.12
- LangChain and LangChain Core (tool definitions)
- Groq API with `openai/gpt-oss-20b` (LLM)
- Streamlit (UI)
- Open-Meteo (weather API)
- Requests and python-dotenv

## Limitations

- The datasets (`flights.json`, `hotels.json`, `places.json`) are sample data. Some records look synthetic, for example attraction names and types do not always match, and flight durations can be unrealistic.
- Flight dates in the dataset are from 2025. For future travel dates, the agent uses the same flight schedule (departure time and duration) on the requested date. Real booking times may differ.
- Weather forecasts are available only for roughly the next 16 days.
- Hotel and flight prices are from the dataset, not live prices.
- Daily food and local travel costs are a fixed default estimate (₹1500 per day).
- Groq free tier has token-per-minute limits, so repeated requests may need a short wait.

## Future Scope

- Live flight and hotel data through APIs
- Multi-city trips
- Downloadable PDF itinerary
- Hindi and Hinglish responses
- Agent evaluation dashboard with MLflow or LangSmith

## Author

Abhishek Nimaje