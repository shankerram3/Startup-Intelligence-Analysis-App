"""
Graph cleanup utilities for Neo4j knowledge graph
Converts MENTIONED_IN relationships to entity properties for cleaner graph
"""

from neo4j import GraphDatabase
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GraphCleaner:
    """Remove MENTIONED_IN relationships and convert to properties"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def fix_mentioned_in_relationships(self):
        """
        Convert MENTIONED_IN relationships to entity properties
        """
        print("\n" + "="*80)
        print("FIXING MENTIONED_IN RELATIONSHIPS")
        print("="*80 + "\n")
        
        with self.driver.session() as session:
            # Step 1: Get all entity types (excluding Article)
            result = session.run("""
                MATCH (n)
                WHERE NOT n:Article
                RETURN DISTINCT labels(n)[0] as label
            """)
            entity_labels = [record["label"] for record in result]
            
            print(f"Found entity types: {entity_labels}\n")
            
            if not entity_labels:
                print("No entity types found. Skipping cleanup.")
                return
            
            # Step 2: First, migrate ALL MENTIONED_IN relationships to properties (globally)
            print("Converting all MENTIONED_IN relationships to properties...")
            session.run("""
                MATCH (e)-[r:MENTIONED_IN]->(a:Article)
                WHERE NOT e:Article
                WITH e, collect(DISTINCT a.id) as article_ids
                SET e.source_articles = CASE 
                    WHEN e.source_articles IS NULL THEN article_ids
                    WHEN NOT all(id IN article_ids WHERE id IN e.source_articles) 
                    THEN e.source_articles + [x IN article_ids WHERE NOT x IN e.source_articles]
                    ELSE e.source_articles
                END,
                e.article_count = size(e.source_articles),
                e.last_mentioned = timestamp()
            """)
            print("✓ Migrated all to properties")
            
            # Step 3: Delete ALL MENTIONED_IN relationships (regardless of label)
            print("\nDeleting all MENTIONED_IN relationships...")
            delete_result = session.run("""
                MATCH ()-[r:MENTIONED_IN]->()
                DELETE r
                RETURN count(r) as deleted
            """)
            delete_record = delete_result.single()
            deleted = delete_record["deleted"] if delete_record else 0
            print(f"✓ Deleted {deleted} MENTIONED_IN relationships\n")
            
            # Step 3: Verify cleanup
            remaining = session.run("""
                MATCH ()-[r:MENTIONED_IN]->()
                RETURN count(r) as count
            """)
            remaining_record = remaining.single()
            remaining_count = remaining_record["count"] if remaining_record else 0
            
            print("="*80)
            if remaining_count == 0:
                print("✅ SUCCESS: All MENTIONED_IN relationships removed")
            else:
                print(f"⚠️  WARNING: {remaining_count} MENTIONED_IN relationships remain")
            print("="*80 + "\n")
    
    def show_statistics(self):
        """Show graph statistics after cleanup"""
        with self.driver.session() as session:
            # Count nodes
            node_result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as type, count(n) as count
                ORDER BY count DESC
            """)
            
            print("\n" + "="*80)
            print("GRAPH STATISTICS (AFTER CLEANUP)")
            print("="*80)
            print("\nNodes:")
            for record in node_result:
                print(f"  {record['type']}: {record['count']}")
            
            # Count relationships
            rel_result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            """)
            
            print("\nRelationships:")
            total_rels = 0
            for record in rel_result:
                count = record['count']
                total_rels += count
                print(f"  {record['type']}: {count}")
            
            print(f"\nTotal relationships: {total_rels}")
            print("="*80 + "\n")
    
    def test_provenance_queries(self):
        """Test that we can still query article sources"""
        print("\n" + "="*80)
        print("TESTING PROVENANCE QUERIES")
        print("="*80 + "\n")
        
        with self.driver.session() as session:
            # Test 1: Find entities with most mentions
            result = session.run("""
                MATCH (e:Company)
                WHERE e.article_count IS NOT NULL
                RETURN e.name, e.article_count
                ORDER BY e.article_count DESC
                LIMIT 5
            """)
            
            print("Top 5 most mentioned companies:")
            for record in result:
                print(f"  {record['e.name']}: {record['e.article_count']} articles")
            
            # Test 2: Get source articles for an entity
            result = session.run("""
                MATCH (e:Company)
                WHERE e.article_count IS NOT NULL
                RETURN e.name, e.source_articles
                LIMIT 1
            """)
            
            record = result.single()
            if record:
                print(f"\nSample: {record['e.name']}")
                articles = record['e.source_articles']
                if articles:
                    print(f"Source articles: {articles[:3]}...")
            
            print("\n" + "="*80 + "\n")


def main():
    """Run the cleanup"""
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    
    print("\nConnecting to Neo4j...")
    print(f"URI: {NEO4J_URI}")
    
    cleaner = GraphCleaner(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        # Run cleanup
        cleaner.fix_mentioned_in_relationships()
        
        # Show new statistics
        cleaner.show_statistics()
        
        # Test provenance still works
        cleaner.test_provenance_queries()
        
        print("✅ Cleanup complete! Your graph is now cleaner.\n")
        print("Try visualizing it in Neo4j Browser:")
        print("  MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50\n")
        
    finally:
        cleaner.close()


if __name__ == "__main__":
    main()

