"""Creates the Capstone Demo Script and Viva Preparation as a PDF file."""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUTPUT_FILE = "Capstone_Demo_and_Viva_Travel_Planner.pdf"
LIVE_URL = "https://travel-ai-agent-3llr.onrender.com"


def build_styles():
    """Create paragraph styles for headings and body text."""
    base_styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("Title", parent=base_styles["Title"], fontSize=20, spaceAfter=10),
        "heading": ParagraphStyle("Heading", parent=base_styles["Heading2"], fontSize=14, spaceBefore=12, spaceAfter=6),
        "subheading": ParagraphStyle(
            "Subheading", parent=base_styles["Heading3"], fontSize=11, spaceBefore=8, spaceAfter=4
        ),
        "body": ParagraphStyle("Body", parent=base_styles["BodyText"], fontSize=10, leading=14, spaceAfter=6),
        "bullet": ParagraphStyle(
            "Bullet", parent=base_styles["BodyText"], fontSize=10, leading=14, leftIndent=12, spaceAfter=3
        ),
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
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def demo_script_rows():
    """Return the time-wise demo script as table rows."""
    return [
        ["Time", "What to show", "What to say"],
        [
            "0:00 to 0:30",
            f"Open the live URL: {LIVE_URL}",
            "This is an AI travel planner built with LangChain, Groq, FastAPI, and a custom frontend. It is live on Render.",
        ],
        [
            "0:30 to 1:00",
            "Home page: hero, destination cards, Your Trip Planner card",
            "The home page lets users start from a popular city. Clicking a city opens the planner with that destination.",
        ],
        [
            "1:00 to 2:00",
            "Plan Trip: set From, To, dates. Open Advanced preferences. Click Plan my trip.",
            "The AI agent uses 5 tools: flights, hotels, places, weather, and budget. It decides which tools to call, based on the request.",
        ],
        [
            "2:00 to 2:30",
            "Show the Markdown result: flight, hotel, weather, itinerary, budget",
            "Every value comes from the tools, not from the model. The budget is calculated by a tool, so the math is reliable.",
        ],
        [
            "2:30 to 3:00",
            "Click Download JSON. Open the file.",
            "The same plan is available as structured JSON, which other systems can use.",
        ],
        [
            "3:00 to 3:30",
            "Itinerary tab: Goa, 3 days, Build itinerary",
            "This tab uses local data only, so it does not use the LLM. It shows the day-wise plan and budget instantly.",
        ],
        [
            "3:30 to 4:00",
            "Hotels tab (filter by stars) and Places tab (filter by type)",
            "Browsing is free and fast, because it uses our datasets directly.",
        ],
        [
            "4:00 to 4:30",
            "Favorites (click heart) and My Trips (Save trip)",
            "Users can save favorites and trips. These are stored in the browser, so no login is needed.",
        ],
        [
            "4:30 to 5:00",
            "Chat with AI button: ask one travel question. Then show the Reports folder.",
            "The chat assistant answers general questions. The project also has EDA, technical, business, and agent evaluation reports.",
        ],
    ]


def viva_questions():
    """Return the viva questions with short answers."""
    return [
        (
            "What problem does this project solve?",
            "Travellers spend a lot of time switching between flight, hotel, and attraction websites. The planner builds a complete, budget-aware plan from one request.",
        ),
        (
            "Why did you use an agent and not a single LLM prompt?",
            "A single prompt cannot access live or structured data. The agent calls tools to get real data (flights, hotels, places, weather), so the answer is grounded.",
        ),
        (
            "How does the agent decide which tool to call?",
            "The LLM reads the system prompt and the tool descriptions. It returns tool calls in its response, and the agent code runs them. This repeats until the LLM gives a final answer.",
        ),
        (
            "Why did you choose Groq and openai/gpt-oss-20b?",
            "Groq is fast and has a free tier. The 20b model supports tool calling and is cheaper to run than the 120b model, which hit the rate limit faster during testing.",
        ),
        (
            "What is the role of temperature?",
            "Temperature controls randomness. We used 0.2 so answers are consistent for the same request.",
        ),
        (
            "How do you prevent hallucinations?",
            "The prompt says to use only tool data. Budget math is done by a tool, not by the model. We also check the results with an evaluation script.",
        ),
        (
            "How did you evaluate the agent?",
            "We wrote 12 test queries and checked JSON validity, required sections, itinerary completeness, budget limit, and budget math. Results are in the Agent Performance Report.",
        ),
        (
            "What were the main problems you faced?",
            "Tool-calling loops repeated the same tool, the itinerary had empty days when interests had few matches, and the free-tier token limit slowed testing. We fixed these with prompt rules, a fallback in the itinerary, and shorter tool outputs.",
        ),
        (
            "Why are the datasets sample data?",
            "The project is a prototype. Real flight and hotel APIs need partner access or paid plans. We documented the limitations clearly, including unrealistic durations and synthetic names.",
        ),
        (
            "Why is the Itinerary tab separate from the agent?",
            "The Itinerary tab uses local data only, so it is fast and free. The agent is used when the user needs a full plan with reasoning and live weather.",
        ),
        (
            "Why did you not use a database?",
            "The data is small and read-only, so JSON files are enough. Favorites and trips use browser storage for the demo. A database is listed as future work.",
        ),
        (
            "Why FastAPI and not Flask or Django?",
            "FastAPI is fast, uses type hints and Pydantic for validation, and generates API docs automatically at /docs.",
        ),
        (
            "How is the project deployed?",
            "Code is on GitHub. Render builds it from requirements.txt and runs uvicorn with the port from the environment. The Groq key is stored as an environment variable.",
        ),
        (
            "What are the security concerns?",
            "The API key is not in the code. User input is validated with Pydantic. Chat and plan responses are sanitized before showing them in the browser.",
        ),
        (
            "What would you improve next?",
            "Real data sources, user accounts with a database, automated tests with pytest, and cost tracking for LLM calls.",
        ),
        (
            "What is the business value?",
            "Lower support load for travel platforms, faster itinerary drafts for agencies, and clear budget comparisons for customers.",
        ),
    ]


def build_story(styles):
    """Build the list of document elements in order."""
    story = []

    story.append(Paragraph("Capstone Demo Script and Viva Preparation", styles["title"]))
    story.append(Paragraph(f"Live URL: {LIVE_URL}", styles["body"]))
    story.append(
        Paragraph(
            "Total demo time: about 5 minutes. Keep to the times shown, and leave 1 to 2 minutes for questions.",
            styles["body"],
        )
    )

    # Part 1: Demo script
    story.append(Paragraph("Part 1: Live Demo Script (5 minutes)", styles["heading"]))
    story.append(make_table(demo_script_rows()))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Before the demo:</b>", styles["body"]))
    before_demo = [
        "Open the live URL 2 minutes early, so the Render free instance is awake.",
        "Check that Groq is not rate limited (one Plan my trip call should work).",
        "Keep a backup screenshot of the Plan result and the JSON file, in case the live site is slow.",
        "Have the GitHub repo open in another tab, to show the code structure if asked.",
    ]
    for item in before_demo:
        story.append(Paragraph(f"- {item}", styles["bullet"]))

    # Part 2: Viva
    story.append(Paragraph("Part 2: Viva Questions and Answers", styles["heading"]))
    story.append(Paragraph("Short answers you can say in 20 to 30 seconds each.", styles["body"]))
    for index, (question, answer) in enumerate(viva_questions(), start=1):
        story.append(Paragraph(f"<b>Q{index}. {question}</b>", styles["subheading"]))
        story.append(Paragraph(answer, styles["body"]))

    # Part 3: Tips
    story.append(Paragraph("Part 3: Tips for the Presentation", styles["heading"]))
    tips = [
        "If a question is unclear, repeat it in your own words before answering.",
        "If you do not know an answer, say so, then explain how you would find out.",
        "Point to the project files when asked about implementation (api.py, agent/travel_agent.py, tools/).",
        "Mention the limitations yourself before the teacher asks. It shows honesty and understanding.",
        "Keep answers short. Offer to show the code or the test results if the teacher wants more detail.",
    ]
    for tip in tips:
        story.append(Paragraph(f"- {tip}", styles["bullet"]))

    return story


def create_pdf(output_path: str = OUTPUT_FILE) -> None:
    """Build the capstone demo and viva PDF at the given path."""
    document = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Capstone Demo Script and Viva Preparation",
    )
    document.build(build_story(build_styles()))
    print(f"PDF created: {output_path}")


if __name__ == "__main__":
    create_pdf()
