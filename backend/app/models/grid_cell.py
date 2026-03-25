from sqlalchemy import Column, Integer, SmallInteger, Float, UniqueConstraint
from geoalchemy2 import Geometry

from app.database import Base


class GridCell(Base):
    __tablename__ = "grid_cells"

    id = Column(Integer, primary_key=True)
    row_idx = Column(SmallInteger, nullable=False)
    col_idx = Column(SmallInteger, nullable=False)
    centroid = Column(Geometry("POINT", srid=4326), nullable=False)
    boundary = Column(Geometry("POLYGON", srid=4326), nullable=False)

    score_transport = Column(Float)
    score_parks = Column(Float)
    score_education = Column(Float)
    score_air_quality = Column(Float)
    score_noise = Column(Float)
    score_shopping = Column(Float)
    score_healthcare = Column(Float)
    score_commute = Column(Float)
    score_playground = Column(Float)

    __table_args__ = (UniqueConstraint("row_idx", "col_idx"),)
