from sqlalchemy import Column, Integer, String
from geoalchemy2 import Geometry

from app.database import Base


class TransportStop(Base):
    __tablename__ = "transport_stops"

    id = Column(Integer, primary_key=True)
    stop_id = Column(String(50))
    name = Column(String(255))
    stop_type = Column(String(20), nullable=False, index=True)
    geom = Column(Geometry("POINT", srid=4326), nullable=False, index=True)
    route_count = Column(Integer, default=0)
    source = Column(String(20), default="gtfs")
