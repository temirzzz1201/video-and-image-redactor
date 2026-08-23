#!/usr/bin/env bash
set -e

# Запускать из корня проекта VideoEnhancer.
# Скачивает веса Real-ESRGAN и GFPGAN в нужные папки.

REALESRGAN_DIR="models/realesrgan"
GFPGAN_DIR="models/gfpgan"

mkdir -p "$REALESRGAN_DIR" "$GFPGAN_DIR"

echo "== Real-ESRGAN (x2plus) =="
if [ -f "$REALESRGAN_DIR/RealESRGAN_x2plus.pth" ]; then
    echo "Уже скачано, пропускаю."
else
    curl -L -o "$REALESRGAN_DIR/RealESRGAN_x2plus.pth" \
        "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth"
fi

echo "== GFPGAN v1.4 =="
if [ -f "$GFPGAN_DIR/GFPGANv1.4.pth" ]; then
    echo "Уже скачано, пропускаю."
else
    curl -L -o "$GFPGAN_DIR/GFPGANv1.4.pth" \
        "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth"
fi

echo
echo "Готово. Проверка размеров файлов:"
ls -lh "$REALESRGAN_DIR/RealESRGAN_x2plus.pth" "$GFPGAN_DIR/GFPGANv1.4.pth"