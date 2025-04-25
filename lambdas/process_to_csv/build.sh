#!/bin/bash

set -e

# resolve absolute paths
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(realpath "$SCRIPT_DIR/../..")"
ZIP_FILE="$SCRIPT_DIR/lambda_package.zip"

echo "Cleaning previous zip..."
rm -f "$ZIP_FILE"

echo "Building Lambda package in Docker..."

docker run --rm \
  --entrypoint /bin/bash \
  -v "$ROOT_DIR":/app \
  -w /app/lambdas/process_to_csv \
  public.ecr.aws/lambda/python:3.11 \
  -c "
    yum install -y zip > /dev/null &&
    rm -rf build && mkdir -p build/python/shared &&
    pip install --no-cache-dir -q -r requirements.txt -t build/python &&
    cp main.py build/python/ &&
    cp /app/shared/*.py build/python/shared/ &&
    cd build/python && zip -r9 ../../lambda_package.zip . && cd ../..
  "


echo "✅ Done: $ZIP_FILE"
