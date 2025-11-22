#!/bin/bash
# Build script for GraphRAG Docker image

set -e

echo "🐳 Building GraphRAG Docker image..."

# Build the image
docker build -t graphrag:latest .

echo "✅ Docker image built successfully!"
echo ""
echo "To run the container:"
echo "  docker run -p 8000:8000 -e OPENAI_API_KEY=your_key -e NEO4J_URI=bolt://host.docker.internal:7687 graphrag:latest"
echo ""
echo "Or use docker-compose:"
echo "  docker-compose up -d"

