#!/usr/bin/env python3
"""
Simple script to run the TechCrunch scraper
Usage: python run_scraper.py [options]
"""

import asyncio
import argparse
from pathlib import Path
from techcrunch_scraper import TechCrunchScraper
from scraper_config import SCRAPER_CONFIG, TECHCRUNCH_CATEGORIES


async def run_scraper(
    category: str = "startups",
    max_pages: int = None,
    batch_size: int = 10,
    output_dir: str = None
):
    """Run the scraper with specified parameters"""
    
    # Get category URL
    if category in TECHCRUNCH_CATEGORIES:
        category_url = TECHCRUNCH_CATEGORIES[category]
    else:
        category_url = category  # Assume it's a full URL
    
    # Initialize scraper
    scraper = TechCrunchScraper(
        output_dir=output_dir or SCRAPER_CONFIG["output_dir"],
        rate_limit_delay=SCRAPER_CONFIG["rate_limit_delay"],
        max_pages=max_pages
    )
    
    print(f"\n{'='*80}")
    print(f"TechCrunch Scraper - Starting")
    print(f"{'='*80}")
    print(f"Category:     {category}")
    print(f"URL:          {category_url}")
    print(f"Max Pages:    {max_pages or 'Unlimited'}")
    print(f"Batch Size:   {batch_size}")
    print(f"Output Dir:   {scraper.output_dir}")
    print(f"{'='*80}\n")
    
    # Phase 1: Discover articles
    print("Starting Phase 1: Article Discovery...")
    articles = await scraper.discover_articles(category_url=category_url)
    
    if not articles:
        print("❌ No articles discovered. Exiting.")
        return
    
    print(f"\n✓ Discovered {len(articles)} articles")
    
    # Ask user to confirm extraction
    print(f"\nProceed with extracting {len(articles)} articles? (y/n): ", end="", flush=True)
    confirm = input().lower()
    if confirm != 'y':
        print("Extraction cancelled.")
        return
    
    # Phase 2: Extract article content
    print("\nStarting Phase 2: Article Extraction...")
    await scraper.extract_articles(
        articles=articles,
        batch_size=batch_size
    )
    
    print("\n" + "="*80)
    print("✅ SCRAPING COMPLETE!")
    print("="*80)
    print(f"📁 Output directory: {scraper.output_dir}")
    print(f"📊 Articles extracted: {scraper.stats['articles_extracted']}/{len(articles)}")
    print("="*80 + "\n")


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description="TechCrunch Article Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape 3 pages from startups category
  python run_scraper.py --category startups --max-pages 3
  
  # Scrape AI category with custom batch size
  python run_scraper.py --category ai --batch-size 20
  
  # Scrape custom URL
  python run_scraper.py --category https://techcrunch.com/category/fintech/
  
Available categories:
  startups, ai, apps, enterprise, fintech, venture
        """
    )
    
    parser.add_argument(
        "--category",
        type=str,
        default="startups",
        help="Category to scrape (name or full URL)"
    )
    
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of pages to crawl (default: unlimited)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of articles to process concurrently (default: 10)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for scraped data"
    )
    
    parser.add_argument(
        "--discovery-only",
        action="store_true",
        help="Only run discovery phase (don't extract articles)"
    )
    
    args = parser.parse_args()
    
    # Run the scraper
    asyncio.run(run_scraper(
        category=args.category,
        max_pages=args.max_pages,
        batch_size=args.batch_size,
        output_dir=args.output_dir
    ))


if __name__ == "__main__":
    main()