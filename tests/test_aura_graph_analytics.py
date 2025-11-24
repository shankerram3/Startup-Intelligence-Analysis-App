"""
Test Aura Graph Analytics Connection
Tests the connection and basic functionality of Aura Graph Analytics
"""

import os

from dotenv import load_dotenv


def main():
    load_dotenv()

    print("=" * 80)
    print("Testing Aura Graph Analytics Connection")
    print("=" * 80)
    print()

    # Check credentials
    client_id = os.getenv("AURA_API_CLIENT_ID")
    client_secret = os.getenv("AURA_API_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("❌ Aura API credentials not found in .env")
        print("   Set AURA_API_CLIENT_ID and AURA_API_CLIENT_SECRET")
        return False

    print("✅ Aura API credentials found")
    print()

    try:
        from utils.aura_graph_analytics import AuraGraphAnalytics

        print("Creating Aura Graph Analytics session...")
        aura_gds = AuraGraphAnalytics()

        print("✅ Aura Graph Analytics initialized successfully!")
        print()
        print("You can now use Aura Graph Analytics in the pipeline.")
        print()
        print("To test community detection:")
        print(
            "  python -c \"from utils.aura_graph_analytics import AuraGraphAnalytics; gds = AuraGraphAnalytics(); gds.create_session(); result = gds.detect_communities('leiden'); print(result)\""
        )

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Install with: pip install graphdatascience")
        return False
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()
