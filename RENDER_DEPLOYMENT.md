# Render Deployment Guide

## Memory Optimization for Render Free Tier (512 MiB)

This guide addresses memory issues when deploying to Render's free tier.

## ✅ Fixed Issues

### 1. **Uvicorn Auto-Reload Disabled**
- ✅ Reload is automatically disabled in containers (production)
- ✅ Set `DISABLE_RELOAD=true` in Dockerfile as fallback
- ✅ Reload only enabled if `ENABLE_RELOAD=true` is explicitly set

### 2. **Data Directories Created at Runtime**
- ✅ Removed `RUN mkdir -p data/...` from Dockerfile
- ✅ Directories created in Python at startup (saves image size)
- ✅ Creates: `data/articles`, `data/metadata`, `data/processing`, `data/raw_data`, `logs`

### 3. **PORT Environment Variable**
- ✅ Uses `PORT` (Render's standard) with fallback to `API_PORT`
- ✅ Format: `PORT || API_PORT || 8000`

### 4. **Memory-Saving Optimizations**
- ✅ No data directories in Docker image layers
- ✅ Single process (no reloader) in production
- ✅ CPU-only PyTorch (no CUDA dependencies)

## 🔧 Render Environment Variables

Set these in Render dashboard:

```bash
# Required
PORT=8000  # Render sets this automatically, but good to have as fallback
OPENAI_API_KEY=your_key
NEO4J_URI=bolt://your-neo4j-uri
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Optional but recommended
DISABLE_RELOAD=true  # Explicitly disable reload (already handled, but safe)
ENVIRONMENT=production  # Mark as production
LOG_LEVEL=INFO  # Reduce log verbosity
JSON_LOGS=true  # Structured logging

# Redis (optional - set to empty if not using)
REDIS_URL=  # Leave empty if not using Redis
CACHE_ENABLED=false  # Disable cache if not using Redis

# Security
JWT_SECRET_KEY=your_generated_secret  # Generate with: openssl rand -hex 32
```

## 📋 Render Start Command

In Render dashboard, set:

```
python api.py
```

Or if using Docker:
```
# Dockerfile CMD is already set correctly
CMD ["python", "api.py"]
```

## 🚨 Memory Troubleshooting

If you still hit 512 MiB limit:

1. **Disable Redis Cache** (if not needed):
   ```
   CACHE_ENABLED=false
   REDIS_URL=
   ```

2. **Reduce Log Verbosity**:
   ```
   LOG_LEVEL=WARNING
   ENABLE_FILE_LOGGING=false
   ```

3. **Skip Heavy Features**:
   - Don't run pipeline from API (use separate worker)
   - Disable company intelligence scraping
   - Use lighter embedding models

4. **Upgrade to Paid Tier**:
   - Render Starter: $7/month (512 MiB → 1 GiB)
   - Render Standard: $25/month (1 GiB → 2 GiB)

## ✅ Verification

After deployment, check logs for:

```
✅ "reload_enabled": false
✅ "is_production": true
✅ "is_container": true
✅ No "Started reloader process" message
✅ Server starts on correct PORT
```

## 📝 Notes

- **Data Persistence**: Render's free tier has ephemeral disk. Use Render Disk or external storage for persistent data.
- **Build Time**: First build may take 5-10 minutes (installing PyTorch, Playwright, etc.)
- **Health Checks**: Health endpoint at `/health` is checked every 30s

