#!/bin/sh
set -e

echo "Waiting for database..."
until pg_isready -h db -p 5432 -U gis; do
  sleep 1
done
echo "Database is ready."

echo "Running migrations..."
alembic upgrade head

echo "Running data ingestion..."
python scripts/ingest_all.py

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
