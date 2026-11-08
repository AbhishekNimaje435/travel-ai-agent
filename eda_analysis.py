"""Exploratory data analysis for flights, hotels, and places datasets."""

import json
import os
from collections import Counter

import pandas as pd

DATA_DIRECTORY = os.path.join(os.path.dirname(__file__), "data")


def load_dataset(file_name: str) -> pd.DataFrame:
    """Load one JSON dataset into a pandas DataFrame."""
    with open(os.path.join(DATA_DIRECTORY, file_name), "r", encoding="utf-8") as json_file:
        return pd.DataFrame(json.load(json_file))


def print_section(title: str) -> None:
    """Print a clear section heading in the terminal."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def analyze_flights(flights_df: pd.DataFrame) -> None:
    """Print key statistics about the flights dataset."""
    print_section("FLIGHTS DATASET")
    print(f"Total records: {len(flights_df)}")
    print(f"Missing values:\n{flights_df.isnull().sum().to_string()}")
    print(f"Duplicate flight_id: {flights_df['flight_id'].duplicated().sum()}")
    print(f"Airlines:\n{flights_df['airline'].value_counts().to_string()}")
    print(f"\nPrice (Rs) summary:\n{flights_df['price'].describe().round(2).to_string()}")

    departure = pd.to_datetime(flights_df["departure_time"])
    arrival = pd.to_datetime(flights_df["arrival_time"])
    duration_minutes = (arrival - departure).dt.total_seconds() / 60
    print(f"\nDuration (minutes) summary:\n{duration_minutes.describe().round(2).to_string()}")
    print(f"Flights with duration under 60 min: {(duration_minutes < 60).sum()}")
    print(f"Flights with duration over 300 min: {(duration_minutes > 300).sum()}")
    print(f"Date range: {departure.min().date()} to {departure.max().date()}")

    route_counts = Counter(zip(flights_df["from"], flights_df["to"]))
    print(f"Unique routes: {len(route_counts)}")
    print(f"Routes with more than one flight: {sum(1 for count in route_counts.values() if count > 1)}")


def analyze_hotels(hotels_df: pd.DataFrame) -> None:
    """Print key statistics about the hotels dataset."""
    print_section("HOTELS DATASET")
    print(f"Total records: {len(hotels_df)}")
    print(f"Missing values:\n{hotels_df.isnull().sum().to_string()}")
    print(f"Duplicate hotel_id: {hotels_df['hotel_id'].duplicated().sum()}")
    print(f"Hotels per city:\n{hotels_df['city'].value_counts().to_string()}")
    print(f"\nStars distribution:\n{hotels_df['stars'].value_counts().sort_index().to_string()}")
    print(f"\nPrice per night (Rs) summary:\n{hotels_df['price_per_night'].describe().round(2).to_string()}")

    correlation = hotels_df["stars"].corr(hotels_df["price_per_night"])
    print(f"\nCorrelation between stars and price: {correlation:.3f}")

    four_star_plus = hotels_df[hotels_df["stars"] >= 4]
    print(f"Hotels with 4+ stars: {len(four_star_plus)}")
    print(f"Hotels with 4+ stars under Rs 5000: {(four_star_plus['price_per_night'] <= 5000).sum()}")


def analyze_places(places_df: pd.DataFrame) -> None:
    """Print key statistics about the places dataset."""
    print_section("PLACES DATASET")
    print(f"Total records: {len(places_df)}")
    print(f"Missing values:\n{places_df.isnull().sum().to_string()}")
    print(f"Duplicate place_id: {places_df['place_id'].duplicated().sum()}")
    print(f"Places per city:\n{places_df['city'].value_counts().to_string()}")
    print(f"\nType distribution:\n{places_df['type'].value_counts().to_string()}")
    print(f"\nRating summary:\n{places_df['rating'].describe().round(2).to_string()}")
    print(f"Places with rating 4.0 or above: {(places_df['rating'] >= 4.0).sum()}")

    duplicate_names = places_df.groupby(["name", "city"]).size()
    print(f"Same name used more than once in the same city: {(duplicate_names > 1).sum()}")


def main() -> None:
    """Run the EDA for all three datasets."""
    flights_df = load_dataset("flights.json")
    hotels_df = load_dataset("hotels.json")
    places_df = load_dataset("places.json")

    analyze_flights(flights_df)
    analyze_hotels(hotels_df)
    analyze_places(places_df)


if __name__ == "__main__":
    main()