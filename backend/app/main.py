from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.grid_endpoints import router as grid_router
from app.api.meta_endpoints import router as meta_router

app = FastAPI(
    title="Sofia Apartment Recommender",
    description="Find the best location to buy an apartment in Sofia based on GIS data",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(grid_router, prefix="/api")
app.include_router(meta_router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
