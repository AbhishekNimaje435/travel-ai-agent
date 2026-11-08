# ✈️ AI Travel Planner

An agentic AI travel planner built with **LangChain**, **Groq (LLM)**, **FastAPI**, and a custom **HTML/CSS/JavaScript** frontend. Describe your trip in plain terms, and the AI agent decides which tools to call (flights, hotels, attractions, weather, and budget) to build a complete, budget-aware travel plan. Browse hotels, attractions, and day-wise itineraries instantly, save favourites, keep your trip plans, and chat with a travel assistant.

🔗 **Live demo:** [https://travel-ai-agent-3llr.onrender.com]

> The free hosting plan sleeps after inactivity. The first load can take 30 to 60 seconds.

---

| Home and trip planner | Trip plan result |
|---|---|
| ![Home](docs/screenshots/home.png) | ![Result](docs/screenshots/result.png) |

> Add your screenshots in a `docs/screenshots/` folder and update the paths above.

---

## 🎯 Problem Statement

Planning a trip means switching between flight, hotel, and attraction websites, comparing inconsistent information, and building an itinerary by hand. Most of that time goes into searching, not deciding.

This project automates the workflow. A single request produces a structured plan with a selected flight, a hotel recommendation, a day-wise itinerary, a weather forecast, and a budget breakdown, all grounded in tool data rather than invented by the model.

## 💼 Business Use Cases

- **Self-service trip planning** for travel websites and apps (similar to MakeMyTrip, ClearTrip, or Ixigo)
- **Faster itinerary drafts** for travel agencies
- **Budget-focused recommendations** for price-sensitive travellers
- **Lower customer support load** by answering common planning questions automatically

---

## ✨ Features

### 🤖 AI Trip Planner (Groq LLM agent)
- Natural language trip requests with dates, travellers, budget, star rating, amenities, and interests
- Tool-calling agent that chooses between 5 tools and runs them in a loop
- Cheapest or fastest flight preference, with optional return flight
- Budget check against the user's total budget, with a clear over-budget warning
- Extra requirements (for example: vegetarian food, relaxed pace) are passed to the agent
- Temperature and tool toggles available in the backend

### 🛏️ Hotels (local data, no LLM call)
- Filter by city, minimum stars, and maximum price per night
- Sort by stars, or by price (low to high or high to low)
- Save any hotel to favourites with ♡

### 📍 Places (local data, no LLM call)
- Filter by city, attraction type, and minimum rating
- Sort by rating or name
- Save any place to favourites with ♡

### 📋 Itinerary (local planner, no LLM call)
- Builds a day-wise plan from places and hotels data
- Choose number of days, places per day, minimum rating, and interests
- Never repeats a place across days
- Budget card with flight, hotel, and local expense totals

### 💾 Favourites and My Trips (browser storage)
- Save hotels and places to **Favorites**
- Save a generated AI plan to **My Trips**, view it later, or delete it
- Data is stored in the browser's `localStorage`, so no account is needed

### 💬 Chat with AI
- Floating travel assistant in the sidebar
- Answers travel questions briefly (destinations, packing, planning tips)
- Keeps the last few messages as context

---

## 🧠 How the AI Agent Works

```
User request (form)
      │
      ▼
FastAPI  POST /api/plan
      │
      ▼
Groq LLM (openai/gpt-oss-20b) ──► decides which tool to call
      │                                  │
      │   ◄──── tool result (JSON) ──────┤
      │                                  │
      ▼                                  │
Repeat until the final answer           │
      │                                  │
      ▼                                  │
Structured trip plan (Markdown) ◄────────┘
```

**Tools available to the agent:**

| Tool | Data source | What it does |
|---|---|---|
| `search_flights` | `flights.json` | Finds one-way flights, cheapest and fastest options, with an optional travel date |
| `search_hotels` | `hotels.json` | Filters hotels by city, stars, and price, and ranks them |
| `search_places` | `places.json` | Finds attractions by city, type, and rating |
| `get_weather_forecast` | Open-Meteo API (free, no key) | Daily max and min temperature, rain probability, and conditions |
| `estimate_trip_budget` | Calculation | Adds flight, hotel, and daily local expenses into a total |

The agent is limited to a fixed number of tool rounds, and each tool output is shortened before it goes back to the model, which keeps token usage low.

---

## 🏗️ Project Structure

```
travel_ai_agent/
├── agent/
│   ├── travel_agent.py       # Groq LLM agent with the tool-calling loop
│   └── query_builder.py      # Turns form values into the agent's query
├── tools/
│   ├── flight_tool.py        # Flight search
│   ├── hotel_tool.py         # Hotel recommendation
│   ├── places_tool.py        # Attraction discovery
│   ├── weather_tool.py       # Open-Meteo weather forecast
│   └── budget_tool.py        # Trip budget calculation
├── data/
│   ├── flights.json
│   ├── hotels.json
│   └── places.json
├── frontend/
│   ├── index.html            # Page layout (all pages and panels)
│   ├── style.css             # Styling and animations
│   ├── script.js             # Navigation, search, hotels, places, itinerary
│   ├── storage.js            # Favourites and saved trips (localStorage)
│   └── chat.js               # Chat with AI panel
├── api.py                    # FastAPI backend and API routes
├── app.py                    # Earlier Streamlit version (kept for reference)
├── requirements.txt
├── runtime.txt               # Python version for deployment
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint | Uses Groq | Purpose |
|---|---|---|---|
| GET | `/api/health` | No | Health check |
| POST | `/api/plan` | Yes | Run the AI trip planner agent |
| POST | `/api/chat` | Yes | Chat with the travel assistant |
| GET | `/api/cities` | No | Cities list for the hotels tab and itinerary |
| GET | `/api/hotels` | No | Filtered hotel search |
| GET | `/api/place-options` | No | Cities and attraction types for filters |
| GET | `/api/places` | No | Filtered place search |
| GET | `/api/itinerary` | No | Local day-wise itinerary and budget |

Interactive API docs are available at `/docs` when the server is running.

---

## 🛠️ Tech Stack

- **Language:** Python 3.12, JavaScript (ES6), HTML5, CSS3
- **AI agent:** LangChain Core, LangChain Groq
- **LLM:** Groq API with `openai/gpt-oss-20b` (free tier)
- **Backend:** FastAPI, Uvicorn, Pydantic
- **Frontend:** Vanilla HTML, CSS, and JavaScript, with `marked` and `DOMPurify` from a CDN
- **Weather:** Open-Meteo API (no key required)
- **Storage:** Browser `localStorage` for favourites and saved trips
- **Deployment:** Render (free web service), code from GitHub

---

## ⚙️ Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/AbhishekNimaje435/travel-ai-agent.git
cd travel-ai-agent
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Groq API key

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free key from [console.groq.com](https://console.groq.com). Never commit `.env` to GitHub. It is already listed in `.gitignore`.

### 5. Run the server

```bash
python -m uvicorn api:app --reload
```

Open **http://127.0.0.1:8000** in your browser.

---

## ☁️ Deployment (Render)

1. Push the code to GitHub.
2. On [render.com](https://render.com), create a **New Web Service** from the repository.
3. Use these settings:

| Field | Value |
|---|---|
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn api:app --host 0.0.0.0 --port $PORT` |
| Instance Type | Free |

4. Add an environment variable: `GROQ_API_KEY` with your key.
5. Deploy. Future pushes to `main` redeploy automatically.

---

## 📊 Evaluation and Testing

- **Tool outputs:** Each tool was tested with real queries (for example, Hyderabad to Goa flights, Goa hotels with 4+ stars under ₹5000, Kolkata places with 4.0+ rating). Results were checked against the JSON data.
- **Budget calculation:** Checked manually for a 3-day Goa trip (flight ₹2,907, 2 nights × ₹1,232, 3 days × ₹1,500 = ₹9,871).
- **Agent behaviour:** Tested with several queries. Issues found and fixed included repeated tool calls, invented activities, a past date being used for a future trip, and places repeating across days.
- **Frontend:** Tested all tabs, the sidebar pages, favourites, saved trips, and the chat panel on local and live URLs.

---

## ⚠️ Limitations

- **Sample data:** `flights.json`, `hotels.json`, and `places.json` are sample datasets. Some records look synthetic (attraction names and types do not always match, and some flight durations are unrealistic).
- **Flight dates:** Dataset flights are from 2025. For future dates, the agent uses the same schedule (departure time and duration) on the requested date. Real booking times may differ.
- **No live prices or bookings:** Prices and availability come from the sample data. The app does not book anything.
- **Weather range:** Forecasts are reliable for roughly the next 16 days only.
- **Fixed costs:** Daily food and local travel costs use a default estimate (₹1,500 per person per day), unless the user changes it.
- **Free-tier limits:** The Groq free tier has token-per-minute and daily limits, so heavy use may need a short wait.
- **Free hosting:** Render's free plan sleeps after inactivity, so the first request can be slow.
- **Browser-only storage:** Favourites and saved trips are stored per browser. They do not sync across devices.

---

## 🔮 Future Scope

- User accounts and cloud database for saved trips and favourites
- Live flight and hotel data through APIs
- Multi-city and round-trip itineraries
- Downloadable PDF itinerary
- Hindi and Hinglish responses
- Agent evaluation dashboard with MLflow or LangSmith
- Model comparison (for example, `gpt-oss-120b` versus `gpt-oss-20b`) for quality and cost

---

## 👤 Author

**Abhishek Nimaje**
GitHub: [@AbhishekNimaje435](https://github.com/AbhishekNimaje435)

---

## 📄 License

This project is for learning and portfolio purposes.
