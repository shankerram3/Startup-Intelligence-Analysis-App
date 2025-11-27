#!/bin/bash
# Start both Cloudflare Tunnel and the GraphRAG API server

# Start Cloudflare Tunnel in background if token is provided
if [ -n "$CLOUDFLARE_TUNNEL_TOKEN" ]; then
    echo "🚇 Starting Cloudflare Tunnel..."
    cloudflared tunnel --no-autoupdate run --token "$CLOUDFLARE_TUNNEL_TOKEN" &
    echo "✅ Cloudflare Tunnel started in background"
    sleep 2  # Give tunnel time to connect
else
    echo "⚠️  CLOUDFLARE_TUNNEL_TOKEN not set, skipping tunnel"
fi

# Start the API server in foreground (this becomes PID 1)
# When container stops, Docker will handle cleanup of background processes
echo "🚀 Starting GraphRAG API server..."
exec python api.py

