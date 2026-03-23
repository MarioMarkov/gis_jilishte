"""Fetch air quality data from Open-Meteo API."""

import httpx
from sqlalchemy import text
from app.config import settings
from app.database import SyncSession

AQ_API = "https://air-quality-api.open-meteo.com/v1/air-quality"

# Sample every ~1km across Sofia
SAMPLE_STEP_KM = 1.0


def fetch_air_quality():
    lat_step = SAMPLE_STEP_KM / 111.32
    lon_step = SAMPLE_STEP_KM / (111.32 * 0.7373)  # cos(42.7deg)

    points = []
    lat = settings.sofia_south
    while lat <= settings.sofia_north:
        lon = settings.sofia_west
        while lon <= settings.sofia_east:
            points.append((round(lat, 4), round(lon, 4)))
            lon += lon_step
        lat += lat_step

    print(f"Fetching air quality for {len(points)} sample points...")

    session = SyncSession()
    try:
        session.execute(text("TRUNCATE air_quality_samples RESTART IDENTITY;"))
        session.commit()

        client = httpx.Client(timeout=60)
        rows = []

        # Batch requests: Open-Meteo supports comma-separated coordinates
        batch_size = 10
        for i in range(0, len(points), batch_size):
            batch_points = points[i:i + batch_size]
            lats = ",".join(str(p[0]) for p in batch_points)
            lons = ",".join(str(p[1]) for p in batch_points)

            try:
                resp = client.get(AQ_API, params={
                    "latitude": lats,
                    "longitude": lons,
                    "hourly": "pm2_5,pm10,european_aqi",
                    "past_days": 7,
                    "forecast_days": 0,
                })
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"  Warning: batch {i} failed: {e}")
                continue

            # Handle both single and multi-location responses
            results = data if isinstance(data, list) else [data]
            for j, result in enumerate(results):
                hourly = result.get("hourly", {})
                pm25_vals = [v for v in hourly.get("pm2_5", []) if v is not None]
                pm10_vals = [v for v in hourly.get("pm10", []) if v is not None]
                aqi_vals = [v for v in hourly.get("european_aqi", []) if v is not None]

                idx = i + j if j < len(batch_points) else 0
                if idx >= len(points):
                    continue
                lat, lon = batch_points[min(j, len(batch_points) - 1)]

                rows.append({
                    "geom": f"SRID=4326;POINT({lon} {lat})",
                    "pm25_avg": sum(pm25_vals) / len(pm25_vals) if pm25_vals else None,
                    "pm10_avg": sum(pm10_vals) / len(pm10_vals) if pm10_vals else None,
                    "aqi_avg": sum(aqi_vals) / len(aqi_vals) if aqi_vals else None,
                })

            if (i // batch_size) % 10 == 0:
                print(f"  Progress: {i + len(batch_points)}/{len(points)} points")

        client.close()

        if rows:
            for i in range(0, len(rows), 500):
                batch = rows[i:i + 500]
                session.execute(
                    text(
                        "INSERT INTO air_quality_samples (geom, pm25_avg, pm10_avg, aqi_avg) "
                        "VALUES (:geom, :pm25_avg, :pm10_avg, :aqi_avg)"
                    ),
                    batch,
                )
            session.commit()

        print(f"  -> {len(rows)} air quality samples inserted")
    finally:
        session.close()


if __name__ == "__main__":
    fetch_air_quality()
