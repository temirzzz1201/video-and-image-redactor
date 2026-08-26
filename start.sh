#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$PROJECT_DIR/data/run"

mkdir -p "$PID_DIR"

cd "$PROJECT_DIR" || exit 1

echo "=========================================="
echo "       VideoEnhancer START"
echo "=========================================="

# -------------------------------------------------
# Virtual environment
# -------------------------------------------------

if [ ! -f "$PROJECT_DIR/venv/bin/activate" ]; then
    echo "❌ venv не найден"
    exit 1
fi

source "$PROJECT_DIR/venv/bin/activate"

echo "Python: $(which python)"

# -------------------------------------------------
# Redis
# -------------------------------------------------

if redis-cli ping >/dev/null 2>&1; then
    echo "Redis:   RUNNING"
else
    echo "❌ Redis не запущен"
    echo "Запусти: sudo systemctl start redis-server"
    exit 1
fi

# -------------------------------------------------
# Проверка старых процессов
# -------------------------------------------------

if [ -f "$PID_DIR/celery.pid" ]; then
    OLD_PID=$(cat "$PID_DIR/celery.pid")

    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "Celery уже запущен: PID $OLD_PID"
    else
        rm -f "$PID_DIR/celery.pid"
    fi
fi

if [ -f "$PID_DIR/uvicorn.pid" ]; then
    OLD_PID=$(cat "$PID_DIR/uvicorn.pid")

    if kill -0 "$OLD_PID" 2>/dev/null; then
        echo "FastAPI уже запущен: PID $OLD_PID"
    else
        rm -f "$PID_DIR/uvicorn.pid"
    fi
fi

# -------------------------------------------------
# Celery
# -------------------------------------------------

if [ ! -f "$PID_DIR/celery.pid" ]; then

    echo
    echo "Запускаем Celery..."

    celery -A app.workers.celery_app worker \
        --loglevel=info \
        --pool=solo \
        > "$PROJECT_DIR/data/run/celery.log" 2>&1 &

    CELERY_PID=$!

    echo "$CELERY_PID" > "$PID_DIR/celery.pid"

    sleep 3

    if kill -0 "$CELERY_PID" 2>/dev/null; then
        echo "Celery:  RUNNING (PID $CELERY_PID)"
    else
        echo "❌ Celery не запустился"
        rm -f "$PID_DIR/celery.pid"
        echo
        echo "Последние строки лога:"
        tail -30 "$PROJECT_DIR/data/run/celery.log"
        exit 1
    fi

fi

# -------------------------------------------------
# FastAPI
# -------------------------------------------------

if [ ! -f "$PID_DIR/uvicorn.pid" ]; then

    echo
    echo "Запускаем FastAPI..."

    uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        > "$PROJECT_DIR/data/run/uvicorn.log" 2>&1 &

    UVICORN_PID=$!

    echo "$UVICORN_PID" > "$PID_DIR/uvicorn.pid"

    sleep 3

    if kill -0 "$UVICORN_PID" 2>/dev/null; then
        echo "FastAPI: RUNNING (PID $UVICORN_PID)"
    else
        echo "❌ FastAPI не запустился"
        rm -f "$PID_DIR/uvicorn.pid"
        echo
        echo "Последние строки лога:"
        tail -30 "$PROJECT_DIR/data/run/uvicorn.log"
        exit 1
    fi

fi

echo
echo "=========================================="
echo "       VideoEnhancer ЗАПУЩЕН"
echo "=========================================="
echo
echo "API:     http://127.0.0.1:8000"
echo "Swagger: http://127.0.0.1:8000/docs"
echo
echo "Проверка:"
echo "  ./status.sh"
echo
echo "Остановка:"
echo "  ./stop.sh"
echo
