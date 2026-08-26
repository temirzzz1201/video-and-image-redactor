#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$PROJECT_DIR/data/run"

echo "=========================================="
echo "       VideoEnhancer STOP"
echo "=========================================="

stop_process() {
    local name="$1"
    local pidfile="$2"

    if [ ! -f "$pidfile" ]; then
        echo "$name: NOT RUNNING"
        return
    fi

    PID=$(cat "$pidfile")

    if kill -0 "$PID" 2>/dev/null; then
        echo "Останавливаем $name (PID $PID)..."
        kill "$PID"

        sleep 2

        if kill -0 "$PID" 2>/dev/null; then
            echo "$name не остановился, отправляем SIGKILL"
            kill -9 "$PID" 2>/dev/null || true
        fi

        echo "$name: STOPPED"
    else
        echo "$name: уже остановлен"
    fi

    rm -f "$pidfile"
}

stop_process "Celery" "$PID_DIR/celery.pid"
stop_process "FastAPI" "$PID_DIR/uvicorn.pid"

echo
echo "✓ VideoEnhancer остановлен"
