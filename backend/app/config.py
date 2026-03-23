from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://gis:gis@localhost:5432/jilishte"
    database_url_sync: str = "postgresql://gis:gis@localhost:5432/jilishte"
    # Sofia bounding box
    sofia_south: float = 42.62
    sofia_north: float = 42.77
    sofia_west: float = 23.22
    sofia_east: float = 23.47

    # Grid cell size in meters
    cell_size_m: int = 200

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
