"""
Configuration file for TechCrunch Scraper
Adjust these settings based on your needs
"""

import os
from pathlib import Path

# Scraping Configuration
SCRAPER_CONFIG = {
    # Output directory for scraped data (points to project root's data folder)
    "output_dir": str(Path(__file__).parent.parent / "data"),
    
    # Rate limiting (seconds between requests)
    "rate_limit_delay": 3.0,
    
    # Maximum pages to crawl (None = no limit)
    "max_pages": None,  # Set to a number like 5 for testing
    
    # Batch size for concurrent article extraction
    "batch_size": 10,
    
    # Target category URL
    "category_url": "https://techcrunch.com/category/startups/",
    
    # Browser configuration
    "browser": {
        "headless": True,
        "viewport_width": 1920,
        "viewport_height": 1080,
        "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    },
    
    # Crawler configuration
    "crawler": {
        "page_timeout": 60000,  # milliseconds (60 seconds)
        "wait_until": "load",  # Changed from "networkidle" for faster, more reliable completion
        "delay_before_return_html": 2.0  # seconds
    }
}

# Categories to scrape (you can extend this)
TECHCRUNCH_CATEGORIES = {
    "startups": "https://techcrunch.com/category/startups/",
    "ai": "https://techcrunch.com/category/artificial-intelligence/",
    "apps": "https://techcrunch.com/category/apps/",
    "enterprise": "https://techcrunch.com/category/enterprise/",
    "fintech": "https://techcrunch.com/category/fintech/",
    "venture": "https://techcrunch.com/category/venture/"
}

# Incremental scraping settings
INCREMENTAL_CONFIG = {
    # Enable incremental scraping (only new articles)
    "enabled": False,
    
    # Lookback window in hours (re-check recent articles)
    "lookback_hours": 24,
    
    # Checkpoint file for tracking progress
    "checkpoint_file": "scraping_checkpoint.json"
}