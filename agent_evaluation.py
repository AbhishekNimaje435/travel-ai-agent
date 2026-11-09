"""Runs test queries through the travel agent and records the results for the agent performance report."""

import csv
import time
from datetime import date, timedelta

from agent.travel_agent import run_travel_agent_json

OUTPUT_CSV = "agent_evaluation_results.csv"
DELAY_BETWEEN_QUERIES_SECONDS = 20


def make_test_cases():
    """Return the 12 test queries with what each one should check."""
    today = date.today()
    start = today + timedelta(days=7)
    end = today + timedelta(days=9)

    def dates_text(start_date, end_date):
        return f"Travel dates: {start_date.isoformat()} to {end_date.isoformat()}."

    return [
        {
            "id": "T01",
            "name": "Basic Goa trip, cheapest flight",
            "query": (
                f"Plan a 3-day trip from Hyderabad to Goa. {dates_text(start, end)} "
                "Travellers: 1. Flight preference: cheapest. Hotel at least 4 stars, up to Rs 7000 per night. "
                "Total budget Rs 30000."
            ),
            "expect_budget_under": 30000,
        },
        {
            "id": "T02",
            "name": "Two travellers, fastest flight",
            "query": (
                f"Plan a 3-day trip from Hyderabad to Goa. {dates_text(start, end)} "
                "Travellers: 2. Flight preference: fastest. Hotel at least 4 stars, up to Rs 7000 per night. "
                "Total budget Rs 40000."
            ),
            "expect_budget_under": 40000,
        },
        {
            "id": "T03",
            "name": "Return flight included",
            "query": (
                f"Plan a 3-day trip from Hyderabad to Goa with a return flight. {dates_text(start, end)} "
                "Travellers: 1. Flight preference: cheapest. Hotel at least 4 stars, up to Rs 7000 per night. "
                "Total budget Rs 30000."
            ),
            "expect_budget_under": 30000,
        },
        {
            "id": "T04",
            "name": "Over-budget trip (should warn)",
            "query": (
                f"Plan a 3-day trip from Delhi to Goa. {dates_text(start, end)} "
                "Travellers: 4. Flight preference: cheapest. Hotel at least 4 stars, up to Rs 7000 per night. "
                "Total budget Rs 10000."
            ),
            "expect_budget_under": 10000,
        },
        {
            "id": "T05",
            "name": "Hotel amenity filter (pool)",
            "query": (
                f"Plan a 3-day trip from Hyderabad to Goa. {dates_text(start, end)} "
                "Travellers: 1. Hotel must have pool. Hotel at least 4 stars, up to Rs 7000 per night. "
                "Total budget Rs 30000."
            ),
            "expect_budget_under": 30000,
        },
        {
            "id": "T06",
            "name": "Interests: temple and museum",
            "query": (
                f"Plan a 3-day trip from Hyderabad to Chennai. {dates_text(start, end)} "
                "Travellers: 1. Attraction interests: temple, museum. Hotel at least 3 stars, up to Rs 6000 per night. "
                "Total budget Rs 30000."
            ),
            "expect_budget_under": 30000,
        },
        {
            "id": "T07",
            "name": "Kolkata trip, no interests",
            "query": (
                f"Plan a 3-day trip from Delhi to Kolkata. {dates_text(start, end)} "
                "Travellers: 1. No specific interests. Hotel at least 4 stars, up to Rs 7000 per night. "
                "Total budget Rs 30000."
            ),
            "expect_budget_under": 30000,
        },
        {
            "id": "T08",
            "name": "Jaipur trip, fort and monument",
            "query": (
                f"Plan a 3-day trip from Mumbai to Jaipur. {dates_text(start, end)} "
                "Travellers: 1. Attraction interests: fort, monument. Hotel at least 4 stars, up to Rs 7000 per night. "
                "Total budget Rs 30000."
            ),
            "expect_budget_under": 30000,
        },
        {
            "id": "T09",
            "name": "Strict star filter (5 stars)",
            "query": (
                f"Plan a 2-day trip from Hyderabad to Goa. "
                f"{dates_text(start, start + timedelta(days=1))} "
                "Travellers: 1. Hotel must be 5 stars. Up to Rs 7000 per night. Total budget Rs 30000."
            ),
            "expect_budget_under": 30000,
        },
        {
            "id": "T10",
            "name": "Extra requirement: vegetarian food",
            "query": (
                f"Plan a 3-day trip from Hyderabad to Goa. {dates_text(start, end)} "
                "Travellers: 1. Hotel at least 4 stars, up to Rs 7000 per night. Total budget Rs 30000. "
                "Extra requirement: vegetarian food, relaxed pace."
            ),
            "expect_budget_under": 30000,
        },
        {
            "id": "T11",
            "name": "Mumbai trip, 4 days",
            "query": (
                f"Plan a 4-day trip from Bangalore to Mumbai. "
                f"{dates_text(start, start + timedelta(days=3))} "
                "Travellers: 1. Hotel at least 4 stars, up to Rs 7000 per night. Total budget Rs 40000."
            ),
            "expect_budget_under": 40000,
        },
        {
            "id": "T12",
            "name": "Invalid city (should refuse or explain)",
            "query": (
                f"Plan a 3-day trip from Hyderabad to Paris. {dates_text(start, end)} "
                "Travellers: 1. Hotel at least 4 stars, up to Rs 7000 per night. Total budget Rs 30000."
            ),
            "expect_budget_under": None,
        },
    ]


def check_result(test_case, trip_json):
    """Return a dictionary of pass/fail checks for one result."""
    if trip_json is None:
        return {
            "json_valid": False,
            "all_sections_present": False,
            "itinerary_days_filled": False,
            "budget_within_limit": False,
            "budget_math_correct": False,
        }

    required_keys = ["trip_summary", "flight", "hotel", "weather", "itinerary", "budget", "messages"]
    checks = {
        "json_valid": True,
        "all_sections_present": all(key in trip_json for key in required_keys),
    }

    itinerary = trip_json.get("itinerary", [])
    checks["itinerary_days_filled"] = bool(itinerary) and all(day.get("places") for day in itinerary)

    budget = trip_json.get("budget") or {}
    expected_limit = test_case["expect_budget_under"]
    if expected_limit is None:
        checks["budget_within_limit"] = None
    else:
        checks["budget_within_limit"] = budget.get("total", 0) <= expected_limit

    component_sum = sum(budget.get(key, 0) for key in ["flight", "hotel", "local_expenses"])
    checks["budget_math_correct"] = abs(component_sum - budget.get("total", 0)) < 1

    return checks


def load_finished_ids():
    """Return the IDs of tests that already have a successful row in the results CSV."""
    try:
        with open(OUTPUT_CSV, "r", encoding="utf-8") as csv_file:
            return {row["id"] for row in csv.DictReader(csv_file) if row.get("error") == ""}
    except FileNotFoundError:
        return set()


def run_evaluation():
    """Run the remaining test cases, save the results, and print a summary."""
    finished_ids = load_finished_ids()
    results = []

    try:
        with open(OUTPUT_CSV, "r", encoding="utf-8") as csv_file:
            results = [row for row in csv.DictReader(csv_file) if row.get("error") == ""]
    except FileNotFoundError:
        pass

    for test_case in make_test_cases():
        if test_case["id"] in finished_ids:
            print(f"Skipping {test_case['id']} (already done)")
            continue

        print(f"Running {test_case['id']}: {test_case['name']} ...")
        start_time = time.time()
        try:
            trip_json = run_travel_agent_json(test_case["query"])
            error_message = ""
        except Exception as run_error:
            trip_json = None
            error_message = str(run_error)

        duration = round(time.time() - start_time, 1)
        checks = check_result(test_case, trip_json)

        results.append(
            {
                "id": test_case["id"],
                "name": test_case["name"],
                "duration_seconds": duration,
                "error": error_message,
                **checks,
            }
        )

        print(f"  done in {duration}s, error: {error_message or 'none'}")
        time.sleep(DELAY_BETWEEN_QUERIES_SECONDS)

    if not results:
        print("No results to save.")
        return

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    print(f"\nResults saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    run_evaluation()
