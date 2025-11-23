"""
Test Aura API Credentials
Quick script to verify your Aura API credentials are configured correctly.
"""

import os
from dotenv import load_dotenv


def main():
    load_dotenv()

    client_id = os.getenv("AURA_API_CLIENT_ID")
    client_secret = os.getenv("AURA_API_CLIENT_SECRET")
    project_id = os.getenv("AURA_PROJECT_ID")

    print("=" * 80)
    print("Aura API Credentials Check")
    print("=" * 80)
    print()

    # Check if credentials are set
    if not client_id:
        print("❌ AURA_API_CLIENT_ID is not set in .env")
        print()
        print("To fix:")
        print("1. Get credentials from: https://console.neo4j.io/api-credentials")
        print("2. Add to .env file:")
        print("   AURA_API_CLIENT_ID=your-client-id-here")
        print("   AURA_API_CLIENT_SECRET=your-client-secret-here")
        return False

    if not client_secret:
        print("❌ AURA_API_CLIENT_SECRET is not set in .env")
        print()
        print("To fix:")
        print("1. Get credentials from: https://console.neo4j.io/api-credentials")
        print("2. Add to .env file:")
        print("   AURA_API_CLIENT_SECRET=your-client-secret-here")
        return False

    print(
        f"✅ Client ID: {client_id[:20]}...{client_id[-10:] if len(client_id) > 30 else ''}"
    )
    print(
        f"✅ Client Secret: {'*' * 20}...{client_secret[-10:] if len(client_secret) > 10 else ''}"
    )
    if project_id:
        print(f"✅ Project ID: {project_id}")
    else:
        print("ℹ️  Project ID: Not set (optional if you have only one project)")

    print()
    print("Credentials are configured in .env file!")
    print()
    print("To test connection to Aura Graph Analytics:")
    print("  1. Install: pip install graphdatascience")
    print("  2. Run: python check_aura_graph_analytics.py")
    print()
    print("For more info, see:")
    print("  docs/deployment/AURA_API_CREDENTIALS_GUIDE.md")

    return True


if __name__ == "__main__":
    main()
