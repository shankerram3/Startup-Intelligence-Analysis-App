#!/bin/bash
# Push GraphRAG Docker image to Docker Hub
# Automatically detects image name from docker-compose or running container

set -e

# Configuration
REGISTRY="docker.io"
IMAGE_NAME="${IMAGE_NAME:-graphrag}"
TAG="${TAG:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Detect docker compose command
detect_docker_compose() {
    if docker compose version &> /dev/null; then
        echo "docker compose"
        return
    fi
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
        return
    fi
    echo "docker compose"
}

DOCKER_COMPOSE=$(detect_docker_compose)

# Detect source image name
detect_source_image() {
    # Try to get image from running container
    if docker ps --format '{{.Names}}' | grep -q "^graphrag-api$"; then
        SOURCE_IMAGE=$(docker inspect --format='{{.Config.Image}}' "graphrag-api" 2>/dev/null || true)
        if [ -n "$SOURCE_IMAGE" ] && [ "$SOURCE_IMAGE" != "<no value>" ]; then
            # If image doesn't have a tag, try to find it with :latest
            if [[ "$SOURCE_IMAGE" != *":"* ]]; then
                # Check if :latest version exists
                if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${SOURCE_IMAGE}:latest$"; then
                    echo "${SOURCE_IMAGE}:latest"
                    return
                else
                    # Try to find any tag for this image
                    FOUND_IMAGE=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "^${SOURCE_IMAGE}:" | head -1)
                    if [ -n "$FOUND_IMAGE" ]; then
                        echo "$FOUND_IMAGE"
                        return
                    fi
                fi
            else
                # Image has a tag, check if it exists
                if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${SOURCE_IMAGE}$"; then
                    echo "$SOURCE_IMAGE"
                    return
                fi
            fi
        fi
    fi
    
    # Try to get from docker compose
    if $DOCKER_COMPOSE config &> /dev/null; then
        # Get project name
        PROJECT_NAME=$($DOCKER_COMPOSE config 2>/dev/null | grep -m 1 "name:" | awk '{print $2}' | tr -d '"' || echo "")
        if [ -z "$PROJECT_NAME" ]; then
            # Fallback: use directory name
            PROJECT_NAME=$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g')
        fi
        
        # Try with :latest first
        COMPOSE_IMAGE="${PROJECT_NAME}-graphrag-api:latest"
        if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${COMPOSE_IMAGE}$"; then
            echo "$COMPOSE_IMAGE"
            return
        fi
        
        # Try without tag (will add :latest later if found)
        COMPOSE_IMAGE_NO_TAG="${PROJECT_NAME}-graphrag-api"
        if docker images --format "{{.Repository}}" | grep -q "^${COMPOSE_IMAGE_NO_TAG}$"; then
            # Find the actual tag
            FOUND_TAG=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "^${COMPOSE_IMAGE_NO_TAG}:" | head -1)
            if [ -n "$FOUND_TAG" ]; then
                echo "$FOUND_TAG"
                return
            fi
        fi
    fi
    
    # Try common image names
    for img in "graphrag:latest" "graphrag:amd64" "startup-intelligence-analysis-app-graphrag-api:latest"; do
        if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${img}$"; then
            echo "$img"
            return
        fi
    done
    
    # Return empty if nothing found
    echo ""
}

echo "🐳 Docker Hub Push Script"
echo "========================"
echo ""

# Detect source image
log_info "Detecting source Docker image..."
SOURCE_IMAGE=$(detect_source_image)

if [ -z "$SOURCE_IMAGE" ]; then
    log_error "Could not detect source image automatically"
    echo ""
    log_info "Available images:"
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | head -10
    echo ""
    log_info "Please specify source image:"
    echo "  export SOURCE_IMAGE=your-image-name:tag"
    echo "  ./scripts/push-to-dockerhub.sh"
    echo ""
    log_info "Or build the image first:"
    echo "  docker-compose build graphrag-api"
    exit 1
fi

log_success "Found source image: $SOURCE_IMAGE"

# Verify image exists (check without tag too, in case tag is missing)
IMAGE_EXISTS=false
if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${SOURCE_IMAGE}$"; then
    IMAGE_EXISTS=true
elif [[ "$SOURCE_IMAGE" == *":"* ]]; then
    # Image has tag but not found, try without tag
    IMAGE_NO_TAG="${SOURCE_IMAGE%%:*}"
    if docker images --format "{{.Repository}}" | grep -q "^${IMAGE_NO_TAG}$"; then
        # Found image without tag, try to get the actual tag
        FOUND_IMAGE=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "^${IMAGE_NO_TAG}:" | head -1)
        if [ -n "$FOUND_IMAGE" ]; then
            SOURCE_IMAGE="$FOUND_IMAGE"
            IMAGE_EXISTS=true
            log_info "Using image with actual tag: $SOURCE_IMAGE"
        fi
    fi
fi

if [ "$IMAGE_EXISTS" = false ]; then
    log_error "Source image '$SOURCE_IMAGE' not found!"
    echo ""
    log_info "Available images:"
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | head -10
    exit 1
fi

echo ""
log_info "Step 1: Docker Hub Configuration"

# Get Docker Hub username
if [ -z "$DOCKER_USERNAME" ]; then
    log_warning "DOCKER_USERNAME not set"
    echo ""
    read -p "Enter your Docker Hub username: " DOCKER_USERNAME
    if [ -z "$DOCKER_USERNAME" ]; then
        log_error "Username is required!"
        exit 1
    fi
else
    log_success "Docker Hub username: $DOCKER_USERNAME"
fi

# Build full image name
FULL_IMAGE_NAME="${DOCKER_USERNAME}/${IMAGE_NAME}:${TAG}"

echo ""
log_info "Configuration:"
log_info "  Source image: $SOURCE_IMAGE"
log_info "  Target image: $FULL_IMAGE_NAME"
log_info "  Registry: $REGISTRY (Docker Hub)"
echo ""

# Get image size
IMAGE_SIZE=$(docker images --format "{{.Size}}" "$SOURCE_IMAGE" | head -1)
log_info "Image size: $IMAGE_SIZE"
echo ""

read -p "Continue with push? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_warning "Cancelled."
    exit 0
fi

echo ""
log_info "Step 2: Tagging image..."
docker tag "$SOURCE_IMAGE" "$FULL_IMAGE_NAME"
log_success "Image tagged: $FULL_IMAGE_NAME"
echo ""

log_info "Step 3: Docker Hub Login..."

# Check if already logged in
if docker info 2>/dev/null | grep -q "Username"; then
    CURRENT_USER=$(docker info 2>/dev/null | grep "Username" | awk '{print $2}' || echo "")
    if [ "$CURRENT_USER" = "$DOCKER_USERNAME" ]; then
        log_success "Already logged in as $DOCKER_USERNAME"
    else
        log_warning "Logged in as different user: $CURRENT_USER"
        log_info "Logging in as $DOCKER_USERNAME..."
        docker login
    fi
else
    log_info "Not logged in to Docker Hub"
    log_info "Please log in:"
    docker login
fi

echo ""
log_info "Step 4: Pushing to Docker Hub..."
log_warning "This may take several minutes depending on image size and connection speed..."
echo ""

if docker push "$FULL_IMAGE_NAME"; then
    echo ""
    log_success "✓ Successfully pushed to Docker Hub!"
    echo ""
    log_info "Image URL: https://hub.docker.com/r/${DOCKER_USERNAME}/${IMAGE_NAME}/tags"
    echo ""
    log_info "Others can pull it with:"
    echo "  docker pull $FULL_IMAGE_NAME"
    echo ""
    log_info "Run it with:"
    echo "  docker run -d --name graphrag-api \\"
    echo "    -p 8000:8000 \\"
    echo "    --env-file .env \\"
    echo "    -v \$(pwd)/data:/app/data \\"
    echo "    -v \$(pwd)/logs:/app/logs \\"
    echo "    $FULL_IMAGE_NAME"
    echo ""
else
    log_error "Failed to push image"
    exit 1
fi

