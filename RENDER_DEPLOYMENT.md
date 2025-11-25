# Render Platform Deployment Guide

This guide walks you through deploying the GraphRAG application to Render.

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **Neo4j Database**: 
   - Option A: Use [Neo4j Aura](https://neo4j.com/cloud/aura/) (Recommended)
   - Option B: Self-hosted Neo4j instance
3. **Environment Variables**: Prepare your API keys and credentials

## Quick Start

### Option 1: Using render.yaml (Recommended)

1. **Connect Your Repository**:
   - Push this repository to GitHub/GitLab/Bitbucket
   - Go to Render Dashboard → New → Blueprint
   - Connect your repository
   - Render will automatically detect `render.yaml`

2. **Set Required Environment Variables**:
   Go to your service settings and add:
   ```
   OPENAI_API_KEY=sk-your-openai-api-key
   NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io  # Aura URI
   # OR for self-hosted:
   # NEO4J_URI=bolt://your-neo4j-host:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your-password
   ```

3. **Deploy**:
   - Render will automatically build and deploy
   - Your app will be available at `https://your-service.onrender.com`

### Option 2: Manual Service Creation

1. **Create Web Service**:
   - Go to Render Dashboard → New → Web Service
   - Connect your repository
   - Use these settings:
     - **Build Command**: (leave empty, Docker handles it)
     - **Start Command**: `python api.py`
     - **Dockerfile Path**: `Dockerfile`
     - **Docker Context**: `.`

2. **Create Redis Service** (Optional but recommended):
   - Go to Render Dashboard → New → Redis
   - Name: `graphrag-redis`
   - Plan: Starter (free tier available)
   - Add Redis connection details to Web Service env vars:
     - `REDIS_HOST` → (from Redis service)
     - `REDIS_PORT` → (from Redis service)

3. **Set Environment Variables** (in Web Service):
   ```
   # Required
   OPENAI_API_KEY=sk-your-openai-api-key
   NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your-password
   
   # API Configuration
   API_HOST=0.0.0.0
   # PORT is automatically set by Render, don't override it
   
   # Redis (if using Render Redis)
   CACHE_ENABLED=true
   REDIS_HOST=red-xxxxx  # From your Redis service
   REDIS_PORT=6379       # From your Redis service
   
   # Security
   ALLOWED_ORIGINS=https://your-service.onrender.com
   ENABLE_AUTH=false  # Set to true for production with auth
   JWT_SECRET_KEY=your-secret-key-here  # Generate a random string
   
   # Logging
   LOG_LEVEL=INFO
   JSON_LOGS=true
   ```

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for entity extraction | `sk-...` |
| `NEO4J_URI` | Neo4j connection URI | `neo4j+s://xxxxx.databases.neo4j.io` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `your-password` |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | API host (don't change) |
| `API_PORT` | Auto-set | Port (Render sets `PORT` automatically) |
| `CACHE_ENABLED` | `true` | Enable Redis caching |
| `REDIS_HOST` | - | Redis host (from Render Redis service) |
| `REDIS_PORT` | `6379` | Redis port |
| `ALLOWED_ORIGINS` | - | CORS allowed origins (comma-separated) |
| `ENABLE_AUTH` | `false` | Enable JWT authentication |
| `JWT_SECRET_KEY` | Auto-generated | JWT secret (generate random string) |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `JSON_LOGS` | `true` | Use JSON-formatted logs |

## Post-Deployment Configuration

### 1. Update CORS Origins

After deployment, update `ALLOWED_ORIGINS` in Render dashboard to include your Render URL:
```
ALLOWED_ORIGINS=https://your-service.onrender.com
```

### 2. Test Health Endpoint

```bash
curl https://your-service.onrender.com/health
```

### 3. Access the Application

- **Frontend**: `https://your-service.onrender.com`
- **API Docs**: `https://your-service.onrender.com/docs`
- **Health Check**: `https://your-service.onrender.com/health`
- **Metrics**: `https://your-service.onrender.com/metrics`

## Neo4j Setup

### Using Neo4j Aura (Recommended)

1. **Create Aura Instance**:
   - Go to [console.neo4j.io](https://console.neo4j.io)
   - Create a new Aura instance
   - Choose the free tier (up to 50K nodes)

2. **Get Connection Details**:
   - Copy the connection URI (format: `neo4j+s://xxxxx.databases.neo4j.io`)
   - Note the username and password

3. **Configure in Render**:
   - Set `NEO4J_URI` environment variable
   - Set `NEO4J_USER` (usually `neo4j`)
   - Set `NEO4J_PASSWORD`

### Using Self-Hosted Neo4j

1. Ensure your Neo4j instance is accessible from the internet
2. Use bolt URI: `bolt://your-neo4j-host:7687`
3. Configure firewall to allow connections from Render IPs

## Redis Setup (Optional)

Render provides managed Redis:

1. **Create Redis Service**:
   - Render Dashboard → New → Redis
   - Choose Starter plan (free tier available)
   - Note the connection details

2. **Link to Web Service**:
   - In your Web Service settings
   - Add environment variables from Redis service
   - Or use `render.yaml` which handles this automatically

3. **Benefits**:
   - Faster query responses
   - Reduced database load
   - Better performance for repeated queries

## Monitoring & Logs

### View Logs
- Render Dashboard → Your Service → Logs
- Or use Render CLI: `render logs -s your-service`

### Health Checks
- Render automatically monitors `/health` endpoint
- Check service health in dashboard

### Metrics
- Access Prometheus metrics at `/metrics`
- Use monitoring tools to scrape metrics

## Troubleshooting

### Service Won't Start

1. **Check Logs**:
   ```bash
   render logs -s your-service
   ```

2. **Common Issues**:
   - Missing environment variables
   - Neo4j connection failed
   - Port configuration error

### Database Connection Issues

1. **Verify Neo4j URI**:
   - Check `NEO4J_URI` format
   - For Aura: Use `neo4j+s://` (secure)
   - For self-hosted: Use `bolt://` or `neo4j://`

2. **Test Connection**:
   ```bash
   curl https://your-service.onrender.com/health
   ```
   Should show `"database": "connected"`

### Frontend Not Loading

1. **Check if Frontend is Built**:
   - Docker build should include frontend
   - Check build logs for frontend compilation

2. **Check CORS Settings**:
   - Verify `ALLOWED_ORIGINS` includes your Render URL
   - Check browser console for CORS errors

### Slow Performance

1. **Enable Redis Caching**:
   - Create Redis service
   - Link to Web Service
   - Set `CACHE_ENABLED=true`

2. **Check Render Plan**:
   - Free tier has resource limits
   - Consider upgrading to paid plan

## Cost Estimation

### Free Tier
- **Web Service**: 750 hours/month (spins down after 15 min inactivity)
- **Redis**: 25MB storage

### Paid Tier (Recommended for Production)
- **Starter Plan**: $7/month per service
- Better performance, no spin-down
- More resources

## Next Steps

1. **Run Data Pipeline**:
   - Use the pipeline to populate your graph
   - See `README.md` for pipeline usage

2. **Set Up Authentication** (Production):
   - Enable `ENABLE_AUTH=true`
   - Configure user accounts
   - Set strong `JWT_SECRET_KEY`

3. **Configure Custom Domain**:
   - Render Dashboard → Settings → Custom Domain
   - Add your domain
   - Update DNS records

4. **Set Up CI/CD**:
   - Connect to GitHub
   - Auto-deploy on push to main branch

## Support

- **Render Docs**: [render.com/docs](https://render.com/docs)
- **Render Status**: [status.render.com](https://status.render.com)
- **Project README**: See `README.md` for application-specific docs

## Security Checklist

- [ ] Use strong `JWT_SECRET_KEY`
- [ ] Enable authentication (`ENABLE_AUTH=true`) for production
- [ ] Configure `ALLOWED_ORIGINS` properly
- [ ] Use HTTPS (Render provides automatically)
- [ ] Keep environment variables secure
- [ ] Regularly update dependencies
- [ ] Monitor logs for suspicious activity

---

**Ready to deploy?** Follow the Quick Start guide above or use the `render.yaml` file for automatic setup!

