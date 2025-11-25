# Cloudflare Setup Guide

## Option 1: Cloudflare Tunnel (Recommended - No IP Exposure)

Cloudflare Tunnel creates a secure connection without exposing your IP address or needing DNS records.

### Step 1: Install Cloudflared

```bash
# Download and install
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Verify installation
cloudflared --version
```

### Step 2: Authenticate

```bash
# This will open a browser for you to log in
cloudflared tunnel login
```

### Step 3: Create a Named Tunnel (Persistent)

```bash
# Create a named tunnel
cloudflared tunnel create graphrag-api

# This creates a tunnel with a UUID
# Note the tunnel ID from the output
```

### Step 4: Configure the Tunnel

Create configuration file `~/.cloudflared/config.yml`:

```yaml
tunnel: <your-tunnel-id>
credentials-file: /home/your-user/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: graphrag-api.your-subdomain.workers.dev
    service: http://localhost:8000
  - service: http_status:404
```

Or for a quick test (temporary URL):

```bash
# This gives you a temporary URL like: https://xxxxx.trycloudflare.com
cloudflared tunnel --url http://localhost:8000
```

### Step 5: Run Tunnel as Service (Persistent)

```bash
# Install as systemd service
sudo cloudflared service install

# Start the tunnel
cloudflared tunnel run graphrag-api

# Or run in background
nohup cloudflared tunnel run graphrag-api > /dev/null 2>&1 &
```

### Step 6: Update Vercel

Set `VITE_API_BASE_URL` in Vercel to your Cloudflare tunnel URL:
- Temporary: `https://xxxxx.trycloudflare.com`
- Named tunnel: `https://graphrag-api.your-subdomain.workers.dev`

---

## Option 2: Cloudflare DNS with A Record (If You Have a Domain)

If you want to use your own domain with Cloudflare's proxy and add your IP address:

### Step 1: Add Domain to Cloudflare

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Click "Add a Site" or "Add Site"
3. Enter your domain name (e.g., `yourdomain.com`)
4. Select a plan (Free plan works fine)
5. Follow the setup wizard

### Step 2: Update Nameservers at Your Registrar

Cloudflare will provide nameservers (e.g., `alice.ns.cloudflare.com`, `bob.ns.cloudflare.com`):

1. Go to your domain registrar (GoDaddy, Namecheap, Google Domains, etc.)
2. Find DNS/Nameserver settings
3. Replace existing nameservers with Cloudflare's provided nameservers
4. Save changes
5. Wait for DNS propagation (usually 1-2 hours, can take up to 24 hours)

**Verify nameservers are updated:**
```bash
# Check if nameservers are pointing to Cloudflare
dig NS yourdomain.com
# Should show Cloudflare nameservers
```

### Step 3: Add A Record with Your IP Address

1. Go to Cloudflare Dashboard → Select your domain → **DNS** → **Records**
2. Click **"Add record"**
3. Configure the A record:
   - **Type**: `A`
   - **Name**: `api` (creates `api.yourdomain.com`) or `@` (for root domain `yourdomain.com`)
   - **IPv4 address**: `167.172.26.46` (your server IP)
   - **Proxy status**: 🟠 **Proxied** (orange cloud) - **CRITICAL for HTTPS**
   - **TTL**: Auto
4. Click **"Save"**

**Important:** The orange cloud (Proxied) must be ON. This:
- Hides your real IP address
- Provides HTTPS automatically
- Enables Cloudflare's CDN and DDoS protection

### Step 4: Configure SSL/TLS

1. Go to **SSL/TLS** → **Overview**
2. Set encryption mode to **"Full"** or **"Full (strict)"**
   - **Full**: Cloudflare ↔ Origin (your server) can be HTTP
   - **Full (strict)**: Requires valid SSL on your server too
3. Cloudflare will automatically provision SSL certificate (usually within minutes)

### Step 5: Verify DNS is Working

```bash
# Check if DNS resolves correctly
dig api.yourdomain.com
# Should return: 167.172.26.46 (or Cloudflare IP if proxied)

# Test HTTPS
curl https://api.yourdomain.com/health
```

### Step 6: Update Backend Configuration

Update your backend `.env` or docker-compose to ensure it accepts requests:

```bash
# In your .env file
ALLOWED_ORIGINS=https://your-app.vercel.app,https://api.yourdomain.com
```

### Step 7: Update Vercel

Set `VITE_API_BASE_URL` in Vercel to:
```
https://api.yourdomain.com
```

Then redeploy your Vercel app.

---

## Which Option to Choose?

### Use Cloudflare Tunnel if:
- ✅ You don't have a domain
- ✅ You want to hide your IP address
- ✅ You want quick setup (5 minutes)
- ✅ You want free HTTPS

### Use Cloudflare DNS if:
- ✅ You have a domain name
- ✅ You want to use your own domain
- ✅ You want Cloudflare's CDN and DDoS protection
- ✅ You're okay with exposing your IP (though Cloudflare proxy helps)

---

## Quick Start (Cloudflare Tunnel - Recommended)

For your use case, Cloudflare Tunnel is the easiest:

```bash
# 1. Install
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# 2. Quick test (temporary URL)
cloudflared tunnel --url http://localhost:8000

# Copy the URL it gives you (e.g., https://xxxxx.trycloudflare.com)
# Update VITE_API_BASE_URL in Vercel to this URL
# Redeploy Vercel app
```

For persistent setup:

```bash
# 3. Create named tunnel
cloudflared tunnel login
cloudflared tunnel create graphrag-api

# 4. Configure (edit ~/.cloudflared/config.yml with your tunnel ID)
# 5. Run
cloudflared tunnel run graphrag-api
```

---

## Troubleshooting

### Tunnel not connecting
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check tunnel status
cloudflared tunnel list
cloudflared tunnel info graphrag-api
```

### DNS not working
- Wait for DNS propagation (can take 1-24 hours)
- Verify nameservers are correct at your registrar
- Check Cloudflare DNS settings

### SSL errors
- Ensure proxy is enabled (orange cloud) in Cloudflare
- Set SSL/TLS mode to "Full" or "Full (strict)"
- Wait a few minutes for SSL certificate to provision

