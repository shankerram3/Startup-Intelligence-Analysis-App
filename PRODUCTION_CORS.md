# Production CORS Configuration

## How CORS Works in Production

### Automatic Preview Deployment Support

The backend automatically allows **all Vercel preview deployments** if you configure your **main production domain**.

### Setup

**Step 1: Configure Main Domain**

In your `.env` file, set `ALLOWED_ORIGINS` to your main Vercel production domain:

```bash
ALLOWED_ORIGINS=https://startup-intelligence-analysis-app.vercel.app
```

**Step 2: Restart Backend**

```bash
docker-compose restart graphrag-api
```

### How It Works

1. **Main Domain**: Configure your production domain (e.g., `https://my-app.vercel.app`)
2. **Auto-Allow**: All preview deployments matching your project name are automatically allowed
   - `https://my-app-abc123.vercel.app` ✅
   - `https://my-app-xyz789.vercel.app` ✅
   - `https://my-app-git-main.vercel.app` ✅
   - `https://other-app-abc123.vercel.app` ❌ (different project)

### Examples

**Production Setup:**
```bash
# .env
ALLOWED_ORIGINS=https://startup-intelligence-analysis-app.vercel.app
```

This automatically allows:
- `https://startup-intelligence-analysis-app.vercel.app` (production)
- `https://startup-intelligence-analysis-app-abc123.vercel.app` (preview)
- `https://startup-intelligence-analysis-app-xyz789.vercel.app` (preview)
- `https://startup-intelligence-analysis-app-git-main.vercel.app` (branch preview)

**Multiple Domains:**
```bash
# If you have a custom domain too
ALLOWED_ORIGINS=https://startup-intelligence-analysis-app.vercel.app,https://myapp.com
```

### Verification

Test CORS is working:

```bash
# Test production domain
curl -X OPTIONS "https://your-backend-url/query" \
  -H "Origin: https://startup-intelligence-analysis-app.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -v

# Test preview deployment
curl -X OPTIONS "https://your-backend-url/query" \
  -H "Origin: https://startup-intelligence-analysis-app-abc123.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -v
```

Both should return `access-control-allow-origin` headers.

### Troubleshooting

**If preview deployments still fail:**

1. Check your main domain is correctly configured:
   ```bash
   docker exec graphrag-api env | grep ALLOWED_ORIGINS
   ```

2. Verify the preview domain matches your project name:
   - Main: `my-app.vercel.app`
   - Preview: `my-app-abc123.vercel.app` ✅
   - Preview: `other-app-abc123.vercel.app` ❌

3. Manually add specific preview URL if needed:
   ```bash
   ALLOWED_ORIGINS=https://my-app.vercel.app,https://my-app-abc123.vercel.app
   ```

### Security Notes

- ✅ Only preview deployments from the **same project** are allowed
- ✅ Main domain must be explicitly configured
- ✅ Custom domains must be explicitly added
- ❌ Wildcard `*.vercel.app` is NOT used (too permissive)

