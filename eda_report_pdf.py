"""Creates the EDA report as a PDF file."""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUTPUT_FILE = "EDA_Report_Travel_Planner.pdf"


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
    """Create a styled table from a list of rows. The first row is the header."""
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
    """Build the list of report elements in order."""
    story = []

    story.append(Paragraph("EDA Report: Travel Planning Datasets", styles["title"]))
    story.append(Paragraph("AI Travel Planning Assistant, Agentic AI Capstone", styles["body"]))
    story.append(Spacer(1, 6))

    # 1. Overview
    story.append(Paragraph("1. Dataset Overview", styles["heading"]))
    story.append(
        Paragraph(
            "The project uses three JSON datasets stored in the data/ folder. Together they cover 8 Indian cities: "
            "Delhi, Mumbai, Goa, Bangalore, Chennai, Hyderabad, Kolkata, and Jaipur.",
            styles["body"],
        )
    )
    story.append(
        make_table(
            [
                ["Dataset", "Records", "Columns", "Purpose"],
                ["flights.json", "30", "7", "Flight search, cheapest and fastest selection"],
                ["hotels.json", "40", "6", "Hotel recommendation and budget"],
                ["places.json", "40", "5", "Attraction discovery and itinerary"],
            ]
        )
    )

    # 2. Data quality
    story.append(Paragraph("2. Data Quality", styles["heading"]))
    story.append(
        Paragraph(
            "<b>Missing values:</b> None in any dataset. All 18 columns are complete.", styles["body"]
        )
    )
    story.append(
        Paragraph(
            "<b>Duplicates:</b> No duplicate IDs (flight_id, hotel_id, place_id). Every record is unique.",
            styles["body"],
        )
    )
    story.append(Paragraph("<b>Data quality issues found:</b>", styles["body"]))
    issues = [
        "Place names are generic and repeated (for example, Famous Fort, Scenic Museum, Historic Park). Three names repeat within the same city.",
        "Place type and name do not match. For example, Famous Fort in Delhi is typed as lake, and Scenic Museum in Kolkata is typed as temple.",
        "Flight dates are all from 2025 (4 Jan to 27 Dec 2025). The app uses the dataset schedule on the user's date, which is documented as a limitation.",
        "Flight durations are coarse: only 60, 75, 150, and 240 minutes. Real routes have longer durations, so the data is simplified.",
        "Stars and price have almost no relationship (correlation 0.072). A 2-star hotel can cost more than a 5-star hotel.",
        "Goa has no beach type in places.json, which is why the itinerary uses other types when beach is requested.",
    ]
    for index, issue in enumerate(issues, start=1):
        story.append(Paragraph(f"{index}. {issue}", styles["bullet"]))

    # 3. Key statistics
    story.append(Paragraph("3. Key Statistics", styles["heading"]))
    story.append(Paragraph("<b>Flights</b>", styles["body"]))
    story.append(
        make_table(
            [
                ["Metric", "Value"],
                ["Price (Rs), mean", "5,511"],
                ["Price (Rs), median", "5,422"],
                ["Price (Rs), range", "2,792 to 8,981"],
                ["Duration (minutes), median", "150"],
                ["Unique routes", "25 (5 routes have more than one flight)"],
                ["Airlines", "Air India (10), SpiceJet (8), IndiGo (6), Go First (5), Vistara (1)"],
            ]
        )
    )
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Hotels</b>", styles["body"]))
    story.append(
        make_table(
            [
                ["Metric", "Value"],
                ["Price per night (Rs), mean", "4,130"],
                ["Price per night (Rs), median", "4,070"],
                ["Price per night (Rs), range", "1,232 to 6,481"],
                ["Stars distribution", "2-star (14), 3-star (6), 4-star (9), 5-star (11)"],
                ["Hotels with 4+ stars", "20 (11 of them at or under Rs 5,000)"],
                ["Stars and price correlation", "0.072"],
            ]
        )
    )
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Places</b>", styles["body"]))
    story.append(
        make_table(
            [
                ["Metric", "Value"],
                ["Rating, mean / median", "4.18 / 4.20"],
                ["Rating range", "3.50 to 4.90"],
                ["Places rated 4.0 or above", "28 out of 40 (70%)"],
                ["Types", "park (8), market (7), museum (6), temple (5), lake (4), fort (4), beach (4), monument (2)"],
            ]
        )
    )

    # 4. Insights
    story.append(Paragraph("4. Insights", styles["heading"]))
    insights = [
        "Hotel price is not driven by stars, so the app ranks hotels by stars first and then by price. This makes a cheap 5-star hotel (Royal Heritage, Rs 1,232) a top pick.",
        "Four-star options are limited. Only 11 hotels with 4+ stars cost Rs 5,000 or less, so a tight budget with a high star requirement can return no results. The app shows the closest alternatives in that case.",
        "Interest-based itineraries are constrained. Some cities have few places of a given type, so the itinerary falls back to top-rated places and shows a message.",
        "Flight selection is simple. Most routes have one flight, so cheapest and fastest often return the same option.",
    ]
    for index, insight in enumerate(insights, start=1):
        story.append(Paragraph(f"{index}. {insight}", styles["bullet"]))

    # 5. Limitations
    story.append(Paragraph("5. Limitations", styles["heading"]))
    limitations = [
        "Sample datasets, not live data. Prices and availability do not reflect the real market.",
        "Flight dates are historical, so the schedule is an estimate for future dates.",
        "Place names and types can conflict, so the itinerary shows the type but not a description.",
        "Small size (30 to 40 records per dataset) limits the statistical power of any analysis.",
    ]
    for limitation in limitations:
        story.append(Paragraph(f"- {limitation}", styles["bullet"]))

    # 6. Next steps
    story.append(Paragraph("6. Next Steps", styles["heading"]))
    next_steps = [
        "Replace sample data with a real source (scraped or API-based hotel and flight prices).",
        "Add place descriptions and coordinates for better itineraries and map views.",
        "Normalize place names and types so that they match each other.",
        "Add a validation step when loading data, with unique IDs per city.",
    ]
    for step in next_steps:
        story.append(Paragraph(f"- {step}", styles["bullet"]))

    return story


def create_pdf(output_path: str = OUTPUT_FILE) -> None:
    """Build the EDA report PDF at the given path."""
    document = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="EDA Report: Travel Planning Datasets",
    )
    document.build(build_story(build_styles()))
    print(f"PDF created: {output_path}")


if __name__ == "__main__":
    create_pdf()