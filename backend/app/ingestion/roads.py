"""Fetch major roads from OpenStreetMap for noise estimation."""

import httpx
from sqlalchemy import text
from app.config import settings
from app.database import SyncSession

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
BBOX = f"{settings.sofia_south},{settings.sofia_west},{settings.sofia_north},{settings.sofia_east}"


def fetch_major_roads():
    query = f"""
[out:json][timeout:60];
way["highway"~"motorway|trunk|primary|secondary"]({BBOX});
out geom;
"""
    print("Fetching major roads from OSM...")
    client = httpx.Client(timeout=120)
    resp = client.post(OVERPASS_URL, data={"data": query})
    resp.raise_for_status()
    elements = resp.json().get("elements", [])
    client.close()

    session = SyncSession()
    try:
        session.execute(text("TRUNCATE major_roads RESTART IDENTITY;"))

        rows = []
        for el in elements:
            geom = el.get("geometry", [])
            if len(geom) < 2:
                continue

            coords = ",".join(f"{p['lon']} {p['lat']}" for p in geom)
            wkt = f"SRID=4326;LINESTRING({coords})"
            tags = el.get("tags", {})

            rows.append({
                "osm_id": el.get("id"),
                "road_type": tags.get("highway", ""),
                "name": tags.get("name") or tags.get("name:bg", ""),
                "geom": wkt,
            })

        if rows:
            for i in range(0, len(rows), 500):
                batch = rows[i:i + 500]
                session.execute(
                    text(
                        "INSERT INTO major_roads (osm_id, road_type, name, geom) "
                        "VALUES (:osm_id, :road_type, :name, :geom)"
                    ),
                    batch,
                )

        session.commit()
        print(f"  -> {len(rows)} road segments inserted")
    finally:
        session.close()


if __name__ == "__main__":
    fetch_major_roads()
