#!/usr/bin/env bash
set -e

if [ ! -d "venv" ]; then
    echo "Создаю виртуальное окружение..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

export PYTHONPATH=$(pwd)

echo "Запуск Celery воркера в фоне..."
celery -A app.workers.celery_app worker --loglevel=info --detach

echo "Запуск FastAPI сервера..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
