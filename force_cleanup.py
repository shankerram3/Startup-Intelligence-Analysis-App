#!/usr/bin/env python3
"""
Force cleanup of MENTIONED_IN relationships
Direct script to remove all remaining MENTIONED_IN relationships
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()


def force_cleanup_mentioned_in():
    """Force cleanup of all MENTIONED_IN relationships"""
    
    # Get configuration
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    
    print(f"\nConnecting to Neo4j: {uri}")
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        with driver.session() as session:
            # Step 1: Count existing relationships
            result = session.run("""
                MATCH ()-[r:MENTIONED_IN]->()
                RETURN count(r) as count
            """)
            record = result.single()
            before_count = record["count"] if record else 0
            
            print(f"\nFound {before_count} MENTIONED_IN relationships")
            
            if before_count == 0:
                print("✅ No MENTIONED_IN relationships found. Graph is clean!")
                return
            
            # Step 2: Convert to properties first (if not already done)
            print("\nConverting relationships to properties...")
            session.run("""
                MATCH (e)-[r:MENTIONED_IN]->(a:Article)
                WITH e, collect(DISTINCT a.id) as article_ids
                WHERE e.source_articles IS NULL OR NOT all(id IN article_ids WHERE id IN e.source_articles)
                SET e.source_articles = CASE 
                    WHEN e.source_articles IS NULL THEN article_ids
                    ELSE [x IN e.source_articles WHERE x IN article_ids] + 
                         [x IN article_ids WHERE NOT x IN e.source_articles]
                END,
                e.article_count = size(e.source_articles),
                e.last_mentioned = timestamp()
            """)
            print("✓ Properties updated")
            
            # Step 3: Delete all MENTIONED_IN relationships
            print("\nDeleting MENTIONED_IN relationships...")
            delete_result = session.run("""
                MATCH ()-[r:MENTIONED_IN]->()
                DELETE r
                RETURN count(r) as deleted
            """)
            delete_record = delete_result.single()
            deleted_count = delete_record["deleted"] if delete_record else 0
            
            print(f"✓ Deleted {deleted_count} MENTIONED_IN relationships")
            
            # Step 4: Verify
            verify_result = session.run("""
                MATCH ()-[r:MENTIONED_IN]->()
                RETURN count(r) as remaining
            """)
            verify_record = verify_result.single()
            remaining_count = verify_record["remaining"] if verify_record else 0
            
            print("\n" + "="*80)
            if remaining_count == 0:
                print("✅ SUCCESS: All MENTIONED_IN relationships removed!")
            else:
                print(f"⚠️  WARNING: {remaining_count} MENTIONED_IN relationships remain")
            print("="*80 + "\n")
            
    finally:
        driver.close()


if __name__ == "__main__":
    force_cleanup_mentioned_in()

