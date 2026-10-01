#!/bin/sh
set -e

echo "Starting FastAPI server..."
# We use uvicorn to run the app. It binds to the PORT environment variable 
# (which Render sets automatically) or defaults to 8000.
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
