#!/bin/bash
# Helper script to add Aura API credentials to .env file
# Usage: ./add_aura_credentials.sh

echo "======================================================================"
echo "Adding Aura API Credentials to .env file"
echo "======================================================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating it..."
    touch .env
    chmod 600 .env
fi

# Set credentials from provided values
CLIENT_ID="rT0Rhe9Std26etPPXGiLhcdOxwiz02CS"
CLIENT_SECRET="Oi5eHnjS5TB5kYKj79mItVNdmVSnq3CTeMqoqGvGbOlwSoB3Qhl5HZgURqO0bu2Y"

echo "Adding credentials to .env file..."
echo ""

# Remove old Aura API credentials if they exist
sed -i.bak '/^AURA_API_CLIENT_ID=/d' .env 2>/dev/null || true
sed -i.bak '/^AURA_API_CLIENT_SECRET=/d' .env 2>/dev/null || true
sed -i.bak '/^AURA_PROJECT_ID=/d' .env 2>/dev/null || true

# Remove backup file if created
rm -f .env.bak 2>/dev/null || true

# Add new credentials
echo "" >> .env
echo "# ============================================================================" >> .env
echo "# Neo4j Aura API Credentials (for Aura Graph Analytics)" >> .env
echo "# ============================================================================" >> .env
echo "# Get from: https://console.neo4j.io/api-credentials" >> .env
echo "AURA_API_CLIENT_ID=$CLIENT_ID" >> .env
echo "AURA_API_CLIENT_SECRET=$CLIENT_SECRET" >> .env
echo "AURA_PROJECT_ID=" >> .env

# Secure the .env file
chmod 600 .env

echo "✅ Credentials added to .env file!"
echo ""
echo "Verifying..."
echo ""

# Test that credentials are set
python tests/test_aura_api_credentials.py

echo ""
echo "======================================================================"
echo "✅ Done! Your Aura API credentials are now configured."
echo "======================================================================"
echo ""
echo "Next steps:"
echo "  1. Install Graph Data Science client: pip install graphdatascience"
echo "  2. Test connection: python -c 'from dotenv import load_dotenv; load_dotenv(); import os; print(\"Client ID:\", os.getenv(\"AURA_API_CLIENT_ID\"))'"
echo ""
echo "Security reminder:"
echo "  • .env file is now readable only by you (chmod 600)"
echo "  • Make sure .env is in .gitignore"
echo "  • Never commit credentials to git!"
echo ""

