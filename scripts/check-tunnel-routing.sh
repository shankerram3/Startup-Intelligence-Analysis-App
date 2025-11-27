#!/bin/bash
# Check Cloudflare Tunnel routing configuration and provide solutions

set -e

TUNNEL_ID="da732ca6-02df-4f81-b72f-a98eac676aeb"
PROBLEM_URL="calibration-benz-syndication-calvin.trycloudflare.com"

echo "🔍 Cloudflare Tunnel Routing Analysis"
echo "======================================"
echo ""

echo "📊 Current Status:"
echo "------------------"

# Check if tunnel container is running
if docker ps --format "{{.Names}}" | grep -q "^cloudflare-tunnel$"; then
    echo "✅ Tunnel container is running"
    
    # Get tunnel connection status
    CONNECTIONS=$(docker logs cloudflare-tunnel 2>&1 | grep -c "Registered tunnel connection" || echo "0")
    if [ "$CONNECTIONS" -gt 0 ]; then
        echo "✅ Tunnel is connected to Cloudflare ($CONNECTIONS active connections)"
    else
        echo "⚠️  Tunnel container running but no active connections found"
    fi
else
    echo "❌ Tunnel container is not running"
    exit 1
fi

# Check backend health
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy on port 8000"
else
    echo "❌ Backend is not responding on port 8000"
    exit 1
fi

echo ""
echo "🔴 Problem Identified:"
echo "----------------------"
echo "URL being used: https://$PROBLEM_URL"
echo "Error: 530 (Cloudflare can't route to origin)"
echo ""
echo "This means:"
echo "  - ✅ Tunnel is connected to Cloudflare"
echo "  - ✅ Backend is running"
echo "  - ❌ Cloudflare Dashboard routing is not configured for this URL"
echo ""

echo "💡 Solutions:"
echo "============="
echo ""
echo "Option 1: Check Cloudflare Dashboard Configuration (RECOMMENDED)"
echo "-----------------------------------------------------------------"
echo "1. Go to: https://dash.cloudflare.com"
echo "2. Navigate to: Zero Trust → Networks → Tunnels"
echo "3. Click on tunnel ID: $TUNNEL_ID"
echo "4. Go to 'Public Hostnames' tab"
echo "5. Check what URL is configured there"
echo "6. If different from '$PROBLEM_URL', update your Flutter app to use the correct URL"
echo "7. Verify the routing points to: http://localhost:8000"
echo ""

echo "Option 2: Create a Quick Temporary Tunnel (FOR IMMEDIATE TESTING)"
echo "-------------------------------------------------------------------"
echo "Run this command to get a working URL immediately:"
echo ""
echo "  cloudflared tunnel --url http://localhost:8000"
echo ""
echo "This will output a new URL like: https://xxxxx.trycloudflare.com"
echo "⚠️  Note: This is temporary and will stop when you close the terminal"
echo ""

echo "Option 3: Fix Dashboard Routing"
echo "--------------------------------"
echo "If you need to configure routing in Cloudflare Dashboard:"
echo "1. Go to tunnel configuration in Dashboard"
echo "2. Add or edit a Public Hostname with:"
echo "   - Subdomain: (your choice or leave blank for trycloudflare.com)"
echo "   - Domain: trycloudflare.com (or your custom domain)"
echo "   - Service: http://localhost:8000"
echo "3. Save and wait 1-2 minutes for changes to propagate"
echo ""

echo "🔧 Quick Test:"
echo "--------------"
echo "To test if the tunnel can reach your backend, try:"
echo "  curl -v http://localhost:8000/health"
echo ""
echo "Expected: Should return JSON with status: healthy"
echo ""

echo "📝 Next Steps:"
echo "--------------"
echo "1. Check Cloudflare Dashboard for the correct tunnel URL"
echo "2. Update your Flutter app to use that URL"
echo "3. Or create a quick temporary tunnel for testing"
echo ""

