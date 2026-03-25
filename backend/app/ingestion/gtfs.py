"""Fetch public transport stops from Sofia Plan API (dataset 253) with GTFS fallback."""

import csv
import io
import zipfile
import httpx
from sqlalchemy import text
from app.config import settings
from app.database import SyncSession

SOFIAPLAN_STOPS_URL = "https://api.sofiaplan.bg/datasets/253"
GTFS_URL = "https://gtfs.sofiatraffic.bg/latest/gtfs.zip"

ROUTE_TYPE_MAP = {
    "0": "tram",
    "1": "metro",
    "2": "rail",
    "3": "bus",
    "11": "trolley",
    "800": "trolley",
}


def _stop_type_from_props(props: dict) -> str:
    """Infer stop type from sofiaplan line fields."""
    if props.get("ЛИНИЯ_ТМ") or props.get("LINIA_TM"):
        return "metro"
    if props.get("ЛИНИЯ_ТВ") or props.get("LINIA_TV"):
        return "tram"
    return "bus"


def _fetch_sofiaplan(session) -> bool:
    print("Downloading transport stops from Sofia Plan API...")
    client = httpx.Client(timeout=120)
    try:
        resp = client.get(SOFIAPLAN_STOPS_URL)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  Sofia Plan stops download failed: {e}")
        client.close()
        return False

    features = data.get("features", []) if isinstance(data, dict) else []
    rows = []
    for feat in features:
        geometry = feat.get("geometry")
        props = feat.get("properties") or {}
        if not geometry:
            continue

        coords = geometry.get("coordinates")
        if not coords:
            continue
        geom_type = geometry.get("type", "")
        if geom_type == "Point":
            lon, lat = coords[0], coords[1]
        elif geom_type == "MultiPoint":
            lon, lat = coords[0][0], coords[0][1]
        else:
            continue

        if not (settings.sofia_south <= lat <= settings.sofia_north
                and settings.sofia_west <= lon <= settings.sofia_east):
            continue

        rows.append({
            "stop_id": str(props.get("КОД_СПИРКА") or props.get("KOD_SPIRKA") or props.get("mi_prinx") or ""),
            "name": str(props.get("ИМЕ_СПИРКА") or props.get("IME_SPIRKA") or ""),
            "stop_type": _stop_type_from_props(props),
            "geom": f"SRID=4326;POINT({lon} {lat})",
            "route_count": 0,
            "source": "sofiaplan",
        })

    if not rows:
        client.close()
        return False

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
    print(f"  -> {len(rows)} stops from Sofia Plan")
    client.close()
    return True


def _fetch_gtfs(session) -> bool:
    print("Downloading Sofia GTFS data...")
    client = httpx.Client(timeout=120, follow_redirects=True)
    try:
        resp = client.get(GTFS_URL)
        resp.raise_for_status()
    except Exception as e:
        print(f"  GTFS download failed: {e}")
        client.close()
        return False

    zf = zipfile.ZipFile(io.BytesIO(resp.content))

    route_types = {}
    if "routes.txt" in zf.namelist():
        with zf.open("routes.txt") as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"))
            for row in reader:
                route_types[row["route_id"]] = ROUTE_TYPE_MAP.get(row.get("route_type", "3"), "bus")

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

    if not rows:
        client.close()
        return False

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


def fetch_transport_stops():
    session = SyncSession()
    try:
        session.execute(text("TRUNCATE transport_stops RESTART IDENTITY;"))
        session.commit()

        if not _fetch_sofiaplan(session):
            print("Falling back to GTFS...")
            _fetch_gtfs(session)

        total = session.execute(text("SELECT COUNT(*) FROM transport_stops")).scalar()
        print(f"Total transport stops: {total}")
    finally:
        session.close()


if __name__ == "__main__":
    fetch_transport_stops()
