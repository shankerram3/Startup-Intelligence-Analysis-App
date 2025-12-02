# Multi-stage Dockerfile for GraphRAG Application
# Backend-only API (frontend hosted separately on Vercel)
# Frontend is NOT included in this Docker image

# Build argument to optionally build frontend (default: false for backend-only)
# Set BUILD_FRONTEND=true only if you need to include frontend in the image
ARG BUILD_FRONTEND=false

# Stage 1: Build frontend (only if BUILD_FRONTEND=true)
# This stage is skipped entirely when BUILD_FRONTEND=false to save build time
FROM node:20-alpine AS frontend-builder
ARG BUILD_FRONTEND
WORKDIR /app/frontend

# Only proceed if BUILD_FRONTEND is true
# Create dist directory first so COPY --from works even when BUILD_FRONTEND=false
RUN mkdir -p dist

COPY frontend/package*.json ./
RUN if [ "$BUILD_FRONTEND" = "true" ]; then \
      npm ci; \
    else \
      echo "Backend-only mode: Skipping frontend build (frontend served from Vercel)"; \
    fi

COPY frontend/ ./
RUN if [ "$BUILD_FRONTEND" = "true" ]; then \
      npm run build; \
    fi

# Stage 2: Python backend
# This is the main stage - always built
FROM python:3.11-slim
# Re-declare BUILD_FRONTEND with default value (ARG values don't carry between stages)
ARG BUILD_FRONTEND=false

# Set working directory
WORKDIR /app

# Install all system dependencies in one layer (better caching)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    curl \
    wget \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Install cloudflared for Cloudflare Tunnel
RUN curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared \
    && chmod +x /usr/local/bin/cloudflared

# Copy requirements FIRST for better layer caching
# This layer only invalidates when requirements.txt changes
COPY requirements.txt .

# Install CPU-only PyTorch with BuildKit cache mount (faster rebuilds)
# Use --prefer-binary to prefer pre-built wheels (faster than building from source)
# Install CPU-only PyTorch to prevent CUDA dependencies on AMD architecture
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefer-binary --no-cache-dir \
    torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cpu

# Install other requirements with BuildKit cache mount
# Use --prefer-binary for faster installs (uses pre-built wheels when available)
# Use --extra-index-url to make CPU index available for torch dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefer-binary --no-cache-dir \
    --upgrade --upgrade-strategy only-if-needed \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

# Install Playwright browsers with cache mount (browsers are large, cache helps)
# Make Playwright optional for faster builds when not needed
ARG INSTALL_PLAYWRIGHT=true
RUN --mount=type=cache,target=/root/.cache/ms-playwright \
    if [ "$INSTALL_PLAYWRIGHT" = "true" ]; then \
      playwright install chromium && \
      playwright install-deps chromium; \
    else \
      echo "Skipping Playwright installation (INSTALL_PLAYWRIGHT=false)"; \
    fi

# Copy application code LAST (changes most frequently)
# This invalidates cache only when code changes, not when deps change
COPY . .

# Make startup script executable
RUN chmod +x /app/scripts/start-api-with-tunnel.sh

# Conditionally copy built frontend from builder stage if BUILD_FRONTEND=true
# Frontend is served separately from Vercel when BUILD_FRONTEND=false (default)
# Note: dist directory is created in frontend-builder stage even when BUILD_FRONTEND=false
# to allow COPY to succeed, but it will be empty
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist
RUN if [ "$BUILD_FRONTEND" != "true" ]; then \
      echo "Backend-only mode: Frontend served from Vercel, not included in image"; \
      rm -rf ./frontend/dist || true; \
    else \
      echo "Frontend included in image (BUILD_FRONTEND=true)"; \
    fi

# Don't create data directories in image - create at runtime to save memory
# Data directories will be created by the application on startup

# Expose API port (Render will override with $PORT)
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
# Render uses PORT env var - will be set by Render at runtime
# Prevent CUDA/GPU dependencies (important for AMD architecture)
ENV CUDA_VISIBLE_DEVICES=""
ENV TORCH_CUDA_ARCH_LIST=""
# Disable reload in production (Render, DigitalOcean, etc.)
ENV DISABLE_RELOAD="true"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the API server with optional Cloudflare Tunnel
CMD ["/app/scripts/start-api-with-tunnel.sh"]

