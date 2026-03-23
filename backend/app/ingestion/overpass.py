"""Fetch POIs from OpenStreetMap via Overpass API."""

import json
import time
import httpx
from sqlalchemy import text
from app.config import settings
from app.database import SyncSession

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

BBOX = f"{settings.sofia_south},{settings.sofia_west},{settings.sofia_north},{settings.sofia_east}"

POI_QUERIES = {
    "park": {"tags": ['"leisure"="park"'], "expected": "~200"},
    "kindergarten": {"tags": ['"amenity"="kindergarten"'], "expected": "~300"},
    "school": {"tags": ['"amenity"="school"'], "expected": "~400"},
    "hospital": {"tags": ['"amenity"="hospital"'], "expected": "~30"},
    "pharmacy": {"tags": ['"amenity"="pharmacy"'], "expected": "~400"},
    "supermarket": {"tags": ['"shop"="supermarket"'], "expected": "~300"},
}


def _build_query(tags: list[str]) -> str:
    tag_filters = "".join(f"[{t}]" for t in tags)
    return f"""
[out:json][timeout:60];
(
  node{tag_filters}({BBOX});
  way{tag_filters}({BBOX});
  relation{tag_filters}({BBOX});
);
out center;
"""


def _parse_elements(elements: list, category: str) -> list[dict]:
    rows = []
    for el in elements:
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue
        tags = el.get("tags", {})
        rows.append({
            "osm_id": el.get("id"),
            "category": category,
            "subcategory": None,
            "name": tags.get("name") or tags.get("name:bg"),
            "geom": f"SRID=4326;POINT({lon} {lat})",
            "tags": json.dumps(tags, ensure_ascii=False) if tags else "{}",
        })
    return rows


def fetch_pois():
    session = SyncSession()
    try:
        session.execute(text("TRUNCATE pois RESTART IDENTITY;"))
        session.commit()

        client = httpx.Client(timeout=120)
        for category, info in POI_QUERIES.items():
            query = _build_query(info["tags"])
            print(f"Fetching {category} (expected {info['expected']})...")

            resp = client.post(OVERPASS_URL, data={"data": query})
            resp.raise_for_status()
            data = resp.json()

            elements = data.get("elements", [])
            rows = _parse_elements(elements, category)

            if rows:
                session.execute(
                    text(
                        "INSERT INTO pois (osm_id, category, subcategory, name, geom, tags) "
                        "VALUES (:osm_id, :category, :subcategory, :name, :geom, CAST(:tags AS jsonb))"
                    ),
                    rows,
                )
                session.commit()

            print(f"  -> {len(rows)} {category} POIs inserted")
            time.sleep(2)  # respect Overpass rate limits

        client.close()
        total = session.execute(text("SELECT COUNT(*) FROM pois")).scalar()
        print(f"Total POIs: {total}")
    finally:
        session.close()


if __name__ == "__main__":
    fetch_pois()
