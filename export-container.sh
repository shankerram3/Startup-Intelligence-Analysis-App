#!/bin/bash
# Script to export Docker container with data

set -e

CONTAINER_NAME="graphrag-api"
EXPORT_FILE="graphrag-container-with-data.tar"

echo "📦 Exporting container: $CONTAINER_NAME"
echo "⚠️  WARNING: This will include ALL data in the container!"
echo ""

# Check if container exists
if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container '$CONTAINER_NAME' not found!"
    exit 1
fi

# Check container size
CONTAINER_SIZE=$(docker ps -a --filter "name=${CONTAINER_NAME}" --format "{{.Size}}")
echo "Container size: $CONTAINER_SIZE"
echo ""

# Export the container
echo "Exporting to: $EXPORT_FILE"
echo "This may take several minutes..."
docker export $CONTAINER_NAME > $EXPORT_FILE

# Get file size
FILE_SIZE=$(du -h $EXPORT_FILE | cut -f1)
echo ""
echo "✅ Export complete!"
echo "📁 File: $EXPORT_FILE"
echo "📊 Size: $FILE_SIZE"
echo ""
echo "To share: Upload $EXPORT_FILE to your sharing platform"
echo ""
echo "To import on another machine:"
echo "  docker import $EXPORT_FILE graphrag:with-data"
echo "  docker run -p 8000:8000 -e OPENAI_API_KEY=your_key graphrag:with-data"

