# Multi-stage Dockerfile for GraphRAG Application
# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install frontend dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build frontend for production
RUN npm run build

# Stage 2: Python backend with frontend
FROM python:3.11-slim

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

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

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

