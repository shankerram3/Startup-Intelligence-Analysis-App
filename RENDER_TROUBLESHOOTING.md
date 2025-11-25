# Render Deployment Troubleshooting

## Port Detection Issues

### Problem: "No open ports detected"

**Symptoms:**
- Service starts but Render can't detect the port
- Logs show app running on correct port but deployment fails

**Solution:**
The code has been updated to:
1. Use the app object directly in `uvicorn.run()` instead of string reference
2. Explicitly bind to `0.0.0.0` (required for Render's port scanner)
3. Ensure PORT environment variable is read correctly

**If issue persists:**
- Check that `PORT` environment variable is not overridden
- Verify uvicorn is binding to `0.0.0.0` not `127.0.0.1`
- Ensure no firewall rules block the port

## Redis Connection Issues

### Problem: "Redis connection failed: Connection refused"

**Symptoms:**
- Warning: `⚠️ Redis connection failed: Error 111 connecting to localhost:6379`
- Caching is disabled

**Solution:**
1. **If using Render Redis:**
   - Create Redis service in Render Dashboard
   - Set environment variables:
     - `REDIS_HOST` → (from Redis service connection string)
     - `REDIS_PORT` → `6379`
   - Update `REDIS_HOST` to use the Redis service hostname (not localhost)

2. **If not using Redis:**
   - Set `CACHE_ENABLED=false` in environment variables
   - Application will work without caching (slower but functional)

**Note:** The app will automatically disable caching if Redis is unavailable, so this warning is non-fatal.

## JWT Secret Key Warning

### Problem: "JWT_SECRET_KEY not set. Using development key"

**Solution:**
Set `JWT_SECRET_KEY` environment variable in Render Dashboard:
```bash
# Generate a secure key:
openssl rand -hex 32

# Or use Python:
python -c "import secrets; print(secrets.token_hex(32))"
```

Then set it in Render Dashboard → Environment Variables.

## Environment Variables Checklist

Ensure these are set in Render Dashboard:

**Required:**
- ✅ `OPENAI_API_KEY`
- ✅ `NEO4J_URI`
- ✅ `NEO4J_USER`
- ✅ `NEO4J_PASSWORD`

**Recommended:**
- ✅ `JWT_SECRET_KEY` (generate secure random string)
- ✅ `ALLOWED_ORIGINS` (update with your Render URL after deployment)
- ✅ `REDIS_HOST` (if using Redis)
- ✅ `REDIS_PORT` (if using Redis)

**Optional:**
- `CACHE_ENABLED` (default: true)
- `LOG_LEVEL` (default: INFO)
- `ENABLE_AUTH` (default: false)

## Common Issues

### Service starts but returns 503

**Cause:** RAG instance not initialized (database connection issue)

**Solution:**
- Check Neo4j connection string format
- Verify Neo4j credentials
- Check if Neo4j instance is accessible from Render

### Frontend not loading

**Cause:** Static files not built or not served correctly

**Solution:**
- Check Docker build logs for frontend compilation
- Verify `frontend/dist` directory exists in Docker image
- Check API logs for static file serving errors

### Slow response times

**Cause:** No Redis caching or free tier limitations

**Solution:**
- Enable Redis caching (create Render Redis service)
- Consider upgrading to paid plan (no spin-down)
- Check Neo4j query performance

## Getting Help

1. **Check Render Logs:**
   - Dashboard → Your Service → Logs
   - Look for errors or warnings

2. **Test Health Endpoint:**
   ```bash
   curl https://your-service.onrender.com/health
   ```

3. **Check API Docs:**
   ```bash
   open https://your-service.onrender.com/docs
   ```

4. **Verify Environment Variables:**
   - Dashboard → Your Service → Environment
   - Ensure all required variables are set

5. **Review Build Logs:**
   - Check if Docker build completed successfully
   - Verify frontend was built correctly

## Still Having Issues?

1. Check the main deployment guide: `RENDER_DEPLOYMENT.md`
2. Review Render documentation: https://render.com/docs
3. Check application logs for specific error messages
4. Verify all environment variables are correctly set

