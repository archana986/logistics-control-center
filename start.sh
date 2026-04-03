#!/bin/bash
set -e

# Start the FastAPI app (serves both API and frontend)
uvicorn backend.main:app --host 0.0.0.0 --port 8000
