#!/usr/bin/env python3
"""
Delete TechCrunch Disrupt nodes from Neo4j graph database
Run this script to remove any existing TechCrunch Disrupt 2025 nodes
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()


def delete_techcrunch_disrupt_nodes():
    """Delete all TechCrunch Disrupt related nodes from the graph"""

    # Get Neo4j connection details
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")

    if not password:
        print("❌ NEO4J_PASSWORD not set in .env file")
        return

    print(f"Connecting to Neo4j at {uri}...")
    driver = GraphDatabase.driver(uri, auth=(user, password))

    try:
        with driver.session() as session:
            # First, find all TechCrunch Disrupt nodes
            print("\n🔍 Finding TechCrunch Disrupt nodes...")
            result = session.run(
                """
                MATCH (n)
                WHERE n.name =~ '(?i).*TECHCRUNCH.*DISRUPT.*'
                   OR (n.name =~ '(?i).*DISRUPT.*' 
                       AND (n.name =~ '(?i).*TECHCRUNCH.*'
                            OR n.name =~ '(?i).*2025.*'
                            OR n.name =~ '(?i).*2024.*'))
                RETURN labels(n) as type, n.name as name, id(n) as internal_id
                ORDER BY n.name
            """
            )

            nodes_to_delete = list(result)

            if not nodes_to_delete:
                print("✅ No TechCrunch Disrupt nodes found!")
                return

            print(f"Found {len(nodes_to_delete)} TechCrunch Disrupt node(s):")
            for record in nodes_to_delete:
                print(f"  - {record['name']} (type: {', '.join(record['type'])})")

            # Delete relationships first
            print("\n🗑️  Deleting relationships...")
            rel_result = session.run(
                """
                MATCH (n)-[r]-(related)
                WHERE n.name =~ '(?i).*TECHCRUNCH.*DISRUPT.*'
                   OR (n.name =~ '(?i).*DISRUPT.*' 
                       AND (n.name =~ '(?i).*TECHCRUNCH.*'
                            OR n.name =~ '(?i).*2025.*'
                            OR n.name =~ '(?i).*2024.*'))
                DELETE r
                RETURN count(r) as deleted
            """
            )
            rel_record = rel_result.single()
            rel_count = rel_record["deleted"] if rel_record else 0
            print(f"✓ Deleted {rel_count} relationship(s)")

            # Delete nodes
            print("\n🗑️  Deleting nodes...")
            node_result = session.run(
                """
                MATCH (n)
                WHERE n.name =~ '(?i).*TECHCRUNCH.*DISRUPT.*'
                   OR (n.name =~ '(?i).*DISRUPT.*' 
                       AND (n.name =~ '(?i).*TECHCRUNCH.*'
                            OR n.name =~ '(?i).*2025.*'
                            OR n.name =~ '(?i).*2024.*'))
                DELETE n
                RETURN count(n) as deleted
            """
            )
            node_record = node_result.single()
            node_count = node_record["deleted"] if node_record else 0
            print(f"✓ Deleted {node_count} node(s)")

            # Verify deletion
            print("\n🔍 Verifying deletion...")
            verify_result = session.run(
                """
                MATCH (n)
                WHERE n.name =~ '(?i).*TECHCRUNCH.*DISRUPT.*'
                   OR (n.name =~ '(?i).*DISRUPT.*' 
                       AND (n.name =~ '(?i).*TECHCRUNCH.*'
                            OR n.name =~ '(?i).*2025.*'
                            OR n.name =~ '(?i).*2024.*'))
                RETURN count(n) as remaining
            """
            )
            verify_record = verify_result.single()
            remaining = verify_record["remaining"] if verify_record else 0

            if remaining == 0:
                print("✅ SUCCESS: All TechCrunch Disrupt nodes deleted!")
            else:
                print(
                    f"⚠️  WARNING: {remaining} TechCrunch Disrupt node(s) still remain"
                )

    finally:
        driver.close()
        print("\n✓ Connection closed")


if __name__ == "__main__":
    delete_techcrunch_disrupt_nodes()
