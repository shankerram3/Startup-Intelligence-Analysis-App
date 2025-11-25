#!/bin/bash
# Build script for GraphRAG Docker image optimized for AMD architecture
# This script ensures CPU-only dependencies and avoids CUDA/GPU packages

set -e

echo "🐳 Building GraphRAG Docker image for AMD architecture..."
echo ""

# Detect platform (AMD64/linux/amd64)
PLATFORM="${DOCKER_PLATFORM:-linux/amd64}"

echo "Platform: $PLATFORM"
echo ""

# Build the image with explicit platform specification
# This ensures compatibility with AMD APP platform
docker build \
    --platform $PLATFORM \
    --tag graphrag:latest \
    --tag graphrag:amd64 \
    .

echo ""
echo "✅ Docker image built successfully for AMD architecture!"
echo ""
echo "Image details:"
docker images graphrag:latest --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
echo ""
echo "To run the container:"
echo "  docker run -p 8000:8000 -e OPENAI_API_KEY=your_key -e NEO4J_URI=bolt://host.docker.internal:7687 graphrag:latest"
echo ""
echo "Or use docker-compose:"
echo "  docker-compose up -d"
echo ""
echo "Note: This build uses CPU-only PyTorch to avoid CUDA dependencies on AMD."

