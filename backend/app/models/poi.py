from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry

from app.database import Base


class Poi(Base):
    __tablename__ = "pois"

    id = Column(Integer, primary_key=True)
    osm_id = Column(BigInteger)
    category = Column(String(50), nullable=False, index=True)
    subcategory = Column(String(50))
    name = Column(String(255))
    geom = Column(Geometry("POINT", srid=4326), nullable=False, index=True)
    tags = Column(JSONB)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
