# Vercel Frontend Deployment Guide

This guide explains how to deploy the frontend to Vercel while keeping the backend API separate.

**This repository is configured for backend-only deployment by default.** The frontend is served separately from Vercel, and the backend Docker image does not include frontend files.

## Architecture

- **Backend API**: Deployed separately (Docker, Render, DigitalOcean, etc.) - **backend-only, no frontend included**
- **Frontend**: Deployed on Vercel (separate deployment)
- **Communication**: Frontend calls backend API via CORS

## Backend-Only Configuration

The backend is configured for backend-only deployment:
- `Dockerfile` excludes frontend by default (`BUILD_FRONTEND=false`)
- `.dockerignore` excludes frontend build artifacts
- CORS is configured via `ALLOWED_ORIGINS` environment variable
- API endpoints only - no static file serving for frontend

## Prerequisites

1. Vercel account (sign up at [vercel.com](https://vercel.com))
2. Backend API deployed and accessible
3. Git repository with frontend code

## Deployment Steps

### 1. Prepare Frontend for Vercel

The frontend is already configured for Vercel deployment. The `vercel.json` file is in the `frontend/` directory.

### 2. Set Environment Variables in Vercel

1. Go to your Vercel project settings
2. Navigate to **Settings** → **Environment Variables**
3. Add the following variable:

```
VITE_API_BASE_URL=https://your-backend-api-url.com
```

**Important**: Replace `https://your-backend-api-url.com` with your actual backend API URL.

### 3. Deploy to Vercel

#### Option A: Deploy via Vercel Dashboard

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your Git repository
3. Set the **Root Directory** to `frontend`
4. Vercel will auto-detect the framework (Vite)
5. Add the `VITE_API_BASE_URL` environment variable
6. Click **Deploy**

#### Option B: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Navigate to frontend directory
cd frontend

# Deploy
vercel

# Follow the prompts:
# - Link to existing project or create new
# - Set root directory to current directory
# - Add environment variables when prompted
```

#### Option C: Deploy via Git Push

1. Connect your repository to Vercel
2. Set root directory to `frontend` in project settings
3. Push to your main branch - Vercel will auto-deploy

### 4. Configure Backend CORS

Make sure your backend API allows requests from your Vercel domain:

```bash
# In your backend .env file or deployment platform environment variables, add:
ALLOWED_ORIGINS=https://your-app.vercel.app,https://your-app-git-main.vercel.app,https://your-custom-domain.com
```

**Important**: Include both your production Vercel domain AND preview deployment domains (format: `*-git-<branch>.vercel.app`) if you want branch previews to work.

You can also include multiple domains separated by commas:
```
ALLOWED_ORIGINS=https://my-app.vercel.app,https://my-app-git-main.vercel.app,https://my-app-git-feature.vercel.app,https://myapp.com
```

## Environment Variables

### Required

- `VITE_API_BASE_URL`: Your backend API URL (e.g., `https://api.example.com`)

### Optional

- `VITE_API_BASE_URL` can also be set at build time or injected at runtime

## Custom Domain

1. Go to your Vercel project → **Settings** → **Domains**
2. Add your custom domain
3. Update `ALLOWED_ORIGINS` in backend to include your custom domain

## Troubleshooting

### CORS Errors

If you see CORS errors:
1. Check that `ALLOWED_ORIGINS` in backend includes your Vercel domain
2. Verify `VITE_API_BASE_URL` is set correctly
3. Check browser console for specific error messages

### API Connection Issues

1. Verify backend API is accessible from browser
2. Check backend health endpoint: `https://your-api.com/health`
3. Verify `VITE_API_BASE_URL` matches your backend URL exactly

### Build Errors

1. Check Vercel build logs
2. Ensure all dependencies are in `package.json`
3. Verify Node.js version (Vercel auto-detects, but you can specify in `package.json`)

## Development

For local development with Vercel frontend:

```bash
cd frontend

# Create .env.local file
echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local

# Run dev server
npm run dev
```

## Production Checklist

- [ ] Backend API deployed and accessible
- [ ] `VITE_API_BASE_URL` set in Vercel environment variables
- [ ] Backend `ALLOWED_ORIGINS` includes Vercel domain
- [ ] Custom domain configured (if needed)
- [ ] SSL/HTTPS enabled on backend
- [ ] Environment variables set correctly

## Example Configuration

### Backend (.env)
```bash
ALLOWED_ORIGINS=https://my-app.vercel.app,https://myapp.com
ENABLE_AUTH=true
JWT_SECRET_KEY=your-secret-key
```

### Vercel Environment Variables
```
VITE_API_BASE_URL=https://api.myapp.com
```

## Support

For issues:
1. Check Vercel deployment logs
2. Check backend API logs
3. Verify environment variables are set correctly
4. Test API connectivity from browser console

