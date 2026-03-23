"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-23
"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    op.create_table(
        "grid_cells",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("row_idx", sa.SmallInteger, nullable=False),
        sa.Column("col_idx", sa.SmallInteger, nullable=False),
        sa.Column("centroid", geoalchemy2.Geometry("POINT", srid=4326, spatial_index=False), nullable=False),
        sa.Column("boundary", geoalchemy2.Geometry("POLYGON", srid=4326, spatial_index=False), nullable=False),
        sa.Column("score_transport", sa.Float),
        sa.Column("score_parks", sa.Float),
        sa.Column("score_education", sa.Float),
        sa.Column("score_air_quality", sa.Float),
        sa.Column("score_noise", sa.Float),
        sa.Column("score_shopping", sa.Float),
        sa.Column("score_healthcare", sa.Float),
        sa.Column("score_commute", sa.Float),
        sa.UniqueConstraint("row_idx", "col_idx"),
    )
    op.create_index("idx_grid_cells_centroid", "grid_cells", ["centroid"], postgresql_using="gist")
    op.create_index("idx_grid_cells_boundary", "grid_cells", ["boundary"], postgresql_using="gist")

    op.create_table(
        "pois",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("osm_id", sa.BigInteger),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("subcategory", sa.String(50)),
        sa.Column("name", sa.String(255)),
        sa.Column("geom", geoalchemy2.Geometry("POINT", srid=4326, spatial_index=False), nullable=False),
        sa.Column("tags", sa.JSON),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_pois_geom", "pois", ["geom"], postgresql_using="gist")
    op.create_index("idx_pois_category", "pois", ["category"])

    op.create_table(
        "transport_stops",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("stop_id", sa.String(50)),
        sa.Column("name", sa.String(255)),
        sa.Column("stop_type", sa.String(20), nullable=False),
        sa.Column("geom", geoalchemy2.Geometry("POINT", srid=4326, spatial_index=False), nullable=False),
        sa.Column("route_count", sa.Integer, default=0),
        sa.Column("source", sa.String(20), default="gtfs"),
    )
    op.create_index("idx_transport_stops_geom", "transport_stops", ["geom"], postgresql_using="gist")
    op.create_index("idx_transport_stops_type", "transport_stops", ["stop_type"])

    op.create_table(
        "major_roads",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("osm_id", sa.BigInteger),
        sa.Column("road_type", sa.String(30)),
        sa.Column("name", sa.String(255)),
        sa.Column("geom", geoalchemy2.Geometry("LINESTRING", srid=4326, spatial_index=False), nullable=False),
    )
    op.create_index("idx_roads_geom", "major_roads", ["geom"], postgresql_using="gist")

    op.create_table(
        "air_quality_samples",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("geom", geoalchemy2.Geometry("POINT", srid=4326, spatial_index=False), nullable=False),
        sa.Column("pm25_avg", sa.Float),
        sa.Column("pm10_avg", sa.Float),
        sa.Column("aqi_avg", sa.Float),
        sa.Column("sampled_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_aq_geom", "air_quality_samples", ["geom"], postgresql_using="gist")


def downgrade():
    op.drop_table("air_quality_samples")
    op.drop_table("major_roads")
    op.drop_table("transport_stops")
    op.drop_table("pois")
    op.drop_table("grid_cells")
