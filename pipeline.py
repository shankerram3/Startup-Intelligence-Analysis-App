"""
Complete Pipeline: TechCrunch Articles → Knowledge Graph → RAG
Orchestrates the entire process from scraped articles to queryable graph
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

# Import structured logging
from utils.logging_config import get_logger, setup_logging

# Load environment variables from .env file
load_dotenv()

# Setup logging
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    json_logs=os.getenv("JSON_LOGS", "false").lower() == "true",
    log_file=(
        Path("logs/pipeline.log")
        if os.getenv("ENABLE_FILE_LOGGING") == "true"
        else None
    ),
)

logger = get_logger(__name__)


def check_requirements():
    """Check if all required packages are installed"""
    required_packages = ["langchain_core", "langchain_openai", "neo4j", "openai"]

    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        logger.error(
            "missing_packages",
            packages=missing,
            install_command=f"pip install {' '.join(missing)}",
        )
        return False

    return True


def check_environment():
    """Check if required environment variables are set"""
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API key for entity extraction",
        "NEO4J_URI": "Neo4j connection URI (e.g., bolt://localhost:7687)",
        "NEO4J_USER": "Neo4j username",
        "NEO4J_PASSWORD": "Neo4j password",
    }

    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"  {var}: {description}")

    if missing:
        logger.error("missing_environment_variables", variables=missing)
        logger.info(
            "environment_setup_instructions",
            instructions=[
                "export OPENAI_API_KEY='your-key'",
                "export NEO4J_URI='bolt://localhost:7687'",
                "export NEO4J_USER='neo4j'",
                "export NEO4J_PASSWORD='your-password'",
            ],
        )
        return False

    return True


def run_pipeline(
    articles_dir: str,
    output_dir: str,
    max_articles: int = None,
    skip_scraping: bool = False,
    skip_extraction: bool = False,
    skip_enrichment: bool = False,
    skip_graph_building: bool = False,
    scrape_category: str = None,
    scrape_max_pages: int = None,
    resume_extraction: bool = True,
    validate_data: bool = True,
    auto_cleanup_graph: bool = True,
    skip_post_processing: bool = False,
    max_companies_to_scrape: int = None,
):
    """
    Run the complete pipeline

    Args:
        articles_dir: Directory containing scraped article JSON files
        output_dir: Directory for extracted entities and intermediate files
        max_articles: Limit number of articles to process (None = all)
        skip_scraping: Skip web scraping phase
        skip_extraction: Skip entity extraction (use existing extractions)
        skip_enrichment: Skip company intelligence enrichment (Phase 1.5)
        skip_graph_building: Skip Neo4j graph construction
        scrape_category: Category to scrape (if scraping is enabled)
        scrape_max_pages: Maximum pages to scrape
        resume_extraction: Resume extraction from checkpoint
        validate_data: Validate articles and extractions
        auto_cleanup_graph: Automatically clean up graph (fix MENTIONED_IN relationships)
        skip_post_processing: Skip post-processing (embeddings, deduplication, etc.) - NOT RECOMMENDED
        max_companies_to_scrape: Maximum number of companies to scrape per article (None = all)
    """

    logger.info("pipeline_starting", phase="initialization")

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
        logger.info("pipeline_phase_starting", phase="0", name="WEB_SCRAPING")

        try:
            import asyncio
            import sys

            # Add scraper directory to path
            scraper_dir = Path(__file__).parent / "scraper"
            if scraper_dir.exists():
                sys.path.insert(0, str(scraper_dir))

            from scraper_config import TECHCRUNCH_CATEGORIES
            from techcrunch_scraper import TechCrunchScraper

            # Get category URL
            if scrape_category in TECHCRUNCH_CATEGORIES:
                category_url = TECHCRUNCH_CATEGORIES[scrape_category]
            else:
                category_url = scrape_category  # Assume it's a full URL

            # Initialize scraper
            scraper = TechCrunchScraper(
                output_dir=articles_dir,
                rate_limit_delay=3.0,
                max_pages=scrape_max_pages,
            )

            # Discover articles
            logger.info("scraping_discovering_articles", category_url=category_url)
            articles = asyncio.run(scraper.discover_articles(category_url=category_url))

            if not articles:
                logger.error(
                    "scraping_no_articles_discovered", category_url=category_url
                )
                return False

            logger.info("scraping_articles_discovered", count=len(articles))

            # Apply max_articles limit BEFORE extraction (to avoid unnecessary scraping)
            if max_articles and len(articles) > max_articles:
                logger.info(
                    "scraping_limiting_articles",
                    discovered=len(articles),
                    limit=max_articles,
                )
                articles = articles[:max_articles]

            # Extract articles
            logger.info("scraping_extracting_articles", count=len(articles))
            asyncio.run(scraper.extract_articles(articles=articles, batch_size=10))

            logger.info(
                "scraping_complete",
                articles_extracted=scraper.stats["articles_extracted"],
            )

        except Exception as e:
            logger.error("scraping_failed", error=str(e), exc_info=True)
            return False
    elif not skip_scraping:
        logger.info("scraping_skipped", reason="no_category_specified")

    # Phase 1: Entity Extraction
    if not skip_extraction:
        logger.info("pipeline_phase_starting", phase="1", name="ENTITY_EXTRACTION")

        from entity_extractor import process_articles_directory

        try:
            extractions = process_articles_directory(
                articles_dir=articles_dir,
                output_dir=output_dir,
                openai_api_key=openai_api_key,
                max_articles=max_articles,
                resume=resume_extraction,
                validate_data=validate_data,
            )

            if not extractions:
                logger.warning(
                    "extraction_no_new_articles",
                    reason="all_articles_already_processed",
                    message="All articles were already processed. No new extractions to process.",
                )
                return False

        except Exception as e:
            logger.error("extraction_failed", error=str(e), exc_info=True)
            return False
    else:
        logger.info("extraction_skipped", reason="using_existing_file")
        if not extractions_file.exists():
            logger.error("extraction_file_not_found", file_path=str(extractions_file))
            return False

    # Phase 1.5: Company Intelligence Enrichment (NEW!)
    enriched_companies_file = output_path / "enriched_companies.json"

    if not skip_enrichment:
        logger.info(
            "pipeline_phase_starting",
            phase="1.5",
            name="COMPANY_INTELLIGENCE_ENRICHMENT",
        )

        try:
            import asyncio
            import sys

            # Add utils directory to path
            utils_dir = Path(__file__).parent / "utils"
            if utils_dir.exists():
                sys.path.insert(0, str(utils_dir))

            # Add scraper directory to path
            scraper_dir = Path(__file__).parent / "scraper"
            if scraper_dir.exists():
                sys.path.insert(0, str(scraper_dir))

            from scraper.company_intelligence_scraper import CompanyIntelligenceScraper
            from utils.company_intelligence_aggregator import (
                CompanyIntelligenceAggregator,
                create_enrichment_summary,
            )
            from utils.company_url_extractor import (
                CompanyURLExtractor,
                extract_company_urls_from_extractions,
            )

            # Load extractions
            with open(extractions_file, "r", encoding="utf-8") as f:
                extractions = json.load(f)

            if max_articles:
                extractions = extractions[:max_articles]

            logger.info(
                "enrichment_processing_articles", article_count=len(extractions)
            )

            # Step 1: Extract company URLs from articles
            logger.info(
                "enrichment_step",
                step=1,
                description="Extracting company URLs from articles",
            )
            all_company_urls = extract_company_urls_from_extractions(
                extractions, articles_dir
            )
            total_urls = sum(len(urls) for urls in all_company_urls.values())
            logger.info(
                "enrichment_urls_extracted",
                total_urls=total_urls,
                article_count=len(all_company_urls),
            )

            # Step 2: Scrape company websites (article by article)
            logger.info(
                "enrichment_step",
                step=2,
                description="Scraping company websites with Playwright",
            )
            intelligence_dir = output_path / "company_intelligence"
            scraper = CompanyIntelligenceScraper(
                output_dir=str(intelligence_dir),
                rate_limit_delay=0.5,  # Minimal delay as requested
                timeout=30000,
                headless=True,
            )

            total_companies_scraped = 0
            for article_id, company_urls in all_company_urls.items():
                logger.debug(
                    "enrichment_article_processing",
                    article_id=article_id,
                    companies_count=len(company_urls),
                )

                # Scrape companies for this article
                try:
                    results = asyncio.run(
                        scraper.scrape_companies_batch(
                            company_urls,
                            article_id,
                            max_companies=max_companies_to_scrape,
                        )
                    )
                    total_companies_scraped += len(results)
                    logger.info(
                        "enrichment_companies_scraped",
                        article_id=article_id,
                        count=len(results),
                    )
                except Exception as e:
                    logger.warning(
                        "enrichment_scraping_failed",
                        article_id=article_id,
                        error=str(e),
                    )
                    continue

            scraper_stats = scraper.get_stats()
            logger.info("enrichment_scraping_complete", **scraper_stats)

            # Step 3: Aggregate intelligence
            logger.info(
                "enrichment_step",
                step=3,
                description="Aggregating company intelligence",
            )
            aggregator = CompanyIntelligenceAggregator()
            enriched_companies = aggregator.aggregate_all_companies(
                extractions, str(intelligence_dir)
            )

            # Save aggregated intelligence
            aggregator.save_aggregated_intelligence(
                enriched_companies, str(enriched_companies_file)
            )

            # Log summary
            summary = create_enrichment_summary(enriched_companies)
            logger.info("enrichment_summary", **summary)
            logger.info("enrichment_complete")

        except ImportError as e:
            logger.warning(
                "enrichment_not_available",
                error=str(e),
                install_command="pip install playwright && playwright install",
            )
        except Exception as e:
            logger.warning("enrichment_failed", error=str(e), exc_info=True)
    else:
        logger.info("enrichment_skipped")

    # Phase 2: Graph Construction
    if not skip_graph_building:
        logger.info(
            "pipeline_phase_starting", phase="2", name="KNOWLEDGE_GRAPH_CONSTRUCTION"
        )

        from graph_builder import TechCrunchGraphBuilder, build_graph_from_extractions

        try:
            build_graph_from_extractions(
                extractions_file=str(extractions_file),
                neo4j_uri=neo4j_uri,
                neo4j_user=neo4j_user,
                neo4j_password=neo4j_password,
            )

            # Phase 2.5: Enrich graph with company intelligence (if available)
            if not skip_enrichment and enriched_companies_file.exists():
                logger.info(
                    "pipeline_phase_starting",
                    phase="2.5",
                    name="ENRICHING_GRAPH_WITH_COMPANY_INTELLIGENCE",
                )

                try:
                    # Load enriched companies
                    with open(enriched_companies_file, "r", encoding="utf-8") as f:
                        enriched_companies = json.load(f)

                    # Connect to graph and enrich
                    builder = TechCrunchGraphBuilder(
                        neo4j_uri, neo4j_user, neo4j_password
                    )
                    try:
                        enrichment_stats = builder.enrich_all_companies(
                            enriched_companies
                        )
                        logger.info("graph_enrichment_complete", **enrichment_stats)
                    finally:
                        builder.close()

                    # Regenerate embeddings for enriched companies
                    logger.info("regenerating_embeddings_for_enriched_companies")

                    try:
                        from utils.embedding_generator import EmbeddingGenerator

                        driver = GraphDatabase.driver(
                            neo4j_uri, auth=(neo4j_user, neo4j_password)
                        )
                        try:
                            generator = EmbeddingGenerator(
                                driver, embedding_model="sentence_transformers"
                            )
                            embed_stats = (
                                generator.regenerate_enriched_company_embeddings()
                            )

                            if "error" in embed_stats:
                                logger.warning(
                                    "embedding_regeneration_error",
                                    error=embed_stats["error"],
                                )
                            else:
                                logger.info(
                                    "embedding_regeneration_complete",
                                    regenerated=embed_stats.get("regenerated", 0),
                                )
                                if embed_stats.get("failed", 0) > 0:
                                    logger.warning(
                                        "embedding_regeneration_failures",
                                        failed=embed_stats["failed"],
                                    )
                        finally:
                            driver.close()

                    except Exception as e:
                        logger.warning(
                            "embedding_regeneration_failed", error=str(e), exc_info=True
                        )
                        # Continue with pipeline

                except Exception as e:
                    logger.warning(
                        "graph_enrichment_failed", error=str(e), exc_info=True
                    )

        except Exception as e:
            logger.error("graph_construction_failed", error=str(e), exc_info=True)
            logger.info(
                "neo4j_setup_instructions",
                command="docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j",
            )
            return False
    else:
        logger.info("graph_construction_skipped")

    # Phase 3: Graph Post-Processing (Optional)
    if not skip_graph_building and auto_cleanup_graph:
        logger.info("pipeline_phase_starting", phase="3", name="GRAPH_POST_PROCESSING")

        try:
            import sys

            # Add utils directory to path
            utils_dir = Path(__file__).parent / "utils"
            if utils_dir.exists():
                sys.path.insert(0, str(utils_dir))

            from graph_cleanup import GraphCleaner

            cleaner = GraphCleaner(neo4j_uri, neo4j_user, neo4j_password)

            try:
                cleaner.fix_mentioned_in_relationships()
                cleaner.show_statistics()
                logger.info("graph_cleanup_complete")
            finally:
                cleaner.close()

        except ImportError as e:
            logger.warning("graph_cleanup_not_available", error=str(e))
        except Exception as e:
            logger.warning("graph_cleanup_failed", error=str(e), exc_info=True)
            # Don't fail pipeline if cleanup fails

    # Phase 4: Post-Processing (Essential for query functionality)
    if not skip_graph_building and not skip_post_processing:
        logger.info("pipeline_phase_starting", phase="4", name="POST_PROCESSING")

        try:
            import sys

            # Add utils directory to path
            utils_dir = Path(__file__).parent / "utils"
            if utils_dir.exists():
                sys.path.insert(0, str(utils_dir))

            # Add parent directory to path for utils imports
            parent_dir = Path(__file__).parent
            if parent_dir not in sys.path:
                sys.path.insert(0, str(parent_dir))

            from utils.community_detector import CommunityDetector
            from utils.embedding_generator import EmbeddingGenerator
            from utils.entity_resolver import EntityResolver
            from utils.relationship_scorer import RelationshipScorer

            # Get Neo4j connection
            driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

            try:
                # 1. Entity Deduplication
                logger.info("postprocessing_step", step=1, name="Entity Deduplication")
                resolver = EntityResolver(driver)
                merge_stats = resolver.merge_all_duplicates(
                    dry_run=False, threshold=0.85
                )
                logger.info("postprocessing_deduplication_complete", **merge_stats)

                # 2. Relationship Strength Calculation
                logger.info(
                    "postprocessing_step",
                    step=2,
                    name="Relationship Strength Calculation",
                )
                scorer = RelationshipScorer(driver)
                update_stats = scorer.update_relationship_strengths()
                logger.info(
                    "postprocessing_relationship_scoring_complete", **update_stats
                )

                # 3. Community Detection
                logger.info("postprocessing_step", step=3, name="Community Detection")
                detector = CommunityDetector(driver)
                communities = detector.detect_communities(
                    algorithm="leiden", min_community_size=3
                )
                method = communities.get("method", "simple")
                logger.info(
                    "postprocessing_community_detection_complete",
                    method=method,
                    **{k: v for k, v in communities.items() if k != "method"},
                )

                # 4. Embedding Generation (includes enriched company data)
                logger.info("postprocessing_step", step=4, name="Embedding Generation")
                generator = EmbeddingGenerator(
                    driver, embedding_model="sentence_transformers"
                )
                embed_stats = generator.generate_embeddings_for_all_entities()
                logger.info(
                    "postprocessing_embedding_generation_complete", **embed_stats
                )

                logger.info("postprocessing_complete")

            finally:
                driver.close()

        except ImportError as e:
            logger.warning("postprocessing_not_available", error=str(e))
        except Exception as e:
            logger.warning("postprocessing_failed", error=str(e), exc_info=True)
            # Don't fail pipeline if post-processing fails

    # Success!
    logger.info("pipeline_complete")
    logger.info(
        "pipeline_next_steps",
        steps=[
            "Open Neo4j Browser: http://localhost:7474",
            "Run Cypher queries to explore the graph",
            "Start GraphRAG API: python api.py",
            "View API docs: http://localhost:8000/docs",
            "Query with Python: python api_client_example.py",
            "Read documentation: RAG_DOCUMENTATION.md",
        ],
    )

    return True


def print_usage():
    """Print usage instructions"""
    print(
        """
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
"""
    )


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="TechCrunch Knowledge Graph Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--articles-dir",
        default="data/articles",
        help="Path to scraped articles directory",
    )

    parser.add_argument(
        "--output-dir", default="data/processing", help="Path for extracted entities"
    )

    parser.add_argument(
        "--max-articles",
        type=int,
        default=None,
        help="Limit number of articles to process",
    )

    parser.add_argument(
        "--skip-scraping", action="store_true", help="Skip web scraping phase"
    )

    parser.add_argument(
        "--skip-extraction", action="store_true", help="Skip entity extraction phase"
    )

    parser.add_argument(
        "--skip-graph", action="store_true", help="Skip graph construction phase"
    )

    parser.add_argument(
        "--skip-enrichment",
        action="store_true",
        help="Skip company intelligence enrichment phase (Phase 1.5)",
    )

    parser.add_argument(
        "--max-companies-per-article",
        type=int,
        default=None,
        help="Maximum number of companies to scrape per article (default: all)",
    )

    parser.add_argument(
        "--scrape-category",
        type=str,
        default=None,
        help="Category to scrape (e.g., 'startups', 'ai'). Enables Phase 0 scraping",
    )

    parser.add_argument(
        "--scrape-max-pages",
        type=int,
        default=None,
        help="Maximum pages to scrape (default: unlimited)",
    )

    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Don't resume from checkpoint (start fresh)",
    )

    parser.add_argument(
        "--no-validation", action="store_true", help="Skip data validation"
    )

    parser.add_argument(
        "--no-cleanup", action="store_true", help="Skip graph post-processing cleanup"
    )

    parser.add_argument(
        "--skip-post-processing",
        action="store_true",
        help="Skip post-processing (embeddings, deduplication, communities) - NOT RECOMMENDED - queries won't work without embeddings",
    )

    parser.add_argument(
        "--help-extended", action="store_true", help="Show extended help"
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
        skip_enrichment=args.skip_enrichment,
        skip_graph_building=args.skip_graph,
        scrape_category=args.scrape_category,
        scrape_max_pages=args.scrape_max_pages,
        resume_extraction=not args.no_resume,
        validate_data=not args.no_validation,
        auto_cleanup_graph=not args.no_cleanup,
        skip_post_processing=args.skip_post_processing,
        max_companies_to_scrape=args.max_companies_per_article,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
