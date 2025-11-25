# Multi-stage Dockerfile for GraphRAG Application
# Backend-only API (frontend hosted separately, e.g., on Vercel)

# Build argument to optionally build frontend (default: false for backend-only)
ARG BUILD_FRONTEND=false

# Stage 1: Build frontend (only if BUILD_FRONTEND=true)
FROM node:20-alpine AS frontend-builder
ARG BUILD_FRONTEND
WORKDIR /app/frontend

# Only build frontend if BUILD_FRONTEND is true
COPY frontend/package*.json ./
RUN if [ "$BUILD_FRONTEND" = "true" ]; then \
      npm ci; \
    else \
      echo "Skipping frontend build (backend-only mode)"; \
    fi

COPY frontend/ ./
RUN if [ "$BUILD_FRONTEND" = "true" ]; then \
      npm run build; \
    fi

# Stage 2: Python backend
FROM python:3.11-slim
ARG BUILD_FRONTEND

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
# Install other requirements (pip will use existing torch installation)
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY . .

# Copy built frontend from builder stage (only if it was built)
ARG BUILD_FRONTEND
RUN if [ "$BUILD_FRONTEND" = "true" ]; then \
      echo "Copying frontend build..."; \
    else \
      echo "Backend-only mode - skipping frontend copy"; \
    fi
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist 2>/dev/null || true

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

