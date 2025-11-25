# Memory Optimization for Render Deployment

## Problem

The default Dockerfile includes Playwright and Chromium browser, which adds ~500MB+ memory usage. This causes out-of-memory errors on Render's starter plan (512MB limit).

## Solution

We've created an optimized Dockerfile (`Dockerfile.api`) that excludes Playwright since the API doesn't need it.

### Memory Savings

| Component | Memory Usage | Included in API? |
|-----------|--------------|------------------|
| Playwright browsers | ~500MB | ❌ No (not needed) |
| Playwright deps | ~100MB | ❌ No (not needed) |
| Python runtime | ~150MB | ✅ Yes |
| Application code | ~50MB | ✅ Yes |
| **Total (optimized)** | **~200MB** | ✅ |
| **Total (with Playwright)** | **~800MB** | ❌ Too large |

## Files

1. **`Dockerfile.api`** - Optimized for API deployment (no Playwright)
2. **`requirements-api.txt`** - Requirements without Playwright
3. **`Dockerfile`** - Full version with Playwright (for local pipeline runs)

## Usage

### Render Deployment (Recommended)

Render automatically uses `Dockerfile.api` as configured in `render.yaml`:
```yaml
dockerfilePath: ./Dockerfile.api
```

### Local Development

For API-only:
```bash
docker build -f Dockerfile.api -t graphrag-api .
docker run -p 8000:8000 graphrag-api
```

For full pipeline (with Playwright):
```bash
docker build -f Dockerfile -t graphrag-full .
docker run -p 8000:8000 graphrag-full
```

## Why Playwright Isn't Needed for API

The API (`api.py`) only:
- Queries the Neo4j graph database
- Processes RAG queries
- Serves frontend static files
- Provides REST endpoints

It does NOT:
- Scrape websites (that's `pipeline.py`)
- Run Playwright browsers
- Need Chromium or browser dependencies

## Verification

Check that Playwright isn't imported in the API:
```bash
grep -r "playwright\|Playwright" api.py
# Should return nothing
```

## Render Plan Recommendations

- **Starter Plan (512MB)**: Use `Dockerfile.api` ✅
- **Standard Plan (1GB)**: Can use either, but `Dockerfile.api` is still recommended
- **Pro Plan (2GB+)**: Either works, but optimized version is still better

## Troubleshooting

If you get "Playwright not found" errors:
- This means you're trying to run `pipeline.py` in the API container
- Pipeline should run separately (not in the API service)
- API only serves queries, pipeline builds the graph

