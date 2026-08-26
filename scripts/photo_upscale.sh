#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR" || exit 1

INPUT="${1:-$PROJECT_DIR/data/input/photos/test.jpg}"
SCALE="${2:-2}"
FACE_ENHANCE="${3:-false}"

echo "=========================================="
echo "       PHOTO UPSCALE"
echo "=========================================="
echo
echo "Файл:          $INPUT"
echo "Масштаб:       ${SCALE}x"
echo "Face Enhance:  $FACE_ENHANCE"
echo

if [ ! -f "$INPUT" ]; then
    echo "❌ Файл не найден:"
    echo "$INPUT"
    exit 1
fi

RESPONSE=$(curl -s -X POST \
    "http://127.0.0.1:8000/api/photo/upscale?scale=$SCALE&face_enhance=$FACE_ENHANCE" \
    -F "file=@$INPUT")

JOB_ID=$(echo "$RESPONSE" | sed -n 's/.*"job_id":"\([^"]*\)".*/\1/p')

if [ -z "$JOB_ID" ]; then
    echo "❌ Не удалось создать задачу"
    echo "$RESPONSE"
    exit 1
fi

echo "Job ID: $JOB_ID"
echo
echo "Обработка..."

while true; do
    STATUS=$(curl -s "http://127.0.0.1:8000/api/jobs/$JOB_ID")

    JOB_STATUS=$(echo "$STATUS" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
    PROGRESS=$(echo "$STATUS" | sed -n 's/.*"progress":\([^,}]*\).*/\1/p')

    printf "\rСтатус: %-10s Прогресс: %-6s%%" "$JOB_STATUS" "$PROGRESS"

    case "$JOB_STATUS" in
        success)
            echo
            echo
            echo "=========================================="
            echo "✓ UPSCALE ЗАВЕРШЁН"
            echo "=========================================="
            echo

            RESULT=$(echo "$STATUS" | sed -n 's/.*"result_path":"\([^"]*\)".*/\1/p')

            echo "Результат:"
            echo "$RESULT"
            echo
            ls -lh "$RESULT" 2>/dev/null
            echo
            exit 0
            ;;

        failed)
            echo
            echo
            echo "=========================================="
            echo "❌ ОШИБКА"
            echo "=========================================="
            echo
            echo "$STATUS"
            exit 1
            ;;
    esac

    sleep 2
done
