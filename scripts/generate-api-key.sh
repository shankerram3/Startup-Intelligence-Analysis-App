#!/bin/bash
# Generate secure API keys for authentication

set -e

echo "🔑 API Key Generator"
echo "==================="
echo ""

# Number of keys to generate (default: 1)
NUM_KEYS=${1:-1}

echo "Generating $NUM_KEYS API key(s)..."
echo ""

for i in $(seq 1 $NUM_KEYS); do
    # Generate a secure random key (32 bytes = 64 hex characters)
    KEY=$(openssl rand -hex 32)
    
    if [ $NUM_KEYS -eq 1 ]; then
        echo "API Key: $KEY"
    else
        echo "Key $i: $KEY"
    fi
done

echo ""
echo "📝 Add to your .env file:"
echo "   API_KEYS=$(openssl rand -hex 32)"
echo ""
echo "Or for multiple keys (comma-separated):"
echo "   API_KEYS=$(openssl rand -hex 32),$(openssl rand -hex 32),$(openssl rand -hex 32)"
echo ""
echo "⚠️  Keep these keys secure and never commit them to git!"

