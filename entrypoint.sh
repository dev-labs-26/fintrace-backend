#!/bin/sh
set -e

# Use PORT from environment or default to 8000
PORT=${PORT:-8000}

echo "Starting Fintrace Backend on port $PORT..."

# Start uvicorn
exec uvicorn main:app --host 0.0.0.0 --port "$PORT" --workers 1
