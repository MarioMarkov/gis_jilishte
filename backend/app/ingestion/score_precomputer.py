"""Pre-compute all 8 scoring dimensions for each grid cell using batch PostGIS queries."""

from sqlalchemy import text
from app.database import SyncSession


def compute_all_scores():
    session = SyncSession()
    try:
        _compute_transport(session)
        _compute_parks(session)
        _compute_education(session)
        _compute_air_quality(session)
        _compute_noise(session)
        _compute_shopping(session)
        _compute_healthcare(session)
        _compute_commute(session)
        _compute_playground(session)

        scored = session.execute(text(
            "SELECT COUNT(*) FROM grid_cells WHERE score_transport IS NOT NULL"
        )).scalar()
        total = session.execute(text("SELECT COUNT(*) FROM grid_cells")).scalar()
        print(f"Scoring complete: {scored}/{total} cells have scores")
    finally:
        session.close()


def _compute_transport(session):
    """Transport score: metro proximity (0.4) + surface stop proximity (0.35) + density (0.25)."""
    print("Computing transport scores...")
    session.execute(text("""
        UPDATE grid_cells g SET score_transport = sub.score FROM (
            SELECT g.id,
                COALESCE(
                    0.4 * GREATEST(0, 1.0 - (MIN(CASE WHEN s.stop_type = 'metro'
                        THEN ST_Distance(g.centroid::geography, s.geom::geography) END) - 500) / 1500.0),
                    0
                )
                + COALESCE(
                    0.35 * GREATEST(0, 1.0 - (MIN(CASE WHEN s.stop_type IN ('bus','tram','trolley')
                        THEN ST_Distance(g.centroid::geography, s.geom::geography) END) - 300) / 700.0),
                    0
                )
                + 0.25 * LEAST(
                    COUNT(CASE WHEN ST_DWithin(g.centroid::geography, s.geom::geography, 500)
                        THEN 1 END)::real / 10.0,
                    1.0
                ) AS score
            FROM grid_cells g
            LEFT JOIN transport_stops s ON ST_DWithin(g.centroid::geography, s.geom::geography, 2000)
            GROUP BY g.id
        ) sub WHERE g.id = sub.id
    """))
    session.commit()
    print("  -> transport scores done")


def _compute_parks(session):
    """Parks score: nearest park proximity (0.6) + count within 1km (0.4)."""
    print("Computing parks scores...")
    session.execute(text("""
        UPDATE grid_cells g SET score_parks = sub.score FROM (
            SELECT g.id,
                COALESCE(0.6 * GREATEST(0, 1.0 - MIN(ST_Distance(g.centroid::geography, p.geom::geography)) / 1500.0), 0)
                + 0.4 * LEAST(
                    COUNT(CASE WHEN ST_DWithin(g.centroid::geography, p.geom::geography, 1000) THEN 1 END)::real / 5.0,
                    1.0
                ) AS score
            FROM grid_cells g
            LEFT JOIN pois p ON p.category = 'park' AND ST_DWithin(g.centroid::geography, p.geom::geography, 2000)
            GROUP BY g.id
        ) sub WHERE g.id = sub.id
    """))
    session.commit()
    print("  -> parks scores done")


def _compute_education(session):
    """Education score: nearest kindergarten (0.35) + nearest school (0.35) + count within 1km (0.3)."""
    print("Computing education scores...")
    session.execute(text("""
        UPDATE grid_cells g SET score_education = sub.score FROM (
            SELECT g.id,
                COALESCE(0.35 * GREATEST(0, 1.0 - MIN(CASE WHEN p.category = 'kindergarten'
                    THEN ST_Distance(g.centroid::geography, p.geom::geography) END) / 1500.0), 0)
                + COALESCE(0.35 * GREATEST(0, 1.0 - MIN(CASE WHEN p.category = 'school'
                    THEN ST_Distance(g.centroid::geography, p.geom::geography) END) / 1500.0), 0)
                + 0.3 * LEAST(
                    COUNT(CASE WHEN p.category IN ('kindergarten','school')
                        AND ST_DWithin(g.centroid::geography, p.geom::geography, 1000) THEN 1 END)::real / 5.0,
                    1.0
                ) AS score
            FROM grid_cells g
            LEFT JOIN pois p ON p.category IN ('kindergarten','school')
                AND ST_DWithin(g.centroid::geography, p.geom::geography, 2000)
            GROUP BY g.id
        ) sub WHERE g.id = sub.id
    """))
    session.commit()
    print("  -> education scores done")


def _compute_air_quality(session):
    """Air quality score: IDW interpolation from nearest samples. Lower AQI = better."""
    print("Computing air quality scores...")
    # Use a lateral join to get 5 nearest samples per cell
    session.execute(text("""
        UPDATE grid_cells g SET score_air_quality = sub.score FROM (
            SELECT g.id,
                CASE WHEN agg.weighted_aqi IS NOT NULL
                    THEN GREATEST(0, LEAST(1.0, 1.0 - agg.weighted_aqi / 100.0))
                    ELSE 0.5
                END AS score
            FROM grid_cells g
            LEFT JOIN LATERAL (
                SELECT
                    SUM(nearest.aqi_avg / GREATEST(nearest.dist, 1))
                    / SUM(1.0 / GREATEST(nearest.dist, 1))
                    AS weighted_aqi
                FROM (
                    SELECT a.aqi_avg,
                           ST_Distance(g.centroid::geography, a.geom::geography) AS dist
                    FROM air_quality_samples a
                    WHERE ST_DWithin(g.centroid::geography, a.geom::geography, 5000)
                    ORDER BY g.centroid::geography <-> a.geom::geography
                    LIMIT 5
                ) nearest
            ) agg ON TRUE
        ) sub WHERE g.id = sub.id
    """))
    session.commit()
    print("  -> air quality scores done")


def _compute_noise(session):
    """Noise score: inverse proximity to major roads. Farther = quieter = better."""
    print("Computing noise scores...")
    session.execute(text("""
        UPDATE grid_cells g SET score_noise = sub.score FROM (
            SELECT g.id,
                CASE
                    WHEN MIN(ST_Distance(g.centroid::geography, r.geom::geography)) IS NULL THEN 1.0
                    WHEN MIN(ST_Distance(g.centroid::geography, r.geom::geography)) < 30 THEN 0.1
                    WHEN MIN(ST_Distance(g.centroid::geography, r.geom::geography)) > 500 THEN 1.0
                    ELSE MIN(ST_Distance(g.centroid::geography, r.geom::geography)) / 500.0
                END AS score
            FROM grid_cells g
            LEFT JOIN major_roads r ON ST_DWithin(g.centroid::geography, r.geom::geography, 1000)
            GROUP BY g.id
        ) sub WHERE g.id = sub.id
    """))
    session.commit()
    print("  -> noise scores done")


def _compute_shopping(session):
    """Shopping score: nearest supermarket proximity (0.6) + count within 1km (0.4)."""
    print("Computing shopping scores...")
    session.execute(text("""
        UPDATE grid_cells g SET score_shopping = sub.score FROM (
            SELECT g.id,
                COALESCE(0.6 * GREATEST(0, 1.0 - MIN(ST_Distance(g.centroid::geography, p.geom::geography)) / 1500.0), 0)
                + 0.4 * LEAST(
                    COUNT(CASE WHEN ST_DWithin(g.centroid::geography, p.geom::geography, 1000) THEN 1 END)::real / 5.0,
                    1.0
                ) AS score
            FROM grid_cells g
            LEFT JOIN pois p ON p.category = 'supermarket' AND ST_DWithin(g.centroid::geography, p.geom::geography, 2000)
            GROUP BY g.id
        ) sub WHERE g.id = sub.id
    """))
    session.commit()
    print("  -> shopping scores done")


def _compute_healthcare(session):
    """Healthcare score: nearest hospital (0.5) + nearest pharmacy (0.5)."""
    print("Computing healthcare scores...")
    session.execute(text("""
        UPDATE grid_cells g SET score_healthcare = sub.score FROM (
            SELECT g.id,
                COALESCE(0.5 * GREATEST(0, 1.0 - MIN(CASE WHEN p.category = 'hospital'
                    THEN ST_Distance(g.centroid::geography, p.geom::geography) END) / 5000.0), 0)
                + COALESCE(0.5 * GREATEST(0, 1.0 - MIN(CASE WHEN p.category = 'pharmacy'
                    THEN ST_Distance(g.centroid::geography, p.geom::geography) END) / 2000.0), 0)
                AS score
            FROM grid_cells g
            LEFT JOIN pois p ON p.category IN ('hospital','pharmacy')
                AND ST_DWithin(g.centroid::geography, p.geom::geography, 5000)
            GROUP BY g.id
        ) sub WHERE g.id = sub.id
    """))
    session.commit()
    print("  -> healthcare scores done")


def _compute_commute(session):
    """Commute score: haversine distance to Sofia city center (NDK area)."""
    print("Computing commute scores...")
    # Sofia center: 42.6977, 23.3219 (NDK/Serdika)
    session.execute(text("""
        UPDATE grid_cells g SET score_commute =
            CASE
                WHEN ST_Distance(g.centroid::geography, ST_SetSRID(ST_MakePoint(23.3219, 42.6977), 4326)::geography) < 2000
                    THEN 1.0
                ELSE GREATEST(0, 1.0 -
                    (ST_Distance(g.centroid::geography, ST_SetSRID(ST_MakePoint(23.3219, 42.6977), 4326)::geography) - 2000)
                    / 13000.0)
            END
    """))
    session.commit()
    print("  -> commute scores done")


def _compute_playground(session):
    """Playground score: nearest playground proximity (0.6) + count within 500m (0.4)."""
    print("Computing playground scores...")
    session.execute(text("""
        UPDATE grid_cells g SET score_playground = sub.score FROM (
            SELECT g.id,
                COALESCE(0.6 * GREATEST(0, 1.0 - MIN(ST_Distance(g.centroid::geography, p.geom::geography)) / 1000.0), 0)
                + 0.4 * LEAST(
                    COUNT(CASE WHEN ST_DWithin(g.centroid::geography, p.geom::geography, 500) THEN 1 END)::real / 3.0,
                    1.0
                ) AS score
            FROM grid_cells g
            LEFT JOIN pois p ON p.category = 'playground' AND ST_DWithin(g.centroid::geography, p.geom::geography, 1500)
            GROUP BY g.id
        ) sub WHERE g.id = sub.id
    """))
    session.commit()
    print("  -> playground scores done")


if __name__ == "__main__":
    compute_all_scores()
