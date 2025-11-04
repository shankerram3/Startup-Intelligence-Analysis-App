#!/usr/bin/env python3
"""
Integration script for new features
Demonstrates how to use the new utilities
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.entity_resolver import EntityResolver
from utils.relationship_scorer import RelationshipScorer
from utils.temporal_analyzer import TemporalAnalyzer
from utils.entity_classifier import EntityClassifier
from utils.coreference_resolver import CoreferenceResolver
from utils.community_detector import CommunityDetector
from utils.embedding_generator import EmbeddingGenerator

load_dotenv()


def integrate_features():
    """Integrate all new features into the pipeline"""
    
    # Get Neo4j connection
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not password:
        print("❌ Error: NEO4J_PASSWORD not set")
        return
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        print("\n" + "="*80)
        print("INTEGRATING NEW FEATURES")
        print("="*80 + "\n")
        
        # 1. Entity Deduplication
        print("1. Entity Deduplication")
        print("-" * 80)
        resolver = EntityResolver(driver)
        merge_stats = resolver.merge_all_duplicates(dry_run=False, threshold=0.85)
        print(f"   ✓ Merged {merge_stats.get('merged', 0)} duplicate entities\n")
        
        # 2. Relationship Strength Calculation
        print("2. Relationship Strength Calculation")
        print("-" * 80)
        scorer = RelationshipScorer(driver)
        update_stats = scorer.update_relationship_strengths()
        print(f"   ✓ Updated {update_stats.get('updated', 0)} relationship strengths\n")
        
        # 3. Temporal Analysis
        print("3. Temporal Analysis")
        print("-" * 80)
        temporal = TemporalAnalyzer(driver)
        print("   ✓ Temporal analysis ready\n")
        
        # 4. Community Detection
        print("4. Community Detection")
        print("-" * 80)
        detector = CommunityDetector(driver)
        communities = detector.detect_communities(min_community_size=3)
        print(f"   ✓ Detected {communities.get('total_communities', 0)} communities\n")
        
        # 5. Embedding Generation
        print("5. Embedding Generation")
        print("-" * 80)
        generator = EmbeddingGenerator(driver, embedding_model="sentence_transformers")
        embed_stats = generator.generate_embeddings_for_all_entities()
        print(f"   ✓ Generated {embed_stats.get('generated', 0)} embeddings\n")
        
        print("="*80)
        print("✅ INTEGRATION COMPLETE!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.close()


if __name__ == "__main__":
    integrate_features()

