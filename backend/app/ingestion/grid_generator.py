"""Generate a grid of 200m cells covering Sofia."""

import math
from sqlalchemy import text
from app.config import settings
from app.database import SyncSession


def generate_grid():
    lat_step = settings.cell_size_m / 111_320
    lon_step = settings.cell_size_m / (111_320 * math.cos(math.radians(
        (settings.sofia_south + settings.sofia_north) / 2
    )))

    n_rows = int((settings.sofia_north - settings.sofia_south) / lat_step)
    n_cols = int((settings.sofia_east - settings.sofia_west) / lon_step)

    print(f"Generating grid: {n_rows} rows x {n_cols} cols = {n_rows * n_cols} cells")
    print(f"Cell size: {lat_step:.6f} lat x {lon_step:.6f} lon degrees")

    session = SyncSession()
    try:
        session.execute(text("TRUNCATE grid_cells RESTART IDENTITY;"))

        batch = []
        for r in range(n_rows):
            for c in range(n_cols):
                clat = settings.sofia_south + (r + 0.5) * lat_step
                clon = settings.sofia_west + (c + 0.5) * lon_step

                half_lat = lat_step / 2
                half_lon = lon_step / 2

                wkt_point = f"SRID=4326;POINT({clon} {clat})"
                wkt_poly = (
                    f"SRID=4326;POLYGON(("
                    f"{clon - half_lon} {clat - half_lat},"
                    f"{clon + half_lon} {clat - half_lat},"
                    f"{clon + half_lon} {clat + half_lat},"
                    f"{clon - half_lon} {clat + half_lat},"
                    f"{clon - half_lon} {clat - half_lat}"
                    f"))"
                )

                batch.append({
                    "row_idx": r, "col_idx": c,
                    "centroid": wkt_point, "boundary": wkt_poly,
                })

                if len(batch) >= 1000:
                    session.execute(
                        text(
                            "INSERT INTO grid_cells (row_idx, col_idx, centroid, boundary) "
                            "VALUES (:row_idx, :col_idx, :centroid, :boundary)"
                        ),
                        batch,
                    )
                    batch.clear()

        if batch:
            session.execute(
                text(
                    "INSERT INTO grid_cells (row_idx, col_idx, centroid, boundary) "
                    "VALUES (:row_idx, :col_idx, :centroid, :boundary)"
                ),
                batch,
            )

        session.commit()
        total = session.execute(text("SELECT COUNT(*) FROM grid_cells")).scalar()
        print(f"Generated {total} grid cells")
    finally:
        session.close()


if __name__ == "__main__":
    generate_grid()
