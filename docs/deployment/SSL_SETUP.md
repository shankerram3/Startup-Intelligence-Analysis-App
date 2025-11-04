# SSL/HTTPS Setup Guide for Azure VM

This guide shows you how to set up HTTPS with a custom domain and SSL certificate for your GraphRAG API on Azure.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Option 1: Using a Custom Domain (Recommended)](#option-1-using-a-custom-domain-recommended)
3. [Option 2: Using Azure Public IP DNS Label](#option-2-using-azure-public-ip-dns-label)
4. [Option 3: Self-Signed Certificate (Development)](#option-3-self-signed-certificate-development)
5. [Nginx Configuration](#nginx-configuration)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting:
- Your Azure VM is running
- GraphRAG API is working on port 8000
- You have SSH access to your VM
- (Optional) You own a domain name

---

## Option 1: Using a Custom Domain (Recommended)

### Step 1: Get Your VM's Public IP

```bash
# On Azure Portal or from your VM
curl ifconfig.me
```

Note this IP address (e.g., `20.1.2.3`)

### Step 2: Configure DNS

In your domain registrar (GoDaddy, Namecheap, Cloudflare, etc.):

1. Create an **A Record**:
   - Name: `api` (or `graphrag`, or `@` for root domain)
   - Type: `A`
   - Value: Your VM's public IP
   - TTL: 3600 (or automatic)

Examples:
- `api.yourdomain.com` → `20.1.2.3`
- `graphrag.yourdomain.com` → `20.1.2.3`

Wait 5-60 minutes for DNS propagation.

### Step 3: Verify DNS

```bash
# From your local machine
nslookup api.yourdomain.com

# Or
dig api.yourdomain.com
```

Should return your VM's IP address.

### Step 4: Install Nginx

```bash
# SSH into your VM
ssh azureuser@<your-vm-ip>

# Install Nginx
sudo apt update
sudo apt install -y nginx

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### Step 5: Install Certbot (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx
```

### Step 6: Configure Nginx for Your Domain

```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/graphrag << 'EOF'
server {
    listen 80;
    server_name api.yourdomain.com;  # Replace with your domain

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Replace 'api.yourdomain.com' with your actual domain
sudo sed -i 's/api.yourdomain.com/YOUR_ACTUAL_DOMAIN/g' /etc/nginx/sites-available/graphrag

# Enable the site
sudo ln -sf /etc/nginx/sites-available/graphrag /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Step 7: Get SSL Certificate with Let's Encrypt

```bash
# Get SSL certificate (replace with your domain and email)
sudo certbot --nginx -d api.yourdomain.com --non-interactive --agree-tos -m your-email@example.com

# Certbot will automatically:
# 1. Verify domain ownership
# 2. Get SSL certificate
# 3. Configure Nginx for HTTPS
# 4. Setup auto-renewal
```

### Step 8: Configure Azure Firewall

```bash
# Allow HTTPS traffic
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status
```

In Azure Portal:
1. Go to your VM → **Networking**
2. Add inbound port rules:
   - Port 80 (HTTP)
   - Port 443 (HTTPS)

### Step 9: Test HTTPS

```bash
# From your local machine
curl https://api.yourdomain.com/health

# Should return: {"status": "healthy"}
```

Visit in browser: `https://api.yourdomain.com/docs`

### Step 10: Verify Auto-Renewal

```bash
# Test renewal process
sudo certbot renew --dry-run

# Check renewal timer
sudo systemctl list-timers | grep certbot
```

Let's Encrypt certificates auto-renew every 60 days.

---

## Option 2: Using Azure Public IP DNS Label

If you don't have a domain, Azure provides a free DNS name.

### Step 1: Configure Azure DNS Label

**In Azure Portal:**
1. Go to your VM → **Overview**
2. Click on **Public IP address**
3. Click **Configuration**
4. Set **DNS name label**: `graphrag-yourname` (must be unique)
5. Click **Save**

Your DNS name will be: `graphrag-yourname.eastus2.cloudapp.azure.com`

### Step 2: Install Nginx and Certbot

```bash
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx
```

### Step 3: Configure Nginx

```bash
# Replace with your Azure DNS name
AZURE_DNS="graphrag-yourname.eastus2.cloudapp.azure.com"

sudo tee /etc/nginx/sites-available/graphrag << EOF
server {
    listen 80;
    server_name $AZURE_DNS;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/graphrag /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### Step 4: Get SSL Certificate

```bash
# Get SSL certificate
sudo certbot --nginx -d $AZURE_DNS --non-interactive --agree-tos -m your-email@example.com
```

### Step 5: Test

```bash
# From local machine
curl https://graphrag-yourname.eastus2.cloudapp.azure.com/health
```

---

## Option 3: Self-Signed Certificate (Development)

⚠️ **For development only** - browsers will show security warnings.

### Step 1: Generate Self-Signed Certificate

```bash
# Create certificate directory
sudo mkdir -p /etc/ssl/graphrag

# Generate certificate (valid for 365 days)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/graphrag/selfsigned.key \
  -out /etc/ssl/graphrag/selfsigned.crt \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Set permissions
sudo chmod 600 /etc/ssl/graphrag/selfsigned.key
```

### Step 2: Install Nginx

```bash
sudo apt update
sudo apt install -y nginx
```

### Step 3: Configure Nginx with SSL

```bash
sudo tee /etc/nginx/sites-available/graphrag << 'EOF'
server {
    listen 443 ssl;
    server_name _;

    ssl_certificate /etc/ssl/graphrag/selfsigned.crt;
    ssl_certificate_key /etc/ssl/graphrag/selfsigned.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/graphrag /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### Step 4: Allow HTTPS

```bash
sudo ufw allow 443/tcp
```

### Step 5: Test

```bash
# From local machine (use -k to ignore certificate warning)
curl -k https://<your-vm-ip>/health
```

---

## Nginx Configuration

### Complete Production Nginx Configuration

```nginx
# /etc/nginx/sites-available/graphrag

# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$host$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL Certificates (managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/graphrag_access.log;
    error_log /var/log/nginx/graphrag_error.log;

    # API Proxy
    location / {
        # Rate limiting
        limit_req zone=api_limit burst=20 nodelay;

        # Proxy settings
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (if any)
    location /static {
        alias /home/azureuser/Startup-Intelligence-Analysis-App/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint (no rate limit)
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
```

### Nginx Performance Tuning

```bash
# Edit main Nginx config
sudo vim /etc/nginx/nginx.conf
```

Add/modify these settings:

```nginx
user www-data;
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    # Basic Settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 20M;

    # Gzip Settings
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Include site configurations
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
```

---

## Troubleshooting

### Issue: Certbot fails with "Could not bind to IPv4"

```bash
# Stop Nginx temporarily
sudo systemctl stop nginx

# Try again
sudo certbot --nginx -d api.yourdomain.com

# Start Nginx
sudo systemctl start nginx
```

### Issue: 502 Bad Gateway

```bash
# Check if API is running
sudo systemctl status graphrag-api

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Check API logs
sudo journalctl -u graphrag-api -f

# Test API directly
curl http://localhost:8000/health
```

### Issue: DNS not resolving

```bash
# Check DNS propagation
nslookup api.yourdomain.com
dig api.yourdomain.com

# Wait longer (can take up to 48 hours in rare cases)
# Usually propagates within 5-60 minutes
```

### Issue: Certificate renewal fails

```bash
# Check Certbot logs
sudo cat /var/log/letsencrypt/letsencrypt.log

# Test renewal
sudo certbot renew --dry-run

# Check Certbot timer
sudo systemctl list-timers | grep certbot

# Manually renew if needed
sudo certbot renew
```

### Issue: Mixed content warnings

Make sure all API calls use HTTPS:
```javascript
// Bad
fetch('http://api.yourdomain.com/query')

// Good
fetch('https://api.yourdomain.com/query')
```

---

## Security Best Practices

### 1. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH (consider restricting to your IP)
sudo ufw allow 80/tcp   # HTTP (for Let's Encrypt)
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 2. Restrict SSH Access

```bash
# In Azure NSG, restrict SSH (port 22) to your IP only
# Azure Portal → VM → Networking → SSH rule → Source: My IP address
```

### 3. Disable Password Authentication

```bash
# Edit SSH config
sudo vim /etc/ssh/sshd_config

# Ensure these settings:
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin no

# Restart SSH
sudo systemctl restart sshd
```

### 4. Setup Fail2Ban

```bash
# Install Fail2Ban
sudo apt install -y fail2ban

# Create config
sudo tee /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true
EOF

# Start Fail2Ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 5. Enable Automatic Security Updates

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## Monitoring SSL Certificate

### Setup Certificate Expiry Monitoring

```bash
# Create monitoring script
cat > ~/check_ssl_expiry.sh << 'EOF'
#!/bin/bash
DOMAIN="api.yourdomain.com"
DAYS_UNTIL_EXPIRY=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -checkend $((86400*30)))

if [ $? -eq 0 ]; then
    echo "Certificate is valid for more than 30 days"
else
    echo "WARNING: Certificate expires in less than 30 days!"
    # Send alert (email, Slack, etc.)
fi
EOF

chmod +x ~/check_ssl_expiry.sh

# Add to crontab (check daily)
(crontab -l 2>/dev/null; echo "0 9 * * * /home/azureuser/check_ssl_expiry.sh") | crontab -
```

---

## Complete Setup Example

Here's a complete example from start to finish:

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Nginx and Certbot
sudo apt install -y nginx certbot python3-certbot-nginx

# 3. Configure firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 4. Create Nginx config
sudo tee /etc/nginx/sites-available/graphrag << 'EOF'
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 5. Enable site
sudo ln -sf /etc/nginx/sites-available/graphrag /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# 6. Get SSL certificate
sudo certbot --nginx -d api.yourdomain.com -m your-email@example.com --agree-tos --non-interactive

# 7. Test
curl https://api.yourdomain.com/health

# 8. Done!
echo "SSL setup complete!"
```

---

## Next Steps

- Setup monitoring with Azure Monitor
- Configure API authentication
- Add rate limiting
- Setup CDN (Azure CDN or Cloudflare)
- Configure Web Application Firewall (WAF)

---

**Your API is now secured with HTTPS! 🔒**

For more information:
- [Azure Deployment Guide](AZURE_DEPLOYMENT_GUIDE.md)
- [Quick Start Guide](QUICKSTART_AZURE.md)
- [README](README.md)
