# Docker Guide

Complete guide for building, running, pushing, and sharing the GraphRAG Docker image.

## Table of Contents

1. [Building the Docker Image](#building-the-docker-image)
2. [Running with Docker Compose](#running-with-docker-compose)
3. [Running Standalone Container](#running-standalone-container)
4. [Pushing to Registry](#pushing-to-registry)
5. [Sharing the Image](#sharing-the-image)
6. [Troubleshooting](#troubleshooting)

---

## Building the Docker Image

### Prerequisites

- Docker installed and running
- Docker Compose (optional, for full stack)

### Option 1: Using the build script
```bash
./build-docker.sh
```

### Option 2: Manual build
```bash
docker build -t graphrag:latest .
```

### Option 3: Using docker-compose
```bash
docker-compose build graphrag-api
```

The Docker image:
- Uses multi-stage build (Node.js for frontend, Python for backend)
- Includes Playwright with Chromium for company intelligence scraping
- Serves the built React frontend from the FastAPI backend
- Exposes port 8000
- Includes health check endpoint
- **Does NOT include data** (data directory is excluded via .dockerignore)

---

## Running with Docker Compose

This will start both Neo4j and the GraphRAG API:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Accessing the Application

Once running:
- **Frontend UI**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health
- **Neo4j Browser**: http://localhost:7474

---

## Running Standalone Container

### Basic run
```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key_here \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PASSWORD=password \
  graphrag:latest
```

### With data volume
```bash
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env:ro \
  -e OPENAI_API_KEY=your_key_here \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  graphrag:latest
```

### Environment Variables

**Required:**
- `OPENAI_API_KEY` - Your OpenAI API key
- `NEO4J_URI` - Neo4j connection URI (default: `bolt://neo4j:7687` in docker-compose)
- `NEO4J_USER` - Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD` - Neo4j password

**Optional:**
- `API_HOST` - API host (default: `0.0.0.0`)
- `API_PORT` - API port (default: `8000`)
- `RAG_EMBEDDING_BACKEND` - Embedding backend: `openai` or `sentence-transformers` (default: `openai`)

---

## Pushing to Registry

### Quick Start: Push Image (Recommended)

```bash
# Set your Docker Hub username
export DOCKER_USERNAME=your-username

# Run the automated script
./push-image.sh
```

### Manual Steps

#### Step 1: Login to Docker Hub
```bash
docker login
```

#### Step 2: Tag the Image
```bash
# Replace 'your-username' with your Docker Hub username
docker tag swmproject-graphrag-api:latest your-username/graphrag:latest

# Or with a specific version tag
docker tag swmproject-graphrag-api:latest your-username/graphrag:v1.0
```

#### Step 3: Push to Registry
```bash
docker push your-username/graphrag:latest
```

### Other Registries

#### AWS ECR
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker tag swmproject-graphrag-api:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/graphrag:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/graphrag:latest
```

#### Google Container Registry (GCR)
```bash
gcloud auth configure-docker
docker tag swmproject-graphrag-api:latest gcr.io/your-project/graphrag:latest
docker push gcr.io/your-project/graphrag:latest
```

#### Azure Container Registry (ACR)
```bash
az acr login --name yourregistry
docker tag swmproject-graphrag-api:latest yourregistry.azurecr.io/graphrag:latest
docker push yourregistry.azurecr.io/graphrag:latest
```

#### GitHub Container Registry (GHCR)
```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
docker tag swmproject-graphrag-api:latest ghcr.io/username/graphrag:latest
docker push ghcr.io/username/graphrag:latest
```

### Image Size Considerations

- Base image: ~4.5GB
- Push time: 10-30 minutes depending on connection
- Storage: Check your registry's free tier limits

---

## Sharing the Image

### Method 1: Docker Hub (Public Repository) 🌐

**Best for**: Public sharing, easy access

```bash
docker login
docker tag swmproject-graphrag-api:latest your-username/graphrag:latest
docker push your-username/graphrag:latest
```

**Share**: `docker pull your-username/graphrag:latest`

**Pros**: Free, easy to share, version control  
**Cons**: Public = anyone can see it

### Method 2: Docker Hub (Private Repository) 🔒

**Best for**: Sharing with specific people

1. Create private repo on Docker Hub
2. Push the image (same commands as above)
3. Add collaborators in repository settings

**Pros**: Private and secure, control access  
**Cons**: Requires Docker Hub Pro ($5/month) for private repos

### Method 3: Export as Tar File 📦

**Best for**: Offline sharing, one-time sharing

```bash
# Save image to tar file
docker save swmproject-graphrag-api:latest -o graphrag-image.tar

# Compress it (recommended - saves ~60% space)
gzip graphrag-image.tar
# Creates: graphrag-image.tar.gz (~1.8GB instead of 4.5GB)
```

**Share**: Upload `graphrag-image.tar.gz` to Google Drive, Dropbox, etc.

**Recipient loads it**:
```bash
gunzip graphrag-image.tar.gz
docker load -i graphrag-image.tar
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=their_key \
  -e NEO4J_URI=bolt://their-neo4j:7687 \
  swmproject-graphrag-api:latest
```

**Pros**: Works offline, no registry needed  
**Cons**: Large file size (~1.8GB compressed)

### Method 4: Export Container (With Data) 📦+💾

**Best for**: Sharing container WITH all data included

⚠️ **WARNING**: This includes ALL data in the container!

```bash
# Start the container
docker-compose up -d

# Export the container
docker export graphrag-api -o graphrag-container.tar
gzip graphrag-container.tar
```

**Recipient imports it**:
```bash
gunzip graphrag-container.tar.gz
docker import graphrag-container.tar graphrag:with-data
docker run -p 8000:8000 graphrag:with-data
```

### Quick Comparison

| Method | File Size | Setup Time | Best For |
|--------|-----------|------------|----------|
| Docker Hub (Public) | 0 (cloud) | 5 min | Public sharing |
| Docker Hub (Private) | 0 (cloud) | 10 min | Team sharing |
| Tar Export | 1.8GB | 2 min | One-time, offline |
| Container Export | 4.5GB+ | 2 min | With data included |

---

## Troubleshooting

### Port already in use
```bash
# Change the port mapping
docker run -p 8001:8000 graphrag:latest
```

### Neo4j connection issues
- Ensure Neo4j is running and accessible
- Check `NEO4J_URI` environment variable
- In docker-compose, Neo4j service name is `neo4j`
- **Important**: Use `bolt://neo4j:7687` in docker-compose (not `localhost`)

### Frontend not loading
- Ensure frontend was built successfully (check build logs)
- Verify `frontend/dist` directory exists in the image
- Check browser console for errors

### Missing environment variables
- Create a `.env` file or pass variables via `-e` flags
- See `.env.aura.template` for example configuration

### Push errors

**"denied: requested access to the resource is denied"**
- Check you're logged in: `docker login`
- Verify repository name matches your username
- Check repository permissions

**"unauthorized: authentication required"**
- Re-login: `docker logout` then `docker login`
- Check token hasn't expired

**Push is very slow**
- Normal for large images (4.5GB+)
- Consider using a registry closer to you
- Check your upload bandwidth

### Security Notes

- **Never commit containers with secrets** in environment variables
- **Review data** before pushing (what's included?)
- **Use private repositories** for production data
- **Consider data encryption** for sensitive information

---

## Scripts

- `build-docker.sh` - Build the Docker image
- `push-image.sh` - Push image to registry (automated)
- `push-to-registry.sh` - Push container with data to registry
- `export-container.sh` - Export container to tar file
