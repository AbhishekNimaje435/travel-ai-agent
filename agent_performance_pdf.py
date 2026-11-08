"""Creates the Agent Performance Report as a PDF, using the evaluation CSV results."""

import csv
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

from agent_evaluation import make_test_cases

RESULTS_CSV = "agent_evaluation_results.csv"
OUTPUT_FILE = "Agent_Performance_Report_Travel_Planner.pdf"

CHECK_COLUMNS = [
    "json_valid",
    "all_sections_present",
    "itinerary_days_filled",
    "budget_within_limit",
    "budget_math_correct",
]


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
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b0b8d0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5fb")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def load_results() -> dict:
    """Read the evaluation CSV and return results keyed by test ID."""
    if not os.path.exists(RESULTS_CSV):
        return {}
    with open(RESULTS_CSV, "r", encoding="utf-8") as csv_file:
        return {row["id"]: row for row in csv.DictReader(csv_file)}


def format_check(value: str) -> str:
    """Turn a CSV string value into a readable mark."""
    if value == "True":
        return "Pass"
    if value == "False":
        return "Fail"
    if value == "":
        return "-"
    return "N/A"


def row_passed(result: dict) -> bool:
    """A test passes when it has no error and every check that applies is True."""
    if result.get("error"):
        return False
    for column in CHECK_COLUMNS:
        value = result.get(column, "")
        if value == "False":
            return False
    return True


def build_story(styles, results):
    """Build the list of report elements in order."""
    story = []
    test_cases = make_test_cases()
    completed = [case for case in test_cases if case["id"] in results]
    passed = [case for case in completed if row_passed(results[case["id"]])]
    failed = [case for case in completed if case not in passed]
    pending = [case for case in test_cases if case["id"] not in results]

    story.append(Paragraph("Agent Performance Report", styles["title"]))
    story.append(
        Paragraph(
            "Evaluation of the AI travel agent on 12 test queries, checking tool use, JSON structure, itinerary completeness, and budget math.",
            styles["body"],
        )
    )

    # 1. Summary
    story.append(Paragraph("1. Summary", styles["heading"]))
    story.append(
        make_table(
            [
                ["Metric", "Value"],
                ["Total test cases", str(len(test_cases))],
                ["Completed", str(len(completed))],
                ["Passed", str(len(passed))],
                ["Failed (including errors)", str(len(failed))],
                ["Pending", str(len(pending))],
                ["Average response time", f"{average_duration(completed):.1f} seconds" if completed else "-"],
            ]
        )
    )
    story.append(
        Paragraph(
            "Note: Tests were run in batches because the Groq free tier has a daily token limit. "
            "Pending tests will be added after the limit resets.",
            styles["body"],
        )
    )

    # 2. Evaluation method
    story.append(Paragraph("2. Evaluation Method", styles["heading"]))
    method_points = [
        "json_valid: the agent returned valid JSON (parsing succeeded).",
        "all_sections_present: trip_summary, flight, hotel, weather, itinerary, budget, and messages are all present.",
        "itinerary_days_filled: every day in the itinerary has at least one place.",
        "budget_within_limit: the total cost is at or below the user's budget (N/A for the invalid-city test).",
        "budget_math_correct: flight + hotel + local expenses equals the total.",
        "A test passes when it has no error and every applicable check is Pass.",
    ]
    for point in method_points:
        story.append(Paragraph(f"- {point}", styles["bullet"]))

    # 3. Test results table
    story.append(Paragraph("3. Test Results", styles["heading"]))
    table_rows = [["ID", "Test name", "Time (s)", "JSON", "Sections", "Itinerary", "Budget limit", "Budget math", "Result"]]
    for case in test_cases:
        result = results.get(case["id"])
        if result is None:
            table_rows.append([case["id"], case["name"], "-", "-", "-", "-", "-", "-", "Pending"])
            continue
        table_rows.append(
            [
                case["id"],
                case["name"],
                result.get("duration_seconds", "-"),
                format_check(result.get("json_valid", "")),
                format_check(result.get("all_sections_present", "")),
                format_check(result.get("itinerary_days_filled", "")),
                format_check(result.get("budget_within_limit", "")),
                format_check(result.get("budget_math_correct", "")),
                "Pass" if row_passed(result) else "Fail",
            ]
        )
    story.append(make_table(table_rows))

    # 4. Errors
    story.append(Paragraph("4. Errors Observed", styles["heading"]))
    error_rows = [["ID", "Error"]]
    for case in completed:
        error_text = results[case["id"]].get("error", "")
        if error_text:
            error_rows.append([case["id"], error_text[:200]])
    if len(error_rows) == 1:
        story.append(Paragraph("No errors recorded in completed tests.", styles["body"]))
    else:
        story.append(make_table(error_rows))
    story.append(
        Paragraph(
            "Groq rate limit errors (429) mean the daily token limit was reached. These are not agent failures.",
            styles["body"],
        )
    )

    # 5. Observations
    story.append(Paragraph("5. Observations", styles["heading"]))
    story.append(
        Paragraph(
            "Observations will be filled in after all 12 tests are complete. Points to look for: whether over-budget trips "
            "are flagged clearly, whether interest filters are followed, and whether invalid cities are handled gracefully.",
            styles["body"],
        )
    )

    # 6. Improvements
    story.append(Paragraph("6. Improvements Made During Development", styles["heading"]))
    improvements = [
        "Tool outputs shortened to 5 items to reduce token use.",
        "Places search limited to one call per plan to avoid repeated tool calls.",
        "Itinerary fallback added: when interests have too few places, top-rated places fill the days, with a note.",
        "Hotel fallback added: closest alternatives shown when no hotel matches exact filters.",
        "Strict rule added: flights are one-way unless both legs are searched.",
    ]
    for item in improvements:
        story.append(Paragraph(f"- {item}", styles["bullet"]))

    return story


def average_duration(completed_cases: list) -> float:
    """Return the average of duration_seconds for completed tests."""
    durations = []
    for case in completed_cases:
        value = load_results().get(case["id"], {}).get("duration_seconds", "")
        if value:
            durations.append(float(value))
    return sum(durations) / len(durations) if durations else 0.0


def create_pdf(output_path: str = OUTPUT_FILE) -> None:
    """Build the agent performance report PDF at the given path."""
    results = load_results()
    document = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title="Agent Performance Report",
    )
    document.build(build_story(build_styles(), results))
    print(f"PDF created: {output_path}")


if __name__ == "__main__":
    create_pdf()