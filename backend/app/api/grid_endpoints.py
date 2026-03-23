import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.weights import WeightParams

router = APIRouter(prefix="/grid", tags=["grid"])


@router.get("/scores")
async def get_grid_scores(
    w_transport: float = Query(5, ge=0, le=10),
    w_parks: float = Query(4, ge=0, le=10),
    w_education: float = Query(4, ge=0, le=10),
    w_air_quality: float = Query(3, ge=0, le=10),
    w_noise: float = Query(3, ge=0, le=10),
    w_shopping: float = Query(3, ge=0, le=10),
    w_healthcare: float = Query(3, ge=0, le=10),
    w_commute: float = Query(3, ge=0, le=10),
    min_score: float = Query(0.0, ge=0, le=1),
    db: AsyncSession = Depends(get_db),
):
    params = WeightParams(
        w_transport=w_transport, w_parks=w_parks, w_education=w_education,
        w_air_quality=w_air_quality, w_noise=w_noise, w_shopping=w_shopping,
        w_healthcare=w_healthcare, w_commute=w_commute,
    )
    weights = params.normalized()

    result = await db.execute(text("""
        SELECT row_idx, col_idx,
               ST_AsGeoJSON(boundary) as geojson,
               ST_Y(centroid) as lat, ST_X(centroid) as lon,
               COALESCE(score_transport, 0) * :wt
               + COALESCE(score_parks, 0) * :wp
               + COALESCE(score_education, 0) * :we
               + COALESCE(score_air_quality, 0) * :wa
               + COALESCE(score_noise, 0) * :wn
               + COALESCE(score_shopping, 0) * :ws
               + COALESCE(score_healthcare, 0) * :wh
               + COALESCE(score_commute, 0) * :wc
               AS total_score,
               score_transport, score_parks, score_education,
               score_air_quality, score_noise, score_shopping,
               score_healthcare, score_commute
        FROM grid_cells
        WHERE score_transport IS NOT NULL
    """), {
        "wt": weights["transport"], "wp": weights["parks"],
        "we": weights["education"], "wa": weights["air_quality"],
        "wn": weights["noise"], "ws": weights["shopping"],
        "wh": weights["healthcare"], "wc": weights["commute"],
    })

    rows = list(result)
    raw_scores = [r.total_score for r in rows if r.total_score >= min_score]
    if not raw_scores:
        return {"type": "FeatureCollection", "features": []}

    score_min = min(raw_scores)
    score_max = max(raw_scores)
    score_range = score_max - score_min if score_max > score_min else 1.0

    features = []
    for row in rows:
        if row.total_score < min_score:
            continue
        normalized = (row.total_score - score_min) / score_range
        features.append({
            "type": "Feature",
            "geometry": json.loads(row.geojson),
            "properties": {
                "row": row.row_idx,
                "col": row.col_idx,
                "score": round(normalized, 4),
                "raw_score": round(row.total_score, 4),
                "lat": round(row.lat, 6),
                "lon": round(row.lon, 6),
                "scores": {
                    "transport": round(row.score_transport or 0, 4),
                    "parks": round(row.score_parks or 0, 4),
                    "education": round(row.score_education or 0, 4),
                    "air_quality": round(row.score_air_quality or 0, 4),
                    "noise": round(row.score_noise or 0, 4),
                    "shopping": round(row.score_shopping or 0, 4),
                    "healthcare": round(row.score_healthcare or 0, 4),
                    "commute": round(row.score_commute or 0, 4),
                },
            },
        })

    return {"type": "FeatureCollection", "features": features}


@router.get("/cell/{row}/{col}")
async def get_cell_detail(
    row: int,
    col: int,
    db: AsyncSession = Depends(get_db),
):
    # Get cell scores
    cell = await db.execute(text("""
        SELECT row_idx, col_idx, ST_Y(centroid) as lat, ST_X(centroid) as lon,
               score_transport, score_parks, score_education,
               score_air_quality, score_noise, score_shopping,
               score_healthcare, score_commute
        FROM grid_cells WHERE row_idx = :row AND col_idx = :col
    """), {"row": row, "col": col})
    cell_row = cell.first()
    if not cell_row:
        return {"error": "Cell not found"}

    # Get nearest POIs for each category
    nearby = {}
    for category in ["park", "kindergarten", "school", "hospital", "pharmacy", "supermarket"]:
        pois = await db.execute(text("""
            SELECT name, ST_Distance(
                (SELECT centroid::geography FROM grid_cells WHERE row_idx = :row AND col_idx = :col),
                geom::geography
            ) as distance_m
            FROM pois WHERE category = :cat
            ORDER BY geom::geography <-> (SELECT centroid::geography FROM grid_cells WHERE row_idx = :row AND col_idx = :col)
            LIMIT 3
        """), {"row": row, "col": col, "cat": category})
        nearby[category] = [
            {"name": r.name or "Unnamed", "distance_m": round(r.distance_m)}
            for r in pois
        ]

    # Get nearest transport stops
    stops = await db.execute(text("""
        SELECT name, stop_type, ST_Distance(
            (SELECT centroid::geography FROM grid_cells WHERE row_idx = :row AND col_idx = :col),
            geom::geography
        ) as distance_m
        FROM transport_stops
        ORDER BY geom::geography <-> (SELECT centroid::geography FROM grid_cells WHERE row_idx = :row AND col_idx = :col)
        LIMIT 5
    """), {"row": row, "col": col})
    nearby["transport"] = [
        {"name": r.name or "Unnamed", "type": r.stop_type, "distance_m": round(r.distance_m)}
        for r in stops
    ]

    return {
        "row": cell_row.row_idx,
        "col": cell_row.col_idx,
        "centroid": [cell_row.lat, cell_row.lon],
        "scores": {
            "transport": round(cell_row.score_transport or 0, 4),
            "parks": round(cell_row.score_parks or 0, 4),
            "education": round(cell_row.score_education or 0, 4),
            "air_quality": round(cell_row.score_air_quality or 0, 4),
            "noise": round(cell_row.score_noise or 0, 4),
            "shopping": round(cell_row.score_shopping or 0, 4),
            "healthcare": round(cell_row.score_healthcare or 0, 4),
            "commute": round(cell_row.score_commute or 0, 4),
        },
        "nearby": nearby,
    }
