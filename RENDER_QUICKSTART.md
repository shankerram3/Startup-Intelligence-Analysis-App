# Quick Start: Deploy to Render

This is a quick reference guide. See `RENDER_DEPLOYMENT.md` for full documentation.

## Step 1: Push to Git

```bash
git add .
git commit -m "Prepare for Render deployment"
git push
```

## Step 2: Deploy on Render

### Option A: Using Blueprint (Recommended)

1. Go to [render.com](https://render.com) → Dashboard → New → Blueprint
2. Connect your repository
3. Render will auto-detect `render.yaml`
4. Click "Apply"

### Option B: Manual Service Creation

1. Go to Dashboard → New → Web Service
2. Connect repository
3. Settings:
   - **Name**: `graphrag-api`
   - **Environment**: Docker
   - **Dockerfile Path**: `Dockerfile`
   - **Docker Context**: `.`

## Step 3: Configure Environment Variables

In Render Dashboard → Your Service → Environment:

**Required:**
```
OPENAI_API_KEY=sk-your-key
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
```

**Optional (with defaults):**
```
ALLOWED_ORIGINS=https://your-service.onrender.com
CACHE_ENABLED=true
LOG_LEVEL=INFO
```

## Step 4: Deploy!

Render will automatically:
- Build the Docker image
- Start the service
- Provide a URL like `https://graphrag-api.onrender.com`

## Step 5: Test

```bash
# Health check
curl https://your-service.onrender.com/health

# API docs
open https://your-service.onrender.com/docs

# Frontend
open https://your-service.onrender.com
```

## Redis (Optional)

To enable caching:

1. Dashboard → New → Redis
2. Name: `graphrag-redis`
3. In your Web Service, add environment variables:
   - `REDIS_HOST` → (from Redis service)
   - `REDIS_PORT` → `6379`

## Troubleshooting

- **Service won't start**: Check logs in Render Dashboard
- **Database connection failed**: Verify `NEO4J_URI` format
- **Frontend not loading**: Check build logs for frontend compilation

## Next Steps

- See `RENDER_DEPLOYMENT.md` for detailed docs
- Configure custom domain in Render Dashboard
- Set up auto-deploy on git push

---

**That's it!** Your app should be live on Render 🚀

