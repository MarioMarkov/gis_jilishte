from sqlalchemy import Column, Integer, Float, DateTime, func
from geoalchemy2 import Geometry

from app.database import Base


class AirQualitySample(Base):
    __tablename__ = "air_quality_samples"

    id = Column(Integer, primary_key=True)
    geom = Column(Geometry("POINT", srid=4326), nullable=False, index=True)
    pm25_avg = Column(Float)
    pm10_avg = Column(Float)
    aqi_avg = Column(Float)
    sampled_at = Column(DateTime(timezone=True), server_default=func.now())
