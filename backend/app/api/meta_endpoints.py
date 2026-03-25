from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

router = APIRouter(prefix="/meta", tags=["meta"])

CATEGORIES = [
    {"key": "transport", "label": "Metro & Public Transport", "label_bg": "Метро и транспорт", "default_weight": 5, "icon": "bus"},
    {"key": "parks", "label": "Parks & Green Spaces", "label_bg": "Паркове и зеленина", "default_weight": 4, "icon": "tree"},
    {"key": "education", "label": "Kindergartens & Schools", "label_bg": "Детски градини и училища", "default_weight": 4, "icon": "school"},
    {"key": "playground", "label": "Playgrounds", "label_bg": "Детски площадки", "default_weight": 2, "icon": "playground"},
    {"key": "air_quality", "label": "Air Quality", "label_bg": "Качество на въздуха", "default_weight": 3, "icon": "wind"},
]


@router.get("/categories")
async def get_categories():
    return {"categories": CATEGORIES}


@router.get("/bounds")
async def get_bounds(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT COUNT(*) FROM grid_cells"))
    total = result.scalar()

    return {
        "bbox": [settings.sofia_west, settings.sofia_south, settings.sofia_east, settings.sofia_north],
        "center": [23.3219, 42.6977],
        "cell_size_m": settings.cell_size_m,
        "total_cells": total,
    }
