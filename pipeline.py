"""
Complete Pipeline: TechCrunch Articles → Knowledge Graph → RAG
Orchestrates the entire process from scraped articles to queryable graph
"""

import os
import sys
from pathlib import Path
import json
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables from .env file
load_dotenv()


def check_requirements():
    """Check if all required packages are installed"""
    required_packages = [
        "langchain_core",
        "langchain_openai",
        "neo4j",
        "openai"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    
    return True


def check_environment():
    """Check if required environment variables are set"""
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API key for entity extraction",
        "NEO4J_URI": "Neo4j connection URI (e.g., bolt://localhost:7687)",
        "NEO4J_USER": "Neo4j username",
        "NEO4J_PASSWORD": "Neo4j password"
    }
    
    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"  {var}: {description}")
    
    if missing:
        print("❌ Missing environment variables:")
        for m in missing:
            print(m)
        print("\nSet them with:")
        print("export OPENAI_API_KEY='your-key'")
        print("export NEO4J_URI='bolt://localhost:7687'")
        print("export NEO4J_USER='neo4j'")
        print("export NEO4J_PASSWORD='your-password'")
        return False
    
    return True


def run_pipeline(
    articles_dir: str,
    output_dir: str,
    max_articles: int = None,
    skip_scraping: bool = False,
    skip_extraction: bool = False,
    skip_graph_building: bool = False,
    scrape_category: str = None,
    scrape_max_pages: int = None,
    resume_extraction: bool = True,
    validate_data: bool = True,
    auto_cleanup_graph: bool = True,
    run_advanced_features: bool = False
):
    """
    Run the complete pipeline
    
    Args:
        articles_dir: Directory containing scraped article JSON files
        output_dir: Directory for extracted entities and intermediate files
        max_articles: Limit number of articles to process (None = all)
        skip_scraping: Skip web scraping phase
        skip_extraction: Skip entity extraction (use existing extractions)
        skip_graph_building: Skip Neo4j graph construction
        scrape_category: Category to scrape (if scraping is enabled)
        scrape_max_pages: Maximum pages to scrape
        resume_extraction: Resume extraction from checkpoint
        validate_data: Validate articles and extractions
        auto_cleanup_graph: Automatically clean up graph (fix MENTIONED_IN relationships)
        run_advanced_features: Run advanced post-processing features (deduplication, scoring, etc.)
    """
    
    print("\n" + "="*80)
    print("TECHCRUNCH KNOWLEDGE GRAPH PIPELINE")
    print("="*80 + "\n")
    
    # Check requirements
    if not check_requirements():
        return False
    
    if not check_environment():
        return False
    
    # Get configuration
    openai_api_key = os.getenv("OPENAI_API_KEY")
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USER")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    extractions_file = output_path / "all_extractions.json"
    
    # Phase 0: Web Scraping
    if not skip_scraping and scrape_category:
        print("\n" + "="*80)
        print("PHASE 0: WEB SCRAPING")
        print("="*80 + "\n")
        
        try:
            import asyncio
            import sys
            
            # Add scraper directory to path
            scraper_dir = Path(__file__).parent / "scraper"
            if scraper_dir.exists():
                sys.path.insert(0, str(scraper_dir))
            
            from techcrunch_scraper import TechCrunchScraper
            from scraper_config import TECHCRUNCH_CATEGORIES
            
            # Get category URL
            if scrape_category in TECHCRUNCH_CATEGORIES:
                category_url = TECHCRUNCH_CATEGORIES[scrape_category]
            else:
                category_url = scrape_category  # Assume it's a full URL
            
            # Initialize scraper
            scraper = TechCrunchScraper(
                output_dir=articles_dir,
                rate_limit_delay=3.0,
                max_pages=scrape_max_pages
            )
            
            # Discover articles
            print(f"Discovering articles from: {category_url}")
            articles = asyncio.run(scraper.discover_articles(category_url=category_url))
            
            if not articles:
                print("❌ No articles discovered")
                return False
            
            print(f"✓ Discovered {len(articles)} articles")
            
            # Extract articles
            print(f"\nExtracting {len(articles)} articles...")
            asyncio.run(scraper.extract_articles(articles=articles, batch_size=10))
            
            print(f"✓ Scraping complete: {scraper.stats['articles_extracted']} articles extracted")
            
        except Exception as e:
            print(f"❌ Scraping failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    elif not skip_scraping:
        print("\n⏭  Skipping scraping (no category specified)")
    
    # Phase 1: Entity Extraction
    if not skip_extraction:
        print("\n" + "="*80)
        print("PHASE 1: ENTITY EXTRACTION")
        print("="*80 + "\n")
        
        from entity_extractor import process_articles_directory
        
        try:
            extractions = process_articles_directory(
                articles_dir=articles_dir,
                output_dir=output_dir,
                openai_api_key=openai_api_key,
                max_articles=max_articles,
                resume=resume_extraction,
                validate_data=validate_data
            )
            
            if not extractions:
                print("❌ No extractions generated")
                return False
                
        except Exception as e:
            print(f"❌ Entity extraction failed: {e}")
            return False
    else:
        print("\n⏭  Skipping entity extraction (using existing file)")
        if not extractions_file.exists():
            print(f"❌ Extractions file not found: {extractions_file}")
            return False
    
    # Phase 2: Graph Construction
    if not skip_graph_building:
        print("\n" + "="*80)
        print("PHASE 2: KNOWLEDGE GRAPH CONSTRUCTION")
        print("="*80 + "\n")
        
        from graph_builder import build_graph_from_extractions
        
        try:
            build_graph_from_extractions(
                extractions_file=str(extractions_file),
                neo4j_uri=neo4j_uri,
                neo4j_user=neo4j_user,
                neo4j_password=neo4j_password
            )
        except Exception as e:
            print(f"❌ Graph construction failed: {e}")
            print("\nMake sure Neo4j is running:")
            print("  docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j")
            return False
    else:
        print("\n⏭  Skipping graph construction")
    
    # Phase 3: Graph Post-Processing (Optional)
    if not skip_graph_building and auto_cleanup_graph:
        print("\n" + "="*80)
        print("PHASE 3: GRAPH POST-PROCESSING")
        print("="*80 + "\n")
        
        try:
            import sys
            from pathlib import Path
            
            # Add utils directory to path
            utils_dir = Path(__file__).parent / "utils"
            if utils_dir.exists():
                sys.path.insert(0, str(utils_dir))
            
            from graph_cleanup import GraphCleaner
            
            cleaner = GraphCleaner(neo4j_uri, neo4j_user, neo4j_password)
            
            try:
                cleaner.fix_mentioned_in_relationships()
                cleaner.show_statistics()
                print("✅ Graph cleanup complete!")
            finally:
                cleaner.close()
                
        except ImportError as e:
            print(f"⚠️  Graph cleanup utility not found: {e}")
            print("Skipping graph cleanup...")
        except Exception as e:
            print(f"⚠️  Graph cleanup failed: {e}")
            # Don't fail pipeline if cleanup fails
    
    # Phase 4: Advanced Features (Optional)
    if not skip_graph_building and run_advanced_features:
        print("\n" + "="*80)
        print("PHASE 4: ADVANCED FEATURES")
        print("="*80 + "\n")
        
        try:
            import sys
            from pathlib import Path
            
            # Add utils directory to path
            utils_dir = Path(__file__).parent / "utils"
            if utils_dir.exists():
                sys.path.insert(0, str(utils_dir))
            
            # Add parent directory to path for utils imports
            parent_dir = Path(__file__).parent
            if parent_dir not in sys.path:
                sys.path.insert(0, str(parent_dir))
            
            from utils.entity_resolver import EntityResolver
            from utils.relationship_scorer import RelationshipScorer
            from utils.community_detector import CommunityDetector
            from utils.embedding_generator import EmbeddingGenerator
            
            # Get Neo4j connection
            driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            
            try:
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
                
                # 3. Community Detection
                print("3. Community Detection")
                print("-" * 80)
                detector = CommunityDetector(driver)
                communities = detector.detect_communities(min_community_size=3)
                print(f"   ✓ Detected {communities.get('total_communities', 0)} communities\n")
                
                # 4. Embedding Generation (optional - requires API key)
                print("4. Embedding Generation")
                print("-" * 80)
                if openai_api_key:
                    generator = EmbeddingGenerator(driver, embedding_model="openai")
                    embed_stats = generator.generate_embeddings_for_all_entities()
                    print(f"   ✓ Generated {embed_stats.get('generated', 0)} embeddings\n")
                else:
                    print("   ⚠️  Skipped (OPENAI_API_KEY not set)\n")
                
                print("="*80)
                print("✅ ADVANCED FEATURES COMPLETE!")
                print("="*80 + "\n")
                
            finally:
                driver.close()
                
        except ImportError as e:
            print(f"⚠️  Advanced features not available: {e}")
            print("Skipping advanced features...")
        except Exception as e:
            print(f"⚠️  Advanced features failed: {e}")
            import traceback
            traceback.print_exc()
            # Don't fail pipeline if advanced features fail
    
    # Success!
    print("\n" + "="*80)
    print("✅ PIPELINE COMPLETE!")
    print("="*80)
    print("\nNext steps:")
    print("1. Open Neo4j Browser: http://localhost:7474")
    print("2. Run Cypher queries to explore the graph")
    print("3. Implement Graph RAG for querying")
    print("="*80 + "\n")
    
    return True


def print_usage():
    """Print usage instructions"""
    print("""
TechCrunch Knowledge Graph Pipeline

Usage:
    python pipeline.py [options]

Options:
    --articles-dir PATH     Path to scraped articles directory
                           (default: data/articles)
    
    --output-dir PATH      Path for extracted entities
                           (default: data/processing)
    
    --max-articles N       Limit to N articles (default: all)
    
    --skip-extraction      Skip entity extraction phase
    
    --skip-graph           Skip graph construction phase

Examples:
    # Process 10 articles and build graph
    python pipeline.py --max-articles 10
    
    # Process all articles
    python pipeline.py
    
    # Only extract entities (don't build graph)
    python pipeline.py --skip-graph
    
    # Only build graph (use existing extractions)
    python pipeline.py --skip-extraction

Environment Variables:
    OPENAI_API_KEY         Your OpenAI API key
    NEO4J_URI             Neo4j connection (bolt://localhost:7687)
    NEO4J_USER            Neo4j username (neo4j)
    NEO4J_PASSWORD        Neo4j password
""")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="TechCrunch Knowledge Graph Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--articles-dir",
        default="data/articles",
        help="Path to scraped articles directory"
    )
    
    parser.add_argument(
        "--output-dir",
        default="data/processing",
        help="Path for extracted entities"
    )
    
    parser.add_argument(
        "--max-articles",
        type=int,
        default=None,
        help="Limit number of articles to process"
    )
    
    parser.add_argument(
        "--skip-scraping",
        action="store_true",
        help="Skip web scraping phase"
    )
    
    parser.add_argument(
        "--skip-extraction",
        action="store_true",
        help="Skip entity extraction phase"
    )
    
    parser.add_argument(
        "--skip-graph",
        action="store_true",
        help="Skip graph construction phase"
    )
    
    parser.add_argument(
        "--scrape-category",
        type=str,
        default=None,
        help="Category to scrape (e.g., 'startups', 'ai'). Enables Phase 0 scraping"
    )
    
    parser.add_argument(
        "--scrape-max-pages",
        type=int,
        default=None,
        help="Maximum pages to scrape (default: unlimited)"
    )
    
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Don't resume from checkpoint (start fresh)"
    )
    
    parser.add_argument(
        "--no-validation",
        action="store_true",
        help="Skip data validation"
    )
    
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Skip graph post-processing cleanup"
    )
    
    parser.add_argument(
        "--advanced-features",
        action="store_true",
        help="Run advanced post-processing features (deduplication, scoring, community detection, embeddings)"
    )
    
    parser.add_argument(
        "--help-extended",
        action="store_true",
        help="Show extended help"
    )
    
    args = parser.parse_args()
    
    if args.help_extended:
        print_usage()
        return
    
    # Run pipeline
    success = run_pipeline(
        articles_dir=args.articles_dir,
        output_dir=args.output_dir,
        max_articles=args.max_articles,
        skip_scraping=args.skip_scraping,
        skip_extraction=args.skip_extraction,
        skip_graph_building=args.skip_graph,
        scrape_category=args.scrape_category,
        scrape_max_pages=args.scrape_max_pages,
        resume_extraction=not args.no_resume,
        validate_data=not args.no_validation,
        auto_cleanup_graph=not args.no_cleanup,
        run_advanced_features=args.advanced_features
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()