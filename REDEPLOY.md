# Zero-Downtime Redeploy Script

## Overview

The `scripts/redeploy.sh` script performs a zero-downtime deployment of the GraphRAG API Docker container. It keeps the current container running while building a new image, health checks the new container, and only switches over if the new container is healthy.

## Features

- ✅ **Zero-downtime deployment**: Keeps old container running during rebuild
- ✅ **No-cache build**: Ensures a clean build without using cached layers
- ✅ **Health checking**: Verifies new container is healthy before switchover
- ✅ **Automatic rollback**: Keeps old container running if new one fails
- ✅ **Clean cleanup**: Removes old containers and images after successful deployment

## Usage

```bash
# From the project root directory
./scripts/redeploy.sh
```

The script will:
1. Check if the current container is running
2. Build a new Docker image with `--no-cache`
3. Start a new container on a temporary port (8001) for health checking
4. Health check the new container (up to 30 attempts, 3 seconds apart)
5. If healthy:
   - Stop the old container
   - Remove the old container
   - Start the new container on the production port (8000)
   - Clean up old images
6. If unhealthy:
   - Keep the old container running
   - Remove the new container
   - Show error logs for debugging

## Requirements

- Docker and Docker Compose installed
- `.env` file present in the project root
- Current container should be running (optional - script will handle this)

## Configuration

You can customize the following variables in the script:

- `COMPOSE_FILE`: docker-compose.yml file location (default: `docker-compose.yml`)
- `SERVICE_NAME`: Service name in docker-compose.yml (default: `graphrag-api`)
- `CONTAINER_NAME`: Container name (default: `graphrag-api`)
- `HEALTH_CHECK_URL`: Health check endpoint (default: `http://localhost:8000/health`)
- `TEMP_PORT`: Temporary port for health checking (default: `8001`)
- `MAX_HEALTH_CHECK_RETRIES`: Maximum health check attempts (default: `30`)
- `HEALTH_CHECK_INTERVAL`: Seconds between health checks (default: `3`)

## Health Check

The script uses the `/health` endpoint to verify the container is ready. The health check:

- Waits for the container to start (5 seconds)
- Attempts up to 30 health checks (3 seconds apart)
- Verifies the HTTP response is successful (200 OK)

## Troubleshooting

### New container fails health check

If the new container fails health checks:

1. Check the container logs:
   ```bash
   docker logs graphrag-api-new
   ```

2. Check the health endpoint manually:
   ```bash
   curl http://localhost:8001/health
   ```

3. Verify environment variables in `.env` file

4. Check Neo4j connection:
   ```bash
   docker exec graphrag-api-new env | grep NEO4J
   ```

### Old container not detected

If the script can't find the old container:

- The container name must match `graphrag-api`
- Check running containers: `docker ps`

### Image name detection fails

The script automatically detects the image name from:
1. Running container's image
2. Docker Compose configuration
3. Project directory name

If detection fails, check:
```bash
docker images | grep graphrag-api
docker-compose config | grep image
```

## Example Output

```
ℹ Starting zero-downtime redeployment...

✓ Current container (graphrag-api) is running - will keep it running during rebuild

ℹ Step 1: Building new Docker image with --no-cache...
⚠ This may take several minutes...

✓ New image built successfully
✓ New image tagged as: startup-intelligence-analysis-app_graphrag-api:new (ID: abc123def456)

ℹ Step 2: Starting new container on temporary port 8001...
✓ New container started: graphrag-api-new
ℹ Waiting for container to be ready...

ℹ Step 3: Health checking new container...
✓ Health check passed! (attempt 5/30)

ℹ Step 4: Switching to new container...
ℹ Stopping old container: graphrag-api
✓ Old container stopped
ℹ Removing old container: graphrag-api
✓ Old container removed
ℹ Stopping temporary container...
ℹ Starting production container with docker-compose...
✓ Production container started

ℹ Final health check on production port...
✓ Production container is healthy!

ℹ Cleaning up old images...

✓ Deployment completed successfully!

Container status:
NAMES           STATUS          PORTS
graphrag-api    Up 10 seconds   0.0.0.0:8000->8000/tcp

ℹ Health check URL: http://localhost:8000/health
ℹ View logs: docker logs -f graphrag-api
```

## Notes

- The script uses `docker-compose build --no-cache` which may take 10-20 minutes depending on your system
- During the switchover, there will be a brief downtime (usually < 5 seconds)
- Old images are automatically cleaned up to save disk space
- The script preserves all environment variables and volumes from docker-compose.yml

## Safety Features

- Automatic cleanup on script exit (via trap)
- Keeps old container running if new one fails
- Health checks ensure new container is ready before switchover
- Detailed logging for debugging
- Error handling at each step

