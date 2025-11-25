#!/bin/bash
# Build script for Render deployment
# This script runs during the Docker build process on Render

set -e

echo "🚀 Starting Render build process..."

# Install system dependencies if needed
echo "📦 Installing system dependencies..."
apt-get update && apt-get install -y \
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
    || echo "⚠️ Some dependencies may already be installed"

# Build frontend
if [ -d "frontend" ]; then
    echo "🎨 Building frontend..."
    cd frontend
    npm ci
    npm run build
    cd ..
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (if needed)
if command -v playwright &> /dev/null; then
    echo "🎭 Installing Playwright browsers..."
    playwright install chromium || echo "⚠️ Playwright installation skipped"
fi

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data/articles data/metadata data/processing data/raw_data logs

echo "✅ Build process completed successfully!"

