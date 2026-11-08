"""Creates the Business Impact Assessment as a PDF file."""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUTPUT_FILE = "Business_Impact_Assessment_Travel_Planner.pdf"


def build_styles():
    """Create paragraph styles for headings and body text."""
    base_styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("Title", parent=base_styles["Title"], fontSize=20, spaceAfter=10),
        "heading": ParagraphStyle("Heading", parent=base_styles["Heading2"], fontSize=14, spaceBefore=12, spaceAfter=6),
        "body": ParagraphStyle("Body", parent=base_styles["BodyText"], fontSize=10, leading=14, spaceAfter=6),
        "bullet": ParagraphStyle("Bullet", parent=base_styles["BodyText"], fontSize=10, leading=14, leftIndent=12, spaceAfter=3),
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

    story.append(Paragraph("Business Impact Assessment: AI Travel Planning Assistant", styles["title"]))
    story.append(Paragraph("How an AI travel planner can create value for travel companies and their customers.", styles["body"]))

    # 1. Problem and opportunity
    story.append(Paragraph("1. Problem and Opportunity", styles["heading"]))
    story.append(
        Paragraph(
            "Travellers usually switch between flight, hotel, and attraction websites, compare inconsistent information, "
            "and build itineraries by hand. Travel companies face high support costs for questions such as 'what should I "
            "do in Goa for 3 days on a budget?'. An AI travel planner can answer these questions in one place, with a "
            "structured plan and a budget breakdown.",
            styles["body"],
        )
    )

    # 2. Target users and companies
    story.append(Paragraph("2. Target Users and Companies", styles["heading"]))
    story.append(
        make_table(
            [
                ["Target", "Need", "How the product helps"],
                ["Individual travellers", "Quick, budget-friendly plans", "Single form gives flights, hotels, places, weather, and budget"],
                ["Online travel platforms (MakeMyTrip, ClearTrip, Ixigo)", "Self-service planning, lower support load", "Embedded planner that answers trip questions automatically"],
                ["Travel agencies", "Faster itinerary drafts for clients", "Day-wise itinerary and budget in seconds"],
                ["Hotels and resorts", "Better visibility and bookings", "Hotel recommendations filtered by stars, price, and amenities"],
            ]
        )
    )

    # 3. Value for customers
    story.append(Paragraph("3. Value for Customers", styles["heading"]))
    value_points = [
        "Time saving: one request replaces many website searches. A plan that normally takes 1 to 2 hours can be drafted in about a minute.",
        "Budget clarity: the plan shows flight, hotel, and local costs, and compares the total with the user's budget.",
        "Better decisions: the agent explains why each flight and hotel was selected, and flags over-budget totals.",
        "Free local browsing: hotels, places, and itinerary tabs work without any AI cost, so users can explore freely.",
        "Saved plans: users keep favorites and trip plans, and can export a JSON file for their own tools.",
    ]
    for point in value_points:
        story.append(Paragraph(f"- {point}", styles["bullet"]))

    # 4. Value for businesses
    story.append(Paragraph("4. Value for Businesses", styles["heading"]))
    story.append(
        make_table(
            [
                ["Benefit", "Description", "Example measure"],
                ["Lower support cost", "Common trip questions answered by the assistant and planner", "Share of support tickets on itinerary and budget questions"],
                ["Higher engagement", "Users spend more time on the platform exploring plans", "Session length and plan generations per user"],
                ["Better conversion", "Planner links users to hotels and flights they liked", "Click-through from plan to booking page"],
                ["Faster sales cycle", "Agencies produce draft itineraries quickly", "Time to first itinerary draft"],
                ["Data for product decisions", "Logs show which destinations and preferences are popular", "Most requested cities and interests"],
            ]
        )
    )

    # 5. Cost and operating model
    story.append(Paragraph("5. Cost and Operating Model", styles["heading"]))
    story.append(
        Paragraph(
            "The current prototype runs on free tiers: Groq free tier for the LLM, Open-Meteo for weather, and Render free "
            "hosting. For a production launch, the main recurring cost is LLM usage. The local tabs (hotels, places, "
            "itinerary) have no LLM cost, so most browsing can stay free, and only plan generation and chat use the model.",
            styles["body"],
        )
    )
    story.append(
        make_table(
            [
                ["Cost item", "Prototype", "Production estimate"],
                ["LLM (Groq or similar)", "Free tier (daily token limit)", "Pay per token, depends on plan requests per day"],
                ["Hosting", "Render free plan", "Paid web service for always-on use"],
                ["Weather API", "Open-Meteo (free, no key)", "Free for non-commercial use, check terms"],
                ["Data", "Sample JSON datasets", "Partner APIs or data licences"],
            ]
        )
    )

    # 6. Risks
    story.append(Paragraph("6. Risks and Mitigation", styles["heading"]))
    risks = [
        "Inaccurate data: sample datasets can show wrong prices or schedules. Mitigation: show a clear note on each result, and connect real data sources before launch.",
        "LLM cost overrun: heavy use can exceed the budget. Mitigation: local tabs for browsing, token-limited tool outputs, and rate limits per user.",
        "Over-reliance on AI answers: users may trust the plan without checking. Mitigation: disclaimers and a link to official booking pages.",
        "Privacy: trip details can be sensitive. Mitigation: data stored in the browser only in this prototype, and no personal data sent to the LLM beyond the trip query.",
        "Service availability: the free hosting plan sleeps when idle. Mitigation: move to a paid plan for production use.",
    ]
    for risk in risks:
        story.append(Paragraph(f"- {risk}", styles["bullet"]))

    # 7. Success metrics
    story.append(Paragraph("7. Success Metrics", styles["heading"]))
    story.append(
        make_table(
            [
                ["Metric", "Target (pilot)", "How to measure"],
                ["Plan completion rate", "Above 70% of started plans", "Plans generated divided by form submissions"],
                ["Time to first plan", "Under 60 seconds (LLM plans)", "Measured from submit to result"],
                ["Plan accuracy", "Above 90% of checked fields correct", "Agent performance report test results"],
                ["Saved trips per user", "At least 1 per returning user", "Saved trips in storage analytics"],
                ["Support ticket reduction", "10% to 20% for planning questions", "Compare before and after launch"],
            ]
        )
    )

    # 8. Next steps
    story.append(Paragraph("8. Recommended Next Steps", styles["heading"]))
    next_steps = [
        "Run a pilot with 20 to 30 real users and collect feedback on plan quality.",
        "Connect a real hotel and flight data source through a partner API.",
        "Add user accounts so saved trips sync across devices.",
        "Measure LLM cost per plan and set a monthly budget.",
        "Prepare a short demo video for portfolio and investor discussions.",
    ]
    for step in next_steps:
        story.append(Paragraph(f"- {step}", styles["bullet"]))

    return story


def create_pdf(output_path: str = OUTPUT_FILE) -> None:
    """Build the business impact assessment PDF at the given path."""
    document = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Business Impact Assessment: AI Travel Planning Assistant",
    )
    document.build(build_story(build_styles()))
    print(f"PDF created: {output_path}")


if __name__ == "__main__":
    create_pdf()