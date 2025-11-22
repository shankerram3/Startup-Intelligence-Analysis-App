#!/bin/bash
# Script to tag and push Docker image to registry

set -e

REGISTRY="${DOCKER_REGISTRY:-docker.io}"  # Default to Docker Hub
USERNAME="${DOCKER_USERNAME:-}"
IMAGE_NAME="${IMAGE_NAME:-graphrag}"
TAG="${TAG:-latest}"
SOURCE_IMAGE="${SOURCE_IMAGE:-swmproject-graphrag-api:latest}"

echo "🐳 Preparing to push Docker image to registry"
echo ""

# Check if source image exists
if ! docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${SOURCE_IMAGE}$"; then
    echo "❌ Source image '$SOURCE_IMAGE' not found!"
    echo ""
    echo "Available images:"
    docker images | grep -E "(graphrag|swmproject)" || echo "  (none found)"
    echo ""
    echo "Build the image first:"
    echo "  docker-compose build graphrag-api"
    echo "  # OR"
    echo "  docker build -t graphrag:latest ."
    exit 1
fi

# Check if username is set
if [ -z "$USERNAME" ]; then
    echo "⚠️  DOCKER_USERNAME not set!"
    echo ""
    echo "Set it with:"
    echo "  export DOCKER_USERNAME=your-username"
    echo ""
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

echo "Source image: $SOURCE_IMAGE"
echo "Target image: $FULL_IMAGE_NAME"
echo "Registry: $REGISTRY"
echo ""

read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

echo ""
echo "📦 Step 1: Tagging image..."
docker tag $SOURCE_IMAGE $FULL_IMAGE_NAME

echo "✅ Image tagged: $FULL_IMAGE_NAME"
echo ""

# Check if logged in
echo "📋 Step 2: Checking Docker login..."
if ! docker info 2>/dev/null | grep -q "Username"; then
    echo "⚠️  Not logged in to Docker registry"
    echo "   Log in with: docker login"
    read -p "Login now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ "$REGISTRY" != "docker.io" ]; then
            docker login $REGISTRY
        else
            docker login
        fi
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

