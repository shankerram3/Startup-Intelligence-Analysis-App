#!/usr/bin/env python3
"""
Delete TechCrunch and TechCrunch Disrupt nodes from Neo4j graph
Removes all nodes and relationships related to TechCrunch/TechCrunch Disrupt
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()


def delete_techcrunch_nodes(confirm: bool = False):
    """
    Delete all TechCrunch and TechCrunch Disrupt related nodes
    
    Args:
        confirm: If True, actually delete nodes. If False, only preview.
    """
    
    # Get configuration
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    
    print(f"\nConnecting to Neo4j: {uri}")
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        with driver.session() as session:
            # Pattern to match TechCrunch or TechCrunch Disrupt in NAME (case-insensitive)
            # This will match:
            # - "TECHCRUNCH DISRUPT 2025"
            # - "TECHCRUNCH"
            # - "TechCrunch Disrupt"
            # - "TECHCRUNCH EQUITY PODCAST"
            # - "STARTUP BATTLEFIELD" (TechCrunch Disrupt event)
            # - "DISRUPT" events/stages
            patterns = [
                "(?i).*TECHCRUNCH.*DISRUPT.*",  # Contains "TechCrunch Disrupt"
                "(?i)^TECHCRUNCH DISRUPT.*",    # Starts with "TechCrunch Disrupt"
                "(?i).*TECHCRUNCH DISRUPT$",    # Ends with "TechCrunch Disrupt"
                "(?i)^TECHCRUNCH$",             # Exact match "TechCrunch"
                "(?i)^TECHCRUNCH ",             # Starts with "TechCrunch " (with space)
                "(?i).*TECHCRUNCH.*",           # Contains "TechCrunch" anywhere
                "(?i)^STARTUP BATTLEFIELD.*",   # Startup Battlefield (TechCrunch Disrupt)
                "(?i).*BATTLEFIELD.*",          # Battlefield events
                "(?i)^DISRUPT.*",               # Disrupt events/stages
                "(?i).*DISRUPT.*",              # Contains "Disrupt"
            ]
            
            # Find all matching nodes
            print("\n" + "="*80)
            print("FINDING TECHCRUNCH/TECHCRUNCH DISRUPT NODES")
            print("="*80 + "\n")
            
            all_matching_nodes = []
            
            for pattern in patterns:
                result = session.run("""
                    MATCH (n)
                    WHERE n.name =~ $pattern
                    RETURN labels(n)[0] as type, n.name as name, n.id as id, id(n) as internal_id
                    ORDER BY n.name
                """, pattern=pattern)
                
                nodes = list(result)
                if nodes:
                    print(f"Pattern: {pattern}")
                    for node in nodes:
                        if node not in all_matching_nodes:
                            all_matching_nodes.append(node)
                        print(f"  {node['type']}: {node['name']} (id: {node['id']})")
                    print()
            
            # Optionally check for nodes with "TechCrunch" in description
            # Note: This might include many nodes that just mention TechCrunch as a source
            # Uncomment if you want to delete these too
            # result = session.run("""
            #     MATCH (n)
            #     WHERE n.description CONTAINS 'TechCrunch' 
            #        OR n.description CONTAINS 'TECHCRUNCH'
            #        OR n.description CONTAINS 'techcrunch'
            #     RETURN labels(n)[0] as type, n.name as name, n.id as id, id(n) as internal_id
            #     ORDER BY n.name
            # """)
            # 
            # desc_nodes = list(result)
            # for node in desc_nodes:
            #     # Only add if not already matched by name
            #     if not any(n['id'] == node['id'] for n in all_matching_nodes):
            #         all_matching_nodes.append(node)
            #         print(f"  [From description] {node['type']}: {node['name']} (id: {node['id']})")
            
            if not all_matching_nodes:
                print("✅ No TechCrunch or TechCrunch Disrupt nodes found!")
                return
            
            print(f"\nFound {len(all_matching_nodes)} nodes to delete")
            
            # Count relationships
            total_rels = 0
            for node in all_matching_nodes:
                result = session.run("""
                    MATCH (n)-[r]-()
                    WHERE id(n) = $internal_id
                    RETURN count(r) as count
                """, internal_id=node['internal_id'])
                record = result.single()
                count = record['count'] if record else 0
                total_rels += count
            
            print(f"Total relationships to be deleted: {total_rels}")
            
            if not confirm:
                print("\n⚠️  PREVIEW MODE - No nodes deleted")
                print("Run with --confirm flag to actually delete nodes")
                print("\n" + "="*80)
                return
            
            # Actually delete
            print("\n" + "="*80)
            print("DELETING TECHCRUNCH/TECHCRUNCH DISRUPT NODES")
            print("="*80 + "\n")
            
            deleted_count = 0
            for node in all_matching_nodes:
                try:
                    # Delete node and all its relationships
                    delete_result = session.run("""
                        MATCH (n)
                        WHERE id(n) = $internal_id
                        DETACH DELETE n
                        RETURN count(n) as deleted
                    """, internal_id=node['internal_id'])
                    
                    delete_record = delete_result.single()
                    if delete_record and delete_record['deleted'] > 0:
                        deleted_count += 1
                        print(f"  ✓ Deleted {node['type']}: {node['name']}")
                
                except Exception as e:
                    print(f"  ✗ Error deleting {node['name']}: {e}")
            
            # Verify deletion
            print("\n" + "="*80)
            print("VERIFICATION")
            print("="*80 + "\n")
            
            # Check for remaining TechCrunch/Disrupt nodes
            remaining_result = session.run("""
                MATCH (n)
                WHERE n.name =~ '(?i).*TECHCRUNCH.*DISRUPT.*'
                   OR n.name =~ '(?i).*TECHCRUNCH.*'
                   OR n.name =~ '(?i).*DISRUPT.*'
                   OR n.name =~ '(?i).*BATTLEFIELD.*'
                   OR n.name CONTAINS 'TechCrunch'
                   OR n.name CONTAINS 'TECHCRUNCH'
                   OR n.name CONTAINS 'Disrupt'
                   OR n.name CONTAINS 'DISRUPT'
                   OR n.name CONTAINS 'Battlefield'
                   OR n.name CONTAINS 'BATTLEFIELD'
                RETURN count(n) as count
            """)
            
            remaining_record = remaining_result.single()
            remaining_count = remaining_record['count'] if remaining_record else 0
            
            if remaining_count == 0:
                print(f"✅ SUCCESS: Deleted {deleted_count} nodes")
                print("✅ No remaining TechCrunch/TechCrunch Disrupt nodes found!")
            else:
                print(f"⚠️  WARNING: {remaining_count} TechCrunch/TechCrunch Disrupt nodes still remain")
                print(f"   (Deleted {deleted_count} nodes)")
            
            print("="*80 + "\n")
            
    finally:
        driver.close()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Delete TechCrunch and TechCrunch Disrupt nodes from Neo4j graph"
    )
    
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually delete nodes (without this flag, only preview is shown)"
    )
    
    args = parser.parse_args()
    
    delete_techcrunch_nodes(confirm=args.confirm)


if __name__ == "__main__":
    main()

