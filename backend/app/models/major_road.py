from sqlalchemy import Column, Integer, BigInteger, String
from geoalchemy2 import Geometry

from app.database import Base


class MajorRoad(Base):
    __tablename__ = "major_roads"

    id = Column(Integer, primary_key=True)
    osm_id = Column(BigInteger)
    road_type = Column(String(30))
    name = Column(String(255))
    geom = Column(Geometry("LINESTRING", srid=4326), nullable=False, index=True)
