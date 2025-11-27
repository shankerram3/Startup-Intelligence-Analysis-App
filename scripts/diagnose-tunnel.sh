#!/bin/bash
# Diagnose and help fix Cloudflare Tunnel issues

set -e

echo "🔍 Cloudflare Tunnel Diagnostic"
echo "================================"
echo ""

# Check if tunnel container is running
echo "1. Checking tunnel container..."
if docker ps --format "{{.Names}}" | grep -q "^cloudflare-tunnel$"; then
    echo "   ✅ Tunnel container is running"
    
    # Check tunnel logs for errors
    echo ""
    echo "2. Recent tunnel logs (last 20 lines):"
    docker logs cloudflare-tunnel --tail 20 2>&1 | grep -i "error\|fail\|registered\|origin" || docker logs cloudflare-tunnel --tail 5
    
else
    echo "   ❌ Tunnel container is not running"
    echo ""
    echo "   To start it, run:"
    echo "   ./run-cloudflare-tunnel.sh YOUR_TOKEN"
    exit 1
fi

# Check backend health
echo ""
echo "3. Checking backend health..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ Backend is healthy on port 8000"
    curl -s http://localhost:8000/health | jq -r '.status // "OK"' 2>/dev/null || echo "   Backend responded"
else
    echo "   ❌ Backend is not responding on port 8000"
    echo ""
    echo "   Check if the backend container is running:"
    echo "   docker ps | grep graphrag-api"
    exit 1
fi

# Check port 8000 is listening
echo ""
echo "4. Checking if port 8000 is listening..."
if ss -tlnp 2>/dev/null | grep -q ":8000" || netstat -tlnp 2>/dev/null | grep -q ":8000"; then
    echo "   ✅ Port 8000 is listening"
else
    echo "   ❌ Port 8000 is not listening"
    exit 1
fi

echo ""
echo "================================"
echo "✅ Local checks passed!"
echo ""
echo "📋 Next Steps:"
echo ""
echo "The 530 error means Cloudflare can't route to your backend."
echo ""
echo "Option 1: Fix Cloudflare Dashboard Configuration (Recommended for persistent tunnel)"
echo "---------------------------------------------------"
echo "1. Go to: https://dash.cloudflare.com → Zero Trust → Networks → Tunnels"
echo "2. Click on your tunnel (ID: da732ca6-02df-4f81-b72f-a98eac676aeb)"
echo "3. Go to 'Public Hostnames' or 'Routing' tab"
echo "4. Check the ingress rules - they should route to: http://localhost:8000"
echo "5. Ensure your tunnel URL matches what you're using in your Flutter app"
echo ""
echo "Option 2: Use a Quick Temporary Tunnel (For testing)"
echo "---------------------------------------------------"
echo "Run this command to get a new temporary URL:"
echo "  cloudflared tunnel --url http://localhost:8000"
echo ""
echo "This will give you a new URL like: https://xxxxx.trycloudflare.com"
echo "Update your Flutter app to use this new URL"
echo ""
echo "Option 3: Restart the Tunnel"
echo "---------------------------------------------------"
echo "Sometimes restarting the tunnel fixes connectivity issues:"
echo "  docker restart cloudflare-tunnel"
echo "  docker logs -f cloudflare-tunnel"
echo ""

