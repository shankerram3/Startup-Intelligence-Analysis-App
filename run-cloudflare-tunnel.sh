#!/bin/bash
# Run Cloudflare Tunnel using Docker
# This provides HTTPS access to your backend API

set -e

# Check if token is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <cloudflare-tunnel-token>"
    echo ""
    echo "Or set CLOUDFLARE_TUNNEL_TOKEN environment variable:"
    echo "  export CLOUDFLARE_TUNNEL_TOKEN=your-token-here"
    echo "  $0"
    exit 1
fi

TOKEN="${1:-${CLOUDFLARE_TUNNEL_TOKEN}}"

if [ -z "$TOKEN" ]; then
    echo "Error: Cloudflare Tunnel token required"
    exit 1
fi

echo "🚇 Starting Cloudflare Tunnel..."
echo ""

# Stop existing tunnel if running
docker stop cloudflare-tunnel 2>/dev/null || true
docker rm cloudflare-tunnel 2>/dev/null || true

# Run tunnel
docker run -d \
  --name cloudflare-tunnel \
  --restart unless-stopped \
  --network host \
  cloudflare/cloudflared:latest \
  tunnel --no-autoupdate run --token "$TOKEN"

echo ""
echo "✅ Cloudflare Tunnel started!"
echo ""
echo "Check logs:"
echo "  docker logs -f cloudflare-tunnel"
echo ""
echo "Stop tunnel:"
echo "  docker stop cloudflare-tunnel"
echo ""

