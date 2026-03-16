#!/usr/bin/env sh
set -eu

INPUT_CSS="./theme/static_src/src/styles.css"
OUTPUT_CSS="./theme/static/css/dist/styles.css"

mkdir -p "$(dirname "$OUTPUT_CSS")"

echo "==> Building Tailwind CSS"
tailwindcss -i "$INPUT_CSS" -o "$OUTPUT_CSS" --minify

echo "==> Tailwind CSS written to $OUTPUT_CSS"
