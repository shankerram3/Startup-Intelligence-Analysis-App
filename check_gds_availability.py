"""
Check GDS (Graph Data Science) Library Availability
This script checks if GDS is available on your Neo4j instance and provides helpful information.
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase


def check_gds_availability():
    """Check if GDS library is available and provide diagnostics"""
    load_dotenv()

    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD")

    if not neo4j_password:
        print("❌ NEO4J_PASSWORD not set in environment")
        return

    print("=" * 80)
    print("GDS (Graph Data Science) Library Availability Check")
    print("=" * 80)
    print(f"\nConnecting to: {neo4j_uri}")

    try:
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        driver.verify_connectivity()
        print("✅ Connected to Neo4j successfully\n")

        with driver.session() as session:
            # Check Neo4j version and edition
            print("1. Neo4j Version & Edition:")
            print("-" * 80)
            try:
                result = session.run(
                    "CALL dbms.components() YIELD name, versions, edition RETURN name, versions[0] as version, edition LIMIT 1"
                )
                record = result.single()
                if record:
                    print(f"   Version: {record['version']}")
                    print(f"   Edition: {record['edition']}")
                else:
                    print("   ⚠️  Could not determine version")
            except Exception as e:
                print(f"   ⚠️  Could not check version: {e}")

            # Check if it's Aura
            is_aura = "databases.neo4j.io" in neo4j_uri or "neo4j+s://" in neo4j_uri
            print(f"\n2. Instance Type:")
            print("-" * 80)
            if is_aura:
                print("   ✅ Neo4j Aura (managed cloud)")
            else:
                print("   ✅ Self-hosted Neo4j")

            # Check for GDS procedures (try multiple methods)
            print(f"\n3. GDS Library Check:")
            print("-" * 80)
            gds_count = 0
            try:
                # Method 1: Try dbms.procedures (older versions)
                try:
                    gds_check = session.run(
                        """
                        CALL dbms.procedures() 
                        YIELD name 
                        WHERE name STARTS WITH 'gds.' 
                        RETURN count(*) as count
                    """
                    )
                    gds_count = gds_check.single()["count"] if gds_check.single() else 0
                except Exception:
                    # Method 2: Try SHOW PROCEDURES (newer versions)
                    try:
                        gds_check = session.run(
                            """
                            SHOW PROCEDURES 
                            YIELD name 
                            WHERE name STARTS WITH 'gds.' 
                            RETURN count(*) as count
                        """
                        )
                        gds_count = (
                            gds_check.single()["count"] if gds_check.single() else 0
                        )
                    except Exception:
                        # Method 3: Try to directly call a GDS procedure
                        try:
                            test_result = session.run(
                                "CALL gds.version() YIELD version RETURN version"
                            )
                            test_record = test_result.single()
                            if test_record:
                                gds_count = 1  # GDS is available if version() works
                                print(
                                    f"   ✅ GDS library is AVAILABLE (via version check)"
                                )
                                print(
                                    f"   GDS Version: {test_record.get('version', 'unknown')}"
                                )
                        except Exception:
                            gds_count = 0

                if gds_count > 0:
                    if (
                        not test_record
                    ):  # Only print if we haven't already printed from version check
                        print(f"   ✅ GDS library is AVAILABLE")
                        print(f"   Found {gds_count} GDS procedures")

                    # Try to list some GDS procedures (optional)
                    try:
                        proc_result = session.run(
                            """
                            SHOW PROCEDURES 
                            YIELD name 
                            WHERE name STARTS WITH 'gds.' 
                            RETURN collect(name)[0..5] as sample_procedures
                        """
                        )
                        proc_record = proc_result.single()
                        if proc_record and proc_record.get("sample_procedures"):
                            print(
                                f"   Sample procedures: {', '.join(proc_record['sample_procedures'])}"
                            )
                    except Exception:
                        pass
                else:
                    test_record = None  # Initialize for later
                    print(f"   ❌ GDS library is NOT available")
                    print(f"   Found 0 GDS procedures")

                    if is_aura:
                        print("\n   📌 Why GDS is not available on Aura Free Tier:")
                        print("      • GDS (Graph Data Science) is a premium feature")
                        print(
                            "      • Available on Aura Professional ($65+/month) and Enterprise"
                        )
                        print("      • Not included in Aura Free tier")
                        print("\n   💡 Solutions:")
                        print("      1. Upgrade to Aura Professional tier (if needed)")
                        print(
                            "      2. Use the fallback simple community detection (already working)"
                        )
                        print(
                            "      3. Use local Neo4j with GDS plugin for development"
                        )
            except Exception as e:
                print(f"   ⚠️  Error checking GDS: {e}")

            # Check existing graphs
            print(f"\n4. Existing GDS Graphs:")
            print("-" * 80)
            try:
                graphs_result = session.run(
                    "CALL gds.graph.list() YIELD graphName RETURN collect(graphName) as graphs"
                )
                graphs_record = graphs_result.single()
                if graphs_record and graphs_record.get("graphs"):
                    print(f"   Found {len(graphs_record['graphs'])} graphs:")
                    for graph in graphs_record["graphs"]:
                        print(f"     • {graph}")
                else:
                    print("   No GDS graphs found")
            except Exception:
                print("   ⚠️  Cannot check graphs (GDS may not be available)")

            # Summary
            print(f"\n" + "=" * 80)
            print("SUMMARY")
            print("=" * 80)

            # Re-check GDS status for summary (try multiple methods)
            gds_available = False
            gds_version = None
            gds_error = None

            # Method 1: Try direct GDS version check (most reliable)
            try:
                test_result = session.run(
                    "CALL gds.version() YIELD version RETURN version"
                )
                test_record = test_result.single()
                if test_record:
                    gds_available = True
                    gds_version = test_record.get("version", "unknown")
            except Exception as e:
                gds_error = str(e)

            # Method 2: Try gds.list() if version doesn't work
            if not gds_available:
                try:
                    list_result = session.run(
                        "CALL gds.list() YIELD name RETURN count(*) as count"
                    )
                    list_record = list_result.single()
                    if (
                        list_record and list_record.get("count", 0) >= 0
                    ):  # Just check if it doesn't error
                        gds_available = True
                except Exception as e2:
                    if not gds_error:
                        gds_error = str(e2)

            # Print summary based on GDS availability
            if not gds_available:
                if is_aura:
                    print("⚠️  GDS is NOT available on your Aura instance.")

                    # Check edition to provide specific guidance
                    try:
                        ed_result = session.run(
                            "CALL dbms.components() YIELD edition RETURN edition LIMIT 1"
                        )
                        edition_record = ed_result.single()
                        edition = (
                            edition_record.get("edition", "unknown")
                            if edition_record
                            else "unknown"
                        )

                        if edition.lower() in ["enterprise", "enterprise edition"]:
                            print(
                                "   ⚠️  You're on Aura Enterprise, but GDS procedures are not available."
                            )
                            print(
                                "   This is expected! On Aura, GDS works differently:"
                            )
                            print(
                                "     • GDS is NOT installed directly on AuraDB instances"
                            )
                            print(
                                "     • Instead, use Aura Graph Analytics (serverless GDS service)"
                            )
                            print(
                                "     • See: https://neo4j.com/docs/graph-data-science-client/current/graph-analytics-serverless/"
                            )
                            print("\n   To use GDS on Aura:")
                            print("     • Install: pip install graphdatascience")
                            print("     • Use GDS Sessions (separate compute units)")
                            print("     • Create sessions using Aura API credentials")
                            print("     • Project graphs from AuraDB to GDS Sessions")
                            print("     • Run algorithms and write results back")
                        else:
                            print("   This is expected if you're on the Free tier.")
                            print(
                                "   The pipeline will use simple community detection (which works fine)."
                            )
                            print("\n   To enable GDS:")
                            print(
                                "   • Upgrade to Aura Professional tier in https://console.neo4j.io/"
                            )
                    except Exception:
                        print("   This might be due to:")
                        print("     • Free tier (GDS not included)")
                        print("     • GDS not enabled on your Aura instance")

                    print(
                        "\n   💡 The pipeline will use simple community detection (which works fine)."
                    )
                    if gds_error:
                        print(f"\n   Technical details: {gds_error[:200]}")
                else:
                    print("⚠️  GDS is NOT available on your Neo4j instance.")
                    print("   To install GDS:")
                    print(
                        "   1. Download from: https://neo4j.com/docs/graph-data-science/"
                    )
                    print("   2. Place in plugins directory")
                    print(
                        "   3. Add to neo4j.conf: dbms.security.procedures.unrestricted=gds.*"
                    )
                    print("   4. Restart Neo4j")
            else:
                print("✅ GDS is available and ready to use!")
                if gds_version:
                    print(f"   GDS Version: {gds_version}")
                print("   Advanced community detection algorithms will be used.")

        driver.close()

    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        print("\nPlease check:")
        print("  • NEO4J_URI is correct")
        print("  • NEO4J_USER is correct")
        print("  • NEO4J_PASSWORD is correct")
        print("  • Neo4j instance is running and accessible")


if __name__ == "__main__":
    check_gds_availability()
