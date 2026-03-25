"""Fetch POIs from the Sofia Plan open data API (https://api.sofiaplan.bg)."""

import json
import httpx
from shapely.geometry import shape
from sqlalchemy import text
from app.database import SyncSession

SOFIAPLAN_API = "https://api.sofiaplan.bg/datasets"

# dataset_id -> category name
DATASETS = {
    235: "park",
    271: "kindergarten",
    166: "school",
    5: "playground",
}

NAME_FIELDS = ["object_nam", "ime", "name", "NAME", "IME", "наименование"]


def _extract_name(props: dict) -> str | None:
    for field in NAME_FIELDS:
        val = props.get(field)
        if val and str(val).strip():
            return str(val).strip()
    return None


def _extract_point(geometry: dict) -> tuple[float, float] | None:
    """Return (lon, lat) from any geometry type."""
    geom_type = geometry.get("type", "")
    coords = geometry.get("coordinates")
    if not coords:
        return None

    if geom_type == "Point":
        return coords[0], coords[1]
    elif geom_type == "MultiPoint":
        return coords[0][0], coords[0][1]
    else:
        # Use shapely centroid for polygons/lines
        try:
            centroid = shape(geometry).centroid
            return centroid.x, centroid.y
        except Exception:
            return None


def fetch_pois():
    session = SyncSession()
    try:
        session.execute(text("TRUNCATE pois RESTART IDENTITY;"))
        session.commit()

        client = httpx.Client(timeout=120)
        for dataset_id, category in DATASETS.items():
            print(f"Fetching {category} from sofiaplan dataset {dataset_id}...")
            try:
                resp = client.get(f"{SOFIAPLAN_API}/{dataset_id}")
                resp.raise_for_status()
            except Exception as e:
                print(f"  -> FAILED: {e}")
                continue

            try:
                data = resp.json()
            except Exception:
                print(f"  -> FAILED: response is not JSON")
                continue

            if isinstance(data, list):
                features = data
            else:
                features = data.get("features", [])
            rows = []
            for feat in features:
                if not isinstance(feat, dict):
                    continue
                geometry = feat.get("geometry")
                # GeoJSON Feature
                if geometry is not None:
                    props = feat.get("properties") or {}
                else:
                    # Plain object without geometry — skip
                    continue

                point = _extract_point(geometry)
                if point is None:
                    continue
                lon, lat = point

                rows.append({
                    "osm_id": None,
                    "category": category,
                    "subcategory": None,
                    "name": _extract_name(props),
                    "geom": f"SRID=4326;POINT({lon} {lat})",
                    "tags": json.dumps(props, ensure_ascii=False),
                })

            if rows:
                for i in range(0, len(rows), 500):
                    batch = rows[i:i + 500]
                    session.execute(
                        text(
                            "INSERT INTO pois (osm_id, category, subcategory, name, geom, tags) "
                            "VALUES (:osm_id, :category, :subcategory, :name, :geom, CAST(:tags AS jsonb))"
                        ),
                        batch,
                    )
                session.commit()

            print(f"  -> {len(rows)} {category} POIs inserted")

        client.close()
        total = session.execute(text("SELECT COUNT(*) FROM pois")).scalar()
        print(f"Total POIs: {total}")
    finally:
        session.close()


if __name__ == "__main__":
    fetch_pois()
