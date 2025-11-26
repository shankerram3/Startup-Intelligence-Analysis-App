#!/bin/bash
# Get a quick Cloudflare Tunnel URL for immediate testing
# This is temporary - use Cloudflare Dashboard for persistent setup

echo "🚇 Starting quick Cloudflare Tunnel..."
echo "This will provide a temporary HTTPS URL"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cloudflared tunnel --url http://localhost:8000

