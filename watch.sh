```bash
#!/bin/bash

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR" || exit 1

echo "=========================================="
echo "       VideoEnhancer WATCH"
echo "=========================================="
echo

# Проверяем API
if ! curl -s --max-time 2 http://127.0.0.1:8000/health >/dev/null; then
    echo "❌ FastAPI не запущен"
    echo "Сначала выполни:"
    echo "  ./start.sh"
    exit 1
fi

# Находим самый свежий mp4 в output
BEFORE_FILE=$(find "$PROJECT_DIR/data/output/video" \
    -type f \
    -name "*.mp4" \
    -printf '%T@ %p\n' 2>/dev/null |
    sort -n |
    tail -1 |
    cut -d' ' -f2-)

echo "Последний результат:"
echo "  ${BEFORE_FILE:-нет файлов}"
echo

echo "Ожидаем завершения обработки..."
echo "Для остановки мониторинга: Ctrl+C"
echo

while true; do

    # Ищем новые/изменённые mp4
    CURRENT_FILE=$(find "$PROJECT_DIR/data/output/video" \
        -type f \
        -name "*.mp4" \
        -printf '%T@ %p\n' 2>/dev/null |
        sort -n |
        tail -1 |
        cut -d' ' -f2-)

    if [ -n "$CURRENT_FILE" ] && [ "$CURRENT_FILE" != "$BEFORE_FILE" ]; then

        # Проверяем, что файл перестал расти
        SIZE1=$(stat -c%s "$CURRENT_FILE" 2>/dev/null || echo 0)
        sleep 3
        SIZE2=$(stat -c%s "$CURRENT_FILE" 2>/dev/null || echo 0)

        if [ "$SIZE1" -eq "$SIZE2" ] && [ "$SIZE2" -gt 0 ]; then

            echo
            echo "=========================================="
            echo "       ✓ ВИДЕО ГОТОВО"
            echo "=========================================="
            echo
            echo "Результат:"
            echo "  $CURRENT_FILE"
            echo

            SIZE_MB=$(awk "BEGIN {printf \"%.2f\", $SIZE2/1024/1024}")

            echo "Размер:"
            echo "  ${SIZE_MB} MB"
            echo

            echo "Параметры видео:"
            ffprobe -v error \
                -show_entries stream=codec_name,width,height,r_frame_rate,bit_rate \
                -show_entries format=duration,size \
                -of default=noprint_wrappers=1 \
                "$CURRENT_FILE"

            echo
            echo "=========================================="

            exit 0
        fi
    fi

    # Показываем последние строки Celery
    if [ -f "$PROJECT_DIR/data/run/celery.log" ]; then

        LAST_PROGRESS=$(grep "Обработано кадров:" \
            "$PROJECT_DIR/data/run/celery.log" |
            tail -1)

        if [ -n "$LAST_PROGRESS" ]; then
            printf "\r%-100s" "$LAST_PROGRESS"
        fi
    fi

    sleep 2
done
```
