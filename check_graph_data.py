#!/usr/bin/env python3
"""
Quick script to verify data is being added to the Neo4j graph
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase
from datetime import datetime

# Load environment variables
load_dotenv()

def check_graph_data():
    """Check if data exists in the graph"""
    
    # Get Neo4j connection details
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not uri or not password:
        print("❌ Error: NEO4J_URI and NEO4J_PASSWORD must be set in .env file")
        return
    
    print("=" * 80)
    print("GRAPH DATA VERIFICATION")
    print("=" * 80)
    print()
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            # 1. Check total node counts
            print("📊 NODE COUNTS:")
            print("-" * 80)
            
            result = session.run("""
                MATCH (n)
                WITH labels(n)[0] as label, count(n) as count
                RETURN label, count
                ORDER BY count DESC
            """)
            
            total_nodes = 0
            for record in result:
                label = record["label"] or "Unknown"
                count = record["count"]
                total_nodes += count
                print(f"  {label:20} {count:>6}")
            
            print(f"\n  {'TOTAL':20} {total_nodes:>6}")
            print()
            
            # 2. Check relationship counts
            print("🔗 RELATIONSHIP COUNTS:")
            print("-" * 80)
            
            result = session.run("""
                MATCH ()-[r]->()
                WITH type(r) as rel_type, count(r) as count
                RETURN rel_type, count
                ORDER BY count DESC
            """)
            
            total_rels = 0
            for record in result:
                rel_type = record["rel_type"]
                count = record["count"]
                total_rels += count
                print(f"  {rel_type:30} {count:>6}")
            
            print(f"\n  {'TOTAL':30} {total_rels:>6}")
            print()
            
            # 3. Check most recent articles
            print("📰 MOST RECENT ARTICLES (last 5):")
            print("-" * 80)
            
            result = session.run("""
                MATCH (a:Article)
                WHERE a.created_at IS NOT NULL
                RETURN a.id as id, 
                       a.title as title,
                       datetime({epochMillis: a.created_at}) as created_at,
                       a.published_date as published_date
                ORDER BY a.created_at DESC
                LIMIT 5
            """)
            
            for i, record in enumerate(result, 1):
                title = (record["title"] or "No title")[:60]
                created = record["created_at"]
                published = record.get("published_date", "N/A")
                print(f"  {i}. {title}...")
                print(f"     Created: {created} | Published: {published}")
                print()
            
            # 4. Check most recent entities
            print("🏢 MOST RECENT ENTITIES (last 10):")
            print("-" * 80)
            
            result = session.run("""
                MATCH (e)
                WHERE (e:Company OR e:Person OR e:Investor OR e:Technology OR e:Product)
                  AND e.updated_at IS NOT NULL
                RETURN labels(e)[0] as type,
                       e.name as name,
                       datetime({epochMillis: e.updated_at}) as updated_at,
                       size(e.source_articles) as article_count
                ORDER BY e.updated_at DESC
                LIMIT 10
            """)
            
            for i, record in enumerate(result, 1):
                entity_type = record["type"]
                name = (record["name"] or "Unknown")[:50]
                updated = record["updated_at"]
                article_count = record.get("article_count", 0)
                print(f"  {i}. [{entity_type:10}] {name:50} | Updated: {updated} | Articles: {article_count}")
            
            print()
            
            # 5. Check entities with embeddings
            print("🧠 EMBEDDINGS STATUS:")
            print("-" * 80)
            
            result = session.run("""
                MATCH (e)
                WHERE NOT e:Article
                WITH labels(e)[0] as label,
                     count(e) as total,
                     count(e.embedding) as with_embedding
                RETURN label, total, with_embedding
                ORDER BY total DESC
            """)
            
            for record in result:
                label = record["label"] or "Unknown"
                total = record["total"]
                with_emb = record["with_embedding"]
                pct = (with_emb / total * 100) if total > 0 else 0
                print(f"  {label:20} {with_emb:>4}/{total:>4} ({pct:>5.1f}%)")
            
            print()
            
            # 6. Check enriched companies
            print("💎 ENRICHED COMPANIES:")
            print("-" * 80)
            
            result = session.run("""
                MATCH (c:Company)
                WHERE c.enrichment_status = 'enriched'
                RETURN count(c) as enriched_count
            """)
            
            enriched = result.single()["enriched_count"]
            result = session.run("MATCH (c:Company) RETURN count(c) as total")
            total_companies = result.single()["total"]
            
            print(f"  Enriched: {enriched}/{total_companies} companies")
            print()
            
            # 7. Sample data check
            print("🔍 SAMPLE DATA CHECK:")
            print("-" * 80)
            
            # Check if we have any data at all
            if total_nodes == 0:
                print("  ⚠️  WARNING: No nodes found in graph!")
                print("     The graph appears to be empty.")
            elif total_nodes < 10:
                print(f"  ⚠️  WARNING: Very few nodes ({total_nodes}) in graph.")
                print("     Pipeline may not have run successfully.")
            else:
                print(f"  ✅ Graph contains {total_nodes} nodes and {total_rels} relationships")
                print("     Data appears to be present!")
            
            print()
            print("=" * 80)
            print("✅ Verification complete!")
            print("=" * 80)
        
        driver.close()
        
    except Exception as e:
        print(f"❌ Error connecting to Neo4j: {e}")
        print()
        print("Make sure:")
        print("  1. Neo4j is running (or AuraDB instance is active)")
        print("  2. NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD are set correctly")
        print("  3. Network connectivity to Neo4j is available")
        sys.exit(1)


if __name__ == "__main__":
    check_graph_data()

