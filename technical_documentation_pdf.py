"""Creates the Technical Documentation as a PDF file."""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Table, TableStyle

OUTPUT_FILE = "Technical_Documentation_Travel_Planner.pdf"


def build_styles():
    """Create paragraph styles for headings, body text, and code blocks."""
    base_styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("Title", parent=base_styles["Title"], fontSize=20, spaceAfter=10),
        "heading": ParagraphStyle("Heading", parent=base_styles["Heading2"], fontSize=14, spaceBefore=12, spaceAfter=6),
        "subheading": ParagraphStyle("Subheading", parent=base_styles["Heading3"], fontSize=11, spaceBefore=8, spaceAfter=4),
        "body": ParagraphStyle("Body", parent=base_styles["BodyText"], fontSize=10, leading=14, spaceAfter=6),
        "bullet": ParagraphStyle("Bullet", parent=base_styles["BodyText"], fontSize=10, leading=14, leftIndent=12, spaceAfter=3),
        "code": ParagraphStyle("Code", parent=base_styles["Code"], fontSize=8, leading=10, backColor=colors.HexColor("#f2f5fb")),
    }


def make_table(rows):
    """Create a styled table from rows. The first row is the header."""
    table = Table(rows, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3a7bd5")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b0b8d0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5fb")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def build_story(styles):
    """Build the list of document elements in order."""
    story = []

    story.append(Paragraph("Technical Documentation: AI Travel Planning Assistant", styles["title"]))
    story.append(Paragraph("Agentic AI capstone project using LangChain, Groq, FastAPI, and a custom frontend.", styles["body"]))

    # 1. Overview
    story.append(Paragraph("1. Project Overview", styles["heading"]))
    story.append(
        Paragraph(
            "The system plans a trip from a natural language or form request. An LLM agent decides which tools to call "
            "(flights, hotels, places, weather, and budget), collects real data from local datasets and a free weather API, "
            "and returns a structured plan. Local tabs (Hotels, Places, Itinerary) work without the LLM, so they are fast and free.",
            styles["body"],
        )
    )

    # 2. Architecture
    story.append(Paragraph("2. System Architecture", styles["heading"]))
    story.append(
        Preformatted(
            "Browser (HTML, CSS, JavaScript)\n"
            "   |\n"
            "   |  fetch() calls\n"
            "   v\n"
            "FastAPI backend (api.py)\n"
            "   |-- /api/plan, /api/plan/json  --> Agent (agent/travel_agent.py)\n"
            "   |                                    |-- Groq LLM (openai/gpt-oss-20b)\n"
            "   |                                    |-- Tools (tools/*.py)\n"
            "   |                                          |-- flights.json\n"
            "   |                                          |-- hotels.json\n"
            "   |                                          |-- places.json\n"
            "   |                                          |-- Open-Meteo API\n"
            "   |-- /api/hotels, /api/places, /api/itinerary  --> local data only\n"
            "   |-- /api/chat  --> Groq LLM (no tools)\n"
            "   v\n"
            "Browser localStorage (favorites, saved trips)",
            styles["code"],
        )
    )

    # 3. Components
    story.append(Paragraph("3. Components", styles["heading"]))
    story.append(
        make_table(
            [
                ["Layer", "File(s)", "Responsibility"],
                ["Backend API", "api.py", "Routes, request validation (Pydantic), error handling"],
                ["Agent", "agent/travel_agent.py", "Groq LLM, tool-calling loop, system prompt, JSON mode"],
                ["Query builder", "agent/query_builder.py", "Turns form values into a natural language query"],
                ["Tools", "tools/*.py", "Flight, hotel, places, weather, and budget functions"],
                ["Data", "data/*.json", "Sample flights, hotels, and places datasets"],
                ["Frontend", "frontend/index.html, style.css, script.js", "Pages, forms, results, and local tabs"],
                ["Storage", "frontend/storage.js", "Favorites and saved trips in localStorage"],
                ["Chat", "frontend/chat.js", "Chat panel that calls /api/chat"],
                ["Deployment", "requirements.txt, runtime.txt", "Python packages and version for Render"],
            ]
        )
    )

    # 4. Tools
    story.append(Paragraph("4. Agent Tools", styles["heading"]))
    story.append(
        make_table(
            [
                ["Tool", "Input", "Output", "Data source"],
                ["search_flights", "source, destination, travel date", "Matching flights, cheapest and fastest", "flights.json"],
                ["search_hotels", "city, min stars, max price", "Ranked hotels, top recommendation", "hotels.json"],
                ["search_places", "city, type, min rating", "Ranked places, top 3", "places.json"],
                ["get_weather_forecast", "city, start date, end date", "Daily max/min temperature, rain %, condition", "Open-Meteo API"],
                ["estimate_trip_budget", "flight price, hotel price, days, daily expense", "Flight, hotel, local, and total cost", "Calculation"],
            ]
        )
    )
    story.append(Paragraph("Each tool returns plain dictionaries. The agent receives them as JSON, and list outputs are shortened to 5 items to save tokens.", styles["body"]))

    # 5. Agent flow
    story.append(Paragraph("5. Agent Flow", styles["heading"]))
    flow_steps = [
        "The user submits the form (cities, dates, travellers, budget, preferences).",
        "The query builder converts the form values into a natural language query.",
        "The agent sends the system prompt and query to the Groq LLM, with the enabled tools attached.",
        "If the LLM asks for tools, the agent runs them, adds the results as tool messages, and calls the LLM again.",
        "This loop runs for up to 12 rounds. When the LLM answers without tool calls, the answer is returned.",
        "For /api/plan/json, the final answer is parsed as JSON. If parsing fails, the agent retries once.",
    ]
    for index, step in enumerate(flow_steps, start=1):
        story.append(Paragraph(f"{index}. {step}", styles["bullet"]))

    # 6. Prompt design
    story.append(Paragraph("6. Prompt Design", styles["heading"]))
    story.append(
        Paragraph(
            "The system prompt is built in build_system_prompt(). It is generated per request, with today's date and only "
            "the enabled tools. It contains two rule groups:",
            styles["body"],
        )
    )
    story.append(Paragraph("<b>Tool usage rules:</b> call each tool once, stop when data is enough, use travel_date, pick cheapest or fastest flight by preference, and call search_places only once.", styles["bullet"]))
    story.append(Paragraph("<b>Answer rules:</b> use only tool data, no invented places or prices, correct travellers and room math, budget comparison, one-way flight note, amenity filter, closest alternatives when no exact match, and a fallback message when interests have too few places.", styles["bullet"]))
    story.append(Paragraph("For JSON output, a fixed JSON schema is appended to the prompt, and the answer is validated with json.loads().", styles["body"]))

    # 7. Key decisions
    story.append(Paragraph("7. Key Design Decisions", styles["heading"]))
    decisions = [
        "Local tools for hotels, places, and itinerary tabs, so the Groq limit is not used for browsing.",
        "Shortened tool outputs (5 items per list) to reduce tokens per request.",
        "Temperature set to 0.2 for consistent answers.",
        "Budget math done in a tool, not by the LLM, to avoid calculation errors.",
        "Browser storage for favorites and saved trips, so no database is needed for the demo.",
        "Fallback messages (closest hotels, non-matching interests) instead of empty results.",
    ]
    for decision in decisions:
        story.append(Paragraph(f"- {decision}", styles["bullet"]))

    # 8. API endpoints
    story.append(Paragraph("8. API Endpoints", styles["heading"]))
    story.append(
        make_table(
            [
                ["Method", "Endpoint", "Uses Groq", "Purpose"],
                ["GET", "/api/health", "No", "Health check"],
                ["POST", "/api/plan", "Yes", "Agent trip plan (Markdown text)"],
                ["POST", "/api/plan/json", "Yes", "Agent trip plan (structured JSON)"],
                ["POST", "/api/chat", "Yes", "Travel assistant chat (no tools)"],
                ["GET", "/api/cities", "No", "Cities list from hotels.json"],
                ["GET", "/api/hotels", "No", "Filtered hotel search"],
                ["GET", "/api/place-options", "No", "Cities and types for filters"],
                ["GET", "/api/places", "No", "Filtered place search"],
                ["GET", "/api/itinerary", "No", "Local day-wise itinerary and budget"],
            ]
        )
    )

    # 9. Deployment
    story.append(Paragraph("9. Deployment", styles["heading"]))
    deployment_steps = [
        "Code is hosted on GitHub. Every push to main triggers a redeploy on Render (free web service).",
        "Start command: uvicorn api:app --host 0.0.0.0 --port $PORT",
        "Python version pinned in runtime.txt. Packages listed in requirements.txt.",
        "GROQ_API_KEY is stored as a Render environment variable, never in the repository.",
        "The free plan sleeps after inactivity, so the first request can take 30 to 60 seconds.",
    ]
    for step in deployment_steps:
        story.append(Paragraph(f"- {step}", styles["bullet"]))

    # 10. Limitations
    story.append(Paragraph("10. Limitations", styles["heading"]))
    limitations = [
        "Sample datasets, not live prices or availability.",
        "Flight dates from 2025 are shown on the requested date using the dataset schedule (documented in the response).",
        "Weather forecasts are reliable for about 16 days only.",
        "Groq free tier has token-per-minute and token-per-day limits, which restrict heavy testing.",
        "Browser storage is per browser; favorites and trips do not sync across devices.",
    ]
    for limitation in limitations:
        story.append(Paragraph(f"- {limitation}", styles["bullet"]))

    # 11. Future work
    story.append(Paragraph("11. Future Work", styles["heading"]))
    future_work = [
        "Replace sample data with live APIs or scraped data.",
        "Add user accounts and a database (SQLite or PostgreSQL) for trips and favorites.",
        "Add automated tests (pytest) and code style checks (flake8).",
        "Add LLM evaluation tracking with MLflow or LangSmith.",
    ]
    for item in future_work:
        story.append(Paragraph(f"- {item}", styles["bullet"]))

    return story


def create_pdf(output_path: str = OUTPUT_FILE) -> None:
    """Build the technical documentation PDF at the given path."""
    document = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Technical Documentation: AI Travel Planning Assistant",
    )
    document.build(build_story(build_styles()))
    print(f"PDF created: {output_path}")


if __name__ == "__main__":
    create_pdf()