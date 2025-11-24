#!/bin/bash
# Script to commit container and push to Docker registry

set -e

CONTAINER_NAME="graphrag-api"
REGISTRY="${DOCKER_REGISTRY:-docker.io}"  # Default to Docker Hub
USERNAME="${DOCKER_USERNAME:-}"
IMAGE_NAME="${IMAGE_NAME:-graphrag}"
TAG="${TAG:-with-data}"

echo "🐳 Preparing to push container to Docker registry"
echo ""

# Check if container exists
if ! docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "❌ Container '$CONTAINER_NAME' not found!"
    echo "   Start it first: docker-compose up -d"
    exit 1
fi

# Check if username is set
if [ -z "$USERNAME" ]; then
    echo "⚠️  DOCKER_USERNAME not set!"
    echo ""
    echo "Set it with:"
    echo "  export DOCKER_USERNAME=your-username"
    echo ""
    echo "Or edit this script to set USERNAME variable"
    read -p "Enter your Docker Hub username: " USERNAME
    if [ -z "$USERNAME" ]; then
        echo "❌ Username required!"
        exit 1
    fi
fi

# Full image name
if [ "$REGISTRY" = "docker.io" ]; then
    FULL_IMAGE_NAME="${USERNAME}/${IMAGE_NAME}:${TAG}"
else
    FULL_IMAGE_NAME="${REGISTRY}/${USERNAME}/${IMAGE_NAME}:${TAG}"
fi

echo "Container: $CONTAINER_NAME"
echo "Registry: $REGISTRY"
echo "Image: $FULL_IMAGE_NAME"
echo ""
echo "⚠️  WARNING: This will include ALL data in the container!"
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

echo ""
echo "📦 Step 1: Committing container to image..."
docker commit $CONTAINER_NAME $FULL_IMAGE_NAME

echo "✅ Image created: $FULL_IMAGE_NAME"
echo ""

# Check if logged in
echo "📋 Step 2: Checking Docker login..."
if ! docker info | grep -q "Username"; then
    echo "⚠️  Not logged in to Docker registry"
    echo "   Log in with: docker login"
    read -p "Login now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker login $REGISTRY
    else
        echo "❌ Please login first: docker login"
        exit 1
    fi
fi

echo ""
echo "📤 Step 3: Pushing to registry..."
echo "   This may take several minutes (image is ~4.5GB+)..."
docker push $FULL_IMAGE_NAME

echo ""
echo "✅ Successfully pushed: $FULL_IMAGE_NAME"
echo ""
echo "Others can pull it with:"
echo "  docker pull $FULL_IMAGE_NAME"
echo ""
echo "And run it with:"
echo "  docker run -p 8000:8000 \\"
echo "    -e OPENAI_API_KEY=their_key \\"
echo "    -e NEO4J_URI=bolt://their-neo4j:7687 \\"
echo "    $FULL_IMAGE_NAME"

