#!/bin/bash
# Zero-downtime redeploy script for GraphRAG API
# Builds new image with no cache, starts new container, health checks it,
# then switches over only if new container is healthy

set -e

# Configuration
COMPOSE_FILE="docker-compose.yml"
SERVICE_NAME="graphrag-api"
CONTAINER_NAME="graphrag-api"
NEW_CONTAINER_NAME="graphrag-api-new"
HEALTH_CHECK_URL="http://localhost:8000/health"
TEMP_PORT="8001"
MAX_HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_INTERVAL=3  # seconds

# Docker Hub push configuration (optional)
# Set DOCKER_USERNAME to enable automatic push after redeploy
# Set PUSH_IMAGE=false to disable push even if DOCKER_USERNAME is set
PUSH_IMAGE="${PUSH_IMAGE:-true}"
DOCKER_USERNAME="${DOCKER_USERNAME:-}"
DOCKER_IMAGE_NAME="${DOCKER_IMAGE_NAME:-graphrag}"
DOCKER_TAG="${DOCKER_TAG:-latest}"

# Detect docker compose command first (needed for image name detection)
detect_docker_compose() {
    # Try docker compose (Docker CLI plugin - newer)
    if docker compose version &> /dev/null; then
        echo "docker compose"
        return
    fi
    # Try docker-compose (standalone - older)
    if command -v docker-compose &> /dev/null; then
        echo "docker-compose"
        return
    fi
    # If neither works, return docker compose as default (will fail with clear error)
    echo "docker compose"
}

DOCKER_COMPOSE=$(detect_docker_compose)

# Detect image name from running container or docker compose
detect_image_name() {
    # Try to get image from running container
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        IMAGE_NAME=$(docker inspect --format='{{.Config.Image}}' "$CONTAINER_NAME" | cut -d: -f1)
        if [ -n "$IMAGE_NAME" ]; then
            echo "$IMAGE_NAME"
            return
        fi
    fi
    
    # Try to get from docker compose config
    if $DOCKER_COMPOSE config &> /dev/null; then
        IMAGE_NAME=$($DOCKER_COMPOSE config 2>/dev/null | grep -A 5 "image:" | grep "$SERVICE_NAME" | head -n 1 | awk '{print $2}' | tr -d '"' || true)
        if [ -n "$IMAGE_NAME" ]; then
            echo "$IMAGE_NAME"
            return
        fi
    fi
    
    # Fallback: use project name pattern
    PROJECT_NAME=$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g')
    echo "${PROJECT_NAME}_${SERVICE_NAME}"
}

IMAGE_NAME=$(detect_image_name)

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

# Check if container is running
is_container_running() {
    docker ps --format '{{.Names}}' | grep -q "^${1}$"
}

# Check if container exists
container_exists() {
    docker ps -a --format '{{.Names}}' | grep -q "^${1}$"
}

# Health check function
health_check() {
    local url=$1
    local container_name=$2
    
    # Check if container is running
    if ! is_container_running "$container_name"; then
        return 1
    fi
    
    # Check health endpoint
    if curl -sf "$url" > /dev/null 2>&1; then
        return 0
    fi
    
    return 1
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary resources..."
    
    # Stop and remove new container if it exists
    if container_exists "$NEW_CONTAINER_NAME"; then
        log_info "Removing temporary container: $NEW_CONTAINER_NAME"
        docker stop "$NEW_CONTAINER_NAME" 2>/dev/null || true
        docker rm "$NEW_CONTAINER_NAME" 2>/dev/null || true
    fi
    
    # Remove temporary image if it exists
    if docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^${IMAGE_NAME}:new$"; then
        log_info "Removing temporary image: ${IMAGE_NAME}:new"
        docker rmi "${IMAGE_NAME}:new" 2>/dev/null || true
    fi
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

# Main deployment script
main() {
    log_info "Starting zero-downtime redeployment..."
    echo ""
    
    # Check if docker-compose.yml exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "docker-compose.yml not found in current directory"
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        log_warning ".env file not found. Some environment variables may not be set."
    else
        log_success ".env file found"
        
        # Check for Cloudflare Tunnel token
        if grep -q "CLOUDFLARE_TUNNEL_TOKEN" .env 2>/dev/null; then
            log_info "Cloudflare Tunnel token found in .env - tunnel will be started automatically"
        else
            log_warning "CLOUDFLARE_TUNNEL_TOKEN not found in .env - tunnel will not start"
            log_warning "Add CLOUDFLARE_TUNNEL_TOKEN to .env if you want tunnel support"
        fi
        
        # Check for Docker Hub push configuration
        if [ "$PUSH_IMAGE" = "true" ]; then
            if [ -n "$DOCKER_USERNAME" ]; then
                log_info "Docker Hub push enabled - image will be pushed to: ${DOCKER_USERNAME}/${DOCKER_IMAGE_NAME}:${DOCKER_TAG}"
            else
                log_info "Docker Hub push enabled but DOCKER_USERNAME not set - push will be skipped"
                log_info "  Set DOCKER_USERNAME to enable automatic push after redeploy"
            fi
        else
            log_info "Docker Hub push disabled (PUSH_IMAGE=false)"
        fi
    fi
    
    # Check if old container is running
    OLD_CONTAINER_RUNNING=false
    if is_container_running "$CONTAINER_NAME"; then
        OLD_CONTAINER_RUNNING=true
        log_success "Current container ($CONTAINER_NAME) is running - will keep it running during rebuild"
    else
        log_warning "Current container ($CONTAINER_NAME) is not running - will start new one directly"
    fi
    
    echo ""
    log_info "Step 1: Building new Docker image with --no-cache..."
    log_warning "This may take several minutes..."
    echo ""
    
    # Build new image with no cache
    log_info "Using: $DOCKER_COMPOSE"
    if $DOCKER_COMPOSE build --no-cache "$SERVICE_NAME"; then
        log_success "New image built successfully"
    else
        log_error "Failed to build new image"
        exit 1
    fi
    
    # Get the newly built image ID
    # docker-compose build creates an image, we need to find it
    # The image is typically the most recently created one matching our service
    log_info "Detecting newly built image..."
    
    # Wait a moment for image to be registered
    sleep 1
    
    # Get the image created by docker-compose build (most recent)
    NEW_IMAGE_ID=$(docker images --format "{{.ID}}\t{{.CreatedAt}}" --filter "reference=${IMAGE_NAME}" | sort -k2 -r | head -n 1 | cut -f1)
    
    if [ -z "$NEW_IMAGE_ID" ]; then
        # Try to find any image with the service name (fallback)
        NEW_IMAGE_ID=$(docker images --format "{{.ID}}\t{{.CreatedAt}}" | head -n 1 | cut -f1 || true)
    fi
    
    if [ -z "$NEW_IMAGE_ID" ]; then
        log_error "Could not find newly built image"
        log_info "Available images:"
        docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}" | head -n 10
        log_error "Please check docker-compose build output"
        exit 1
    fi
    
    # Tag the new image
    docker tag "$NEW_IMAGE_ID" "${IMAGE_NAME}:new"
    log_success "New image tagged as: ${IMAGE_NAME}:new (ID: ${NEW_IMAGE_ID:0:12})"
    
    echo ""
    log_info "Step 2: Starting new container on temporary port $TEMP_PORT..."
    
    # Start new container on temporary port
    # Note: --env-file .env will include CLOUDFLARE_TUNNEL_TOKEN if present
    # The tunnel will start automatically inside the container if token is set
    docker run -d \
        --name "$NEW_CONTAINER_NAME" \
        --env-file .env \
        -p "${TEMP_PORT}:8000" \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/logs:/app/logs" \
        --restart no \
        "${IMAGE_NAME}:new" || {
        log_error "Failed to start new container"
        exit 1
    }
    
    # Verify Cloudflare Tunnel token was loaded (if .env exists)
    if [ -f ".env" ] && grep -q "CLOUDFLARE_TUNNEL_TOKEN" .env 2>/dev/null; then
        log_info "Verifying Cloudflare Tunnel token is loaded in new container..."
        if docker exec "$NEW_CONTAINER_NAME" sh -c "test -n \"\$CLOUDFLARE_TUNNEL_TOKEN\"" 2>/dev/null; then
            log_success "Cloudflare Tunnel token loaded successfully"
        else
            log_warning "Cloudflare Tunnel token may not be loaded - check .env file"
        fi
    fi
    
    log_success "New container started: $NEW_CONTAINER_NAME"
    log_info "Waiting for container to be ready..."
    
    # Wait for container to start
    sleep 5
    
    echo ""
    log_info "Step 3: Health checking new container..."
    
    # Health check the new container
    HEALTH_CHECK_URL_TEMP="http://localhost:${TEMP_PORT}/health"
    HEALTH_CHECK_PASSED=false
    
    for i in $(seq 1 $MAX_HEALTH_CHECK_RETRIES); do
        if health_check "$HEALTH_CHECK_URL_TEMP" "$NEW_CONTAINER_NAME"; then
            log_success "Health check passed! (attempt $i/$MAX_HEALTH_CHECK_RETRIES)"
            HEALTH_CHECK_PASSED=true
            break
        else
            if [ $i -lt $MAX_HEALTH_CHECK_RETRIES ]; then
                log_info "Health check failed (attempt $i/$MAX_HEALTH_CHECK_RETRIES), retrying in ${HEALTH_CHECK_INTERVAL}s..."
                sleep $HEALTH_CHECK_INTERVAL
            fi
        fi
    done
    
    if [ "$HEALTH_CHECK_PASSED" = false ]; then
        log_error "Health check failed after $MAX_HEALTH_CHECK_RETRIES attempts"
        log_error "New container is not healthy - keeping old container running"
        
        # Show new container logs for debugging
        echo ""
        log_info "New container logs (last 50 lines):"
        docker logs --tail 50 "$NEW_CONTAINER_NAME" || true
        
        echo ""
        log_warning "Old container ($CONTAINER_NAME) is still running"
        log_warning "Please investigate the issue and try again"
        exit 1
    fi
    
    echo ""
    log_info "Step 4: Switching to new container..."
    
    # Stop old container if it was running
    if [ "$OLD_CONTAINER_RUNNING" = true ]; then
        log_info "Stopping old container: $CONTAINER_NAME"
        docker stop "$CONTAINER_NAME" || {
            log_error "Failed to stop old container - aborting switchover"
            exit 1
        }
        log_success "Old container stopped"
    fi
    
    # Remove old container
    if container_exists "$CONTAINER_NAME"; then
        log_info "Removing old container: $CONTAINER_NAME"
        docker rm "$CONTAINER_NAME" || {
            log_error "Failed to remove old container"
            exit 1
        }
        log_success "Old container removed"
    fi
    
    # Stop temporary container (will recreate with correct port)
    log_info "Stopping temporary container..."
    docker stop "$NEW_CONTAINER_NAME"
    docker rm "$NEW_CONTAINER_NAME"
    
    # Tag new image as latest for docker-compose
    docker tag "${IMAGE_NAME}:new" "${IMAGE_NAME}:latest"
    
    # Start production container using docker compose
    # This will recreate the container with all correct settings from docker-compose.yml
    # Note: docker-compose automatically reads .env file, so CLOUDFLARE_TUNNEL_TOKEN will be included
    log_info "Starting production container with $DOCKER_COMPOSE..."
    log_info "Note: docker-compose will use .env file automatically (includes CLOUDFLARE_TUNNEL_TOKEN if present)"
    
    if $DOCKER_COMPOSE up -d --no-deps "$SERVICE_NAME"; then
        log_success "Production container started"
        log_info "Cloudflare Tunnel will start automatically if CLOUDFLARE_TUNNEL_TOKEN is in .env"
    else
        log_error "Failed to start production container"
        
        # Try to restore old container
        log_warning "Attempting to restore old container..."
        
        # Find and restore old image
        OLD_IMAGE=$(docker images "${IMAGE_NAME}" --format "{{.ID}}" --filter "dangling=false" | tail -n +2 | head -n 1)
        if [ -n "$OLD_IMAGE" ]; then
            log_info "Restoring old image..."
            docker tag "$OLD_IMAGE" "${IMAGE_NAME}:latest"
            $DOCKER_COMPOSE up -d --no-deps "$SERVICE_NAME" || {
                log_error "Failed to restore old container"
                exit 1
            }
            log_warning "Old container restored - please investigate the deployment issue"
        else
            log_error "Could not find old image to restore"
        fi
        exit 1
    fi
    
    # Wait a moment for container to start
    sleep 3
    
    # Final health check on production port
    log_info "Final health check on production port..."
    if health_check "$HEALTH_CHECK_URL" "$CONTAINER_NAME"; then
        log_success "Production container is healthy!"
    else
        log_error "Production container health check failed"
        log_error "Container is running but health check failed - please investigate"
    fi
    
    echo ""
    log_info "Checking Cloudflare Tunnel status..."
    
    # Check if tunnel is running inside the container
    if docker exec "$CONTAINER_NAME" sh -c "pgrep -f cloudflared > /dev/null 2>&1" 2>/dev/null; then
        log_success "Cloudflare Tunnel is running inside container"
        log_info "Tunnel logs: docker logs $CONTAINER_NAME | grep -i tunnel"
    elif docker exec "$CONTAINER_NAME" sh -c "test -n \"\$CLOUDFLARE_TUNNEL_TOKEN\"" 2>/dev/null; then
        log_warning "Cloudflare Tunnel token is set but tunnel process not found"
        log_warning "Check container logs: docker logs $CONTAINER_NAME"
    else
        log_info "Cloudflare Tunnel not configured (no token set)"
    fi
    
    # Clean up old image
    log_info "Cleaning up old images..."
    
    # Find and remove old images (keep only the new one as latest)
    OLD_IMAGES=$(docker images "${IMAGE_NAME}" --format "{{.ID}}" --filter "dangling=true" | head -n -1)
    if [ -n "$OLD_IMAGES" ]; then
        log_info "Removing old dangling images..."
        echo "$OLD_IMAGES" | xargs -r docker rmi 2>/dev/null || true
    fi
    
    # Remove the temporary :new tag
    docker rmi "${IMAGE_NAME}:new" 2>/dev/null || true
    
    echo ""
    log_success "✓ Deployment completed successfully!"
    echo ""
    log_info "Container status:"
    docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    log_info "Health check URL: $HEALTH_CHECK_URL"
    log_info "View logs: docker logs -f $CONTAINER_NAME"
    echo ""
    log_info "Cloudflare Tunnel:"
    log_info "  - The tunnel runs inside the container if CLOUDFLARE_TUNNEL_TOKEN is set in .env"
    log_info "  - Check tunnel status: docker logs $CONTAINER_NAME | grep -i tunnel"
    log_info "  - Verify tunnel URL in Cloudflare Dashboard"
    
    echo ""
    # Push to Docker Hub if configured
    if [ "$PUSH_IMAGE" = "true" ] && [ -n "$DOCKER_USERNAME" ]; then
        push_to_dockerhub
    elif [ "$PUSH_IMAGE" = "true" ] && [ -z "$DOCKER_USERNAME" ]; then
        log_info "Docker Hub push skipped (DOCKER_USERNAME not set)"
        log_info "  Set DOCKER_USERNAME to enable automatic push after redeploy"
    fi
}

# Push image to Docker Hub
push_to_dockerhub() {
    echo ""
    log_info "Step 6: Pushing image to Docker Hub..."
    
    # Get the source image (the one we just deployed)
    SOURCE_IMAGE=$(docker inspect --format='{{.Config.Image}}' "$CONTAINER_NAME" 2>/dev/null || true)
    
    # If no tag, add :latest
    if [ -n "$SOURCE_IMAGE" ] && [[ "$SOURCE_IMAGE" != *":"* ]]; then
        SOURCE_IMAGE="${SOURCE_IMAGE}:latest"
    fi
    
    # If still empty, try to get from docker compose
    if [ -z "$SOURCE_IMAGE" ] || [ "$SOURCE_IMAGE" = "<no value>" ]; then
        SOURCE_IMAGE="${IMAGE_NAME}:latest"
    fi
    
    # Build full target image name
    FULL_IMAGE_NAME="${DOCKER_USERNAME}/${DOCKER_IMAGE_NAME}:${DOCKER_TAG}"
    
    log_info "Source image: $SOURCE_IMAGE"
    log_info "Target image: $FULL_IMAGE_NAME"
    
    # Check if source image exists
    if ! docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${SOURCE_IMAGE}$"; then
        log_warning "Source image '$SOURCE_IMAGE' not found - skipping push"
        log_info "Available images:"
        docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | head -5
        return
    fi
    
    echo ""
    log_info "Tagging image for Docker Hub..."
    docker tag "$SOURCE_IMAGE" "$FULL_IMAGE_NAME" || {
        log_error "Failed to tag image"
        return
    }
    log_success "Image tagged: $FULL_IMAGE_NAME"
    
    # Check if logged in to Docker Hub
    echo ""
    log_info "Checking Docker Hub login..."
    if ! docker info 2>/dev/null | grep -q "Username"; then
        log_warning "Not logged in to Docker Hub"
        log_info "Skipping push - please login manually: docker login"
        log_info "Then push manually: docker push $FULL_IMAGE_NAME"
        return
    fi
    
    CURRENT_USER=$(docker info 2>/dev/null | grep "Username" | awk '{print $2}' || echo "")
    if [ "$CURRENT_USER" != "$DOCKER_USERNAME" ]; then
        log_warning "Logged in as different user: $CURRENT_USER (expected: $DOCKER_USERNAME)"
        log_info "Skipping push - please login as $DOCKER_USERNAME"
        return
    fi
    
    log_success "Logged in as $DOCKER_USERNAME"
    
    # Push to Docker Hub
    echo ""
    log_info "Pushing to Docker Hub..."
    log_warning "This may take several minutes depending on image size..."
    
    if docker push "$FULL_IMAGE_NAME"; then
        echo ""
        log_success "✓ Successfully pushed to Docker Hub: $FULL_IMAGE_NAME"
        log_info "Image URL: https://hub.docker.com/r/${DOCKER_USERNAME}/${DOCKER_IMAGE_NAME}/tags"
    else
        log_error "Failed to push image to Docker Hub"
        log_info "You can retry manually: docker push $FULL_IMAGE_NAME"
    fi
}

# Run main function
main

