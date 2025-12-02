#!/bin/bash
# Build base image with dependencies pre-installed
# This image can be reused for faster application builds

set -e

IMAGE_NAME="${BASE_IMAGE_NAME:-graphrag-base}"
IMAGE_TAG="${BASE_IMAGE_TAG:-latest}"
INSTALL_PLAYWRIGHT="${INSTALL_PLAYWRIGHT:-true}"

echo "=========================================="
echo "Building Base Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "=========================================="
echo ""

# Enable BuildKit
export DOCKER_BUILDKIT=1

# Build base image
echo "Building base image with dependencies..."
echo "This may take 5-7 minutes (dependencies installation)..."
echo ""

docker build \
    -f Dockerfile.base \
    --build-arg INSTALL_PLAYWRIGHT="${INSTALL_PLAYWRIGHT}" \
    --tag "${IMAGE_NAME}:${IMAGE_TAG}" \
    --tag "${IMAGE_NAME}:latest" \
    .

echo ""
echo "✅ Base image built successfully: ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
echo "Next steps:"
echo "  1. Update Dockerfile.fast to use: FROM ${IMAGE_NAME}:${IMAGE_TAG}"
echo "  2. Build application: docker build -f Dockerfile.fast -t graphrag-api:latest ."
echo ""
echo "Or push to registry:"
echo "  docker tag ${IMAGE_NAME}:${IMAGE_TAG} your-registry/${IMAGE_NAME}:${IMAGE_TAG}"
echo "  docker push your-registry/${IMAGE_NAME}:${IMAGE_TAG}"

