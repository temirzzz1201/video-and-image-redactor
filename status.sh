#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$PROJECT_DIR/data/run"

echo "=========================================="
echo "       VideoEnhancer STATUS"
echo "=========================================="

# Redis
if redis-cli ping >/dev/null 2>&1; then
    echo "Redis:   RUNNING"
else
    echo "Redis:   STOPPED"
fi

# Celery
CELERY_PID=$(pgrep -f "celery.*app.workers.celery_app" | head -n 1)

if [ -n "$CELERY_PID" ]; then
    echo "Celery:  RUNNING (PID $CELERY_PID)"
else
    echo "Celery:  STOPPED"
fi

# FastAPI / Uvicorn
UVICORN_PID=$(pgrep -f "uvicorn app.main:app" | head -n 1)

if [ -n "$UVICORN_PID" ]; then
    echo "FastAPI: RUNNING (PID $UVICORN_PID)"
else
    echo "FastAPI: STOPPED"
fi

echo

# API
if curl -s --max-time 2 http://127.0.0.1:8000/health >/dev/null 2>&1; then
    echo "API:     OK"
    curl -s http://127.0.0.1:8000/health
    echo
else
    echo "API:     NOT AVAILABLE"
fi

echo "=========================================="