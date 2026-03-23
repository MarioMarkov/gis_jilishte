"""Fetch public transport stops from Sofia GTFS or OSM fallback."""

import csv
import io
import zipfile
import httpx
import time
from sqlalchemy import text
from app.config import settings
from app.database import SyncSession

GTFS_URL = "https://gtfs.sofiatraffic.bg/latest/gtfs.zip"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
BBOX = f"{settings.sofia_south},{settings.sofia_west},{settings.sofia_north},{settings.sofia_east}"

# GTFS route_type mapping
ROUTE_TYPE_MAP = {
    "0": "tram",
    "1": "metro",
    "2": "rail",
    "3": "bus",
    "11": "trolley",
    "800": "trolley",
}


def _fetch_gtfs(session):
    """Try to download and parse GTFS data."""
    print("Downloading Sofia GTFS data...")
    client = httpx.Client(timeout=120, follow_redirects=True)
    try:
        resp = client.get(GTFS_URL)
        resp.raise_for_status()
    except Exception as e:
        print(f"GTFS download failed: {e}")
        return False

    zf = zipfile.ZipFile(io.BytesIO(resp.content))

    # Parse routes to determine route types
    route_types = {}
    if "routes.txt" in zf.namelist():
        with zf.open("routes.txt") as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
            for row in reader:
                route_types[row["route_id"]] = ROUTE_TYPE_MAP.get(
                    row.get("route_type", "3"), "bus"
                )

    # Count routes per stop via stop_times.txt and trips.txt
    trip_routes = {}
    if "trips.txt" in zf.namelist():
        with zf.open("trips.txt") as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
            for row in reader:
                trip_routes[row["trip_id"]] = row["route_id"]

    stop_route_ids = {}
    if "stop_times.txt" in zf.namelist():
        with zf.open("stop_times.txt") as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
            for row in reader:
                sid = row["stop_id"]
                rid = trip_routes.get(row.get("trip_id"))
                if rid:
                    stop_route_ids.setdefault(sid, set()).add(rid)

    # Determine stop type from the routes that serve it
    def get_stop_type(stop_id):
        rids = stop_route_ids.get(stop_id, set())
        types = {route_types.get(rid, "bus") for rid in rids}
        if "metro" in types:
            return "metro"
        if "tram" in types:
            return "tram"
        if "trolley" in types:
            return "trolley"
        return "bus"

    # Parse stops
    rows = []
    with zf.open("stops.txt") as f:
        reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
        for row in reader:
            lat = float(row["stop_lat"])
            lon = float(row["stop_lon"])
            if not (settings.sofia_south <= lat <= settings.sofia_north
                    and settings.sofia_west <= lon <= settings.sofia_east):
                continue
            sid = row["stop_id"]
            rows.append({
                "stop_id": sid,
                "name": row.get("stop_name", ""),
                "stop_type": get_stop_type(sid),
                "geom": f"SRID=4326;POINT({lon} {lat})",
                "route_count": len(stop_route_ids.get(sid, set())),
                "source": "gtfs",
            })

    if rows:
        for i in range(0, len(rows), 1000):
            batch = rows[i:i + 1000]
            session.execute(
                text(
                    "INSERT INTO transport_stops (stop_id, name, stop_type, geom, route_count, source) "
                    "VALUES (:stop_id, :name, :stop_type, :geom, :route_count, :source)"
                ),
                batch,
            )
        session.commit()

    print(f"  -> {len(rows)} stops from GTFS")
    client.close()
    return True


def _fetch_osm_fallback(session):
    """Fallback: fetch transport stops from OSM."""
    print("Falling back to OSM transport stops...")
    client = httpx.Client(timeout=120)

    queries = {
        "bus": f'[out:json][timeout:60];node["highway"="bus_stop"]({BBOX});out;',
        "tram": f'[out:json][timeout:60];node["railway"="tram_stop"]({BBOX});out;',
        "metro": f'[out:json][timeout:60];node["station"="subway"]({BBOX});out;',
    }

    for stop_type, query in queries.items():
        resp = client.post(OVERPASS_URL, data={"data": query})
        resp.raise_for_status()
        elements = resp.json().get("elements", [])

        rows = []
        for el in elements:
            rows.append({
                "stop_id": str(el["id"]),
                "name": el.get("tags", {}).get("name", ""),
                "stop_type": stop_type,
                "geom": f"SRID=4326;POINT({el['lon']} {el['lat']})",
                "route_count": 0,
                "source": "osm",
            })

        if rows:
            session.execute(
                text(
                    "INSERT INTO transport_stops (stop_id, name, stop_type, geom, route_count, source) "
                    "VALUES (:stop_id, :name, :stop_type, :geom, :route_count, :source)"
                ),
                rows,
            )
            session.commit()

        print(f"  -> {len(rows)} {stop_type} stops from OSM")
        time.sleep(2)

    client.close()


def fetch_transport_stops():
    session = SyncSession()
    try:
        session.execute(text("TRUNCATE transport_stops RESTART IDENTITY;"))
        session.commit()

        if not _fetch_gtfs(session):
            _fetch_osm_fallback(session)

        total = session.execute(text("SELECT COUNT(*) FROM transport_stops")).scalar()
        print(f"Total transport stops: {total}")
    finally:
        session.close()


if __name__ == "__main__":
    fetch_transport_stops()
