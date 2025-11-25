# How to Start GraphRAG Docker Backend

This guide shows you how to start the GraphRAG backend in Docker.

## Prerequisites

1. Docker and Docker Compose installed
2. Required environment variables set (see below)

## Option 1: Using Docker Compose (Recommended)

This runs the backend API - Neo4j is hosted on AuraDB cloud (external).

### Step 1: Create `.env` file

Create a `.env` file in the project root:

```bash
# Required - AuraDB Connection
OPENAI_API_KEY=sk-your-openai-api-key
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io  # Your AuraDB URI
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-aura-password

# Required - CORS (for Vercel frontend)
ALLOWED_ORIGINS=https://your-app.vercel.app,https://your-app-git-main.vercel.app

# Optional - Security
ENABLE_AUTH=false
JWT_SECRET_KEY=your-secret-key-here
ENABLE_RATE_LIMITING=true

# Optional - Redis Cache (enabled by default if REDIS_URL is set)
CACHE_ENABLED=true
REDIS_URL=redis://default:rYxHAj0uEv7Qcjcz5732l2vzuIYuOAoY@redis-18335.c9.us-east-1-2.ec2.cloud.redislabs.com:18335
# Or use individual config instead of REDIS_URL:
# REDIS_HOST=redis-18335.c9.us-east-1-2.ec2.cloud.redislabs.com
# REDIS_PORT=18335
# REDIS_PASSWORD=rYxHAj0uEv7Qcjcz5732l2vzuIYuOAoY
# REDIS_USERNAME=default

# Optional - Logging
LOG_LEVEL=INFO
JSON_LOGS=true
```

### Step 2: Start the backend

```bash
# Start backend (AuraDB is external)
docker-compose up -d

# View logs
docker-compose logs -f graphrag-api

# Check status
docker-compose ps
```

### Step 3: Verify it's running

```bash
# Check health endpoint
curl http://localhost:8000/health

# Or open in browser
open http://localhost:8000/docs
```

### Stop services

```bash
# Stop backend
docker-compose down
```

## Option 2: Run Docker Container Directly

If you prefer to run the container directly without docker-compose:

### Step 1: Build the image

```bash
# Build backend-only image (no frontend)
./scripts/build-docker-amd.sh

# Or manually:
docker build --build-arg BUILD_FRONTEND=false -t graphrag:latest .
```

### Step 2: Run the container

```bash
docker run -d \
  --name graphrag-api \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-your-key \
  -e NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PASSWORD=your-aura-password \
  -e ALLOWED_ORIGINS=https://your-app.vercel.app \
  -e REDIS_URL=redis://default:password@host:port \
  -e CACHE_ENABLED=true \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  graphrag:latest
```

### Step 3: View logs

```bash
# Follow logs
docker logs -f graphrag-api

# Check status
docker ps | grep graphrag
```

### Stop the container

```bash
docker stop graphrag-api
docker rm graphrag-api
```


## Required Environment Variables

### Minimum Required

- `OPENAI_API_KEY` - Your OpenAI API key
- `NEO4J_URI` - Neo4j AuraDB connection URI (format: `neo4j+s://xxxxx.databases.neo4j.io`)
- `NEO4J_USER` - Neo4j username (usually `neo4j`)
- `NEO4J_PASSWORD` - Neo4j password

### Recommended for Production

- `ALLOWED_ORIGINS` - Comma-separated list of allowed CORS origins (your Vercel domain)
- `JWT_SECRET_KEY` - Secret key for JWT tokens (if using auth)
- `ENABLE_AUTH` - Set to `true` to enable authentication
- `REDIS_URL` - Redis connection URL (format: `redis://username:password@host:port`)
- `CACHE_ENABLED` - Set to `true` to enable caching (default: `true` if REDIS_URL is set)

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs graphrag-api

# Check if port is already in use
sudo lsof -i :8000

# Check container status
docker ps -a | grep graphrag
```

### Can't connect to Neo4j AuraDB

```bash
# Verify AuraDB URI is correct in .env file
# Format: neo4j+s://xxxxx.databases.neo4j.io
# Make sure you're using neo4j+s:// (secure) not bolt://

# Test connection from your local machine
# Download Neo4j Desktop or use cypher-shell to test the connection

# Check container logs for connection errors
docker logs graphrag-api | grep -i neo4j
```

### Health check fails

```bash
# Check if API is responding
curl http://localhost:8000/health

# Check container logs for errors
docker logs graphrag-api | tail -50
```

## Quick Start Commands

```bash
# Start backend (AuraDB is external)
docker-compose up -d

# View API logs
docker-compose logs -f graphrag-api

# Restart API
docker-compose restart graphrag-api

# Stop
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

## Access Points

Once running, access:

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics
- **Neo4j Browser**: Access via your AuraDB dashboard

