cd ~/Desktop/VideoEnhancer

cat > scripts/photo_background.sh <<'EOF'
#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR" || exit 1

INPUT="${1:-$PROJECT_DIR/data/input/photos/test.jpg}"
RETURN_MASK="${2:-false}"

echo "=========================================="
echo "       REMOVE BACKGROUND"
echo "=========================================="
echo
echo "Файл: $INPUT"
echo

if [ ! -f "$INPUT" ]; then
    echo "❌ Файл не найден:"
    echo "$INPUT"
    exit 1
fi

RESPONSE=$(curl -s -X POST \
    "http://127.0.0.1:8000/api/photo/remove-background?return_mask=$RETURN_MASK" \
    -F "file=@$INPUT")

JOB_ID=$(echo "$RESPONSE" | sed -n 's/.*"job_id":"\([^"]*\)".*/\1/p')

if [ -z "$JOB_ID" ]; then
    echo "❌ Не удалось создать задачу"
    echo "$RESPONSE"
    exit 1
fi

echo "Job ID: $JOB_ID"
echo
echo "Удаляем фон..."

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
            echo "✓ ФОН УДАЛЁН"
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
            echo "❌ ОШИБКА"
            echo "$STATUS"
            exit 1
            ;;
    esac

    sleep 2
done
EOF