#!/usr/bin/env python3
"""Master ingestion script: fetches all data and computes scores."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ingestion.grid_generator import generate_grid
from app.ingestion.sofiaplan import fetch_pois
from app.ingestion.gtfs import fetch_transport_stops
from app.ingestion.air_quality import fetch_air_quality
from app.ingestion.score_precomputer import compute_all_scores


def main():
    print("=" * 60)
    print("Sofia Apartment Recommender - Data Ingestion Pipeline")
    print("=" * 60)

    print("\n[1/5] Generating grid cells...")
    generate_grid()

    print("\n[2/5] Fetching POIs from Sofia Plan API...")
    fetch_pois()

    print("\n[3/5] Fetching transport stops...")
    fetch_transport_stops()

    print("\n[4/5] Fetching air quality data...")
    fetch_air_quality()

    print("\n[5/5] Computing scores...")
    compute_all_scores()

    print("\n" + "=" * 60)
    print("Ingestion complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
