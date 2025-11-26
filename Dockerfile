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

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies (for company intelligence scraper)
RUN apt-get update && apt-get install -y \
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

# Copy requirements and install Python dependencies
# Install CPU-only PyTorch first to avoid CUDA dependencies (important for AMD)
COPY requirements.txt .
# Install CPU-only PyTorch to prevent CUDA dependencies on AMD architecture
# This ensures sentence-transformers uses CPU-only PyTorch
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
# Install other requirements, ensuring torch packages are not upgraded/reinstalled
# Use --extra-index-url to make CPU index available for torch dependencies
# Use --upgrade-strategy only-if-needed to prevent upgrading already-installed torch
# This prevents sentence-transformers from installing CUDA-enabled PyTorch
RUN pip install --no-cache-dir --upgrade-strategy only-if-needed --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code (frontend folder excluded via .dockerignore)
COPY . .

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

# Run the API server
CMD ["python", "api.py"]

