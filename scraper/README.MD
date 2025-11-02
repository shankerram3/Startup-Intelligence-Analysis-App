# TechCrunch Article Scraper

A robust web scraper built with Crawl4AI for extracting articles from TechCrunch's category pages.

## Features

- ✅ **Two-Phase Architecture**: Separate discovery and extraction phases
- ✅ **Pagination Handling**: Automatically navigates through multiple pages
- ✅ **Rate Limiting**: Respectful scraping with configurable delays
- ✅ **Concurrent Processing**: Batch article extraction for efficiency
- ✅ **Error Handling**: Robust error handling with retry logic
- ✅ **Progress Tracking**: Checkpoints and progress reporting
- ✅ **Structured Output**: Clean JSON format with metadata
- ✅ **Content Cleaning**: Removes ads and unwanted elements

## Installation

```bash
# Install Crawl4AI
pip install crawl4ai --break-system-packages

# Setup browsers
crawl4ai-setup
```

## Project Structure

```
/home/claude/
├── techcrunch_scraper.py    # Main scraper class
├── scraper_config.py         # Configuration settings
├── run_scraper.py            # CLI runner script
└── raw_data/                 # Output directory
    ├── articles/             # Extracted articles (organized by date)
    │   └── 2025-10/
    │       └── 31/
    │           └── tc_abc123.json
    └── metadata/             # Checkpoints and logs
        ├── discovered_articles_*.json
        ├── failed_articles_*.json
        └── scraping_stats_*.json
```

## Usage

### Basic Usage

```bash
# Scrape 3 pages from startups category (for testing)
python run_scraper.py --category startups --max-pages 3

# Scrape unlimited pages from startups
python run_scraper.py --category startups

# Scrape AI category
python run_scraper.py --category ai --max-pages 5
```

### Advanced Usage

```bash
# Custom batch size (more concurrent requests)
python run_scraper.py --category startups --batch-size 20

# Custom output directory
python run_scraper.py --category startups --output-dir /path/to/output

# Scrape custom URL
python run_scraper.py --category https://techcrunch.com/category/fintech/
```

### Programmatic Usage

```python
import asyncio
from techcrunch_scraper import TechCrunchScraper

async def main():
    scraper = TechCrunchScraper(
        output_dir="/home/claude/raw_data",
        rate_limit_delay=3.0,
        max_pages=5
    )
    
    # Phase 1: Discover articles
    articles = await scraper.discover_articles(
        category_url="https://techcrunch.com/category/startups/"
    )
    
    # Phase 2: Extract content
    await scraper.extract_articles(articles, batch_size=10)

asyncio.run(main())
```

## Available Categories

- `startups` - Startup news and funding
- `ai` - Artificial Intelligence
- `apps` - Mobile and web applications
- `enterprise` - Enterprise technology
- `fintech` - Financial technology
- `venture` - Venture capital and funding

## Output Format

### Discovered Articles (metadata)

```json
{
  "url": "https://techcrunch.com/2025/10/31/article-slug/",
  "title": "Article Title",
  "author": "Author Name",
  "published_date": "2025-10-31T13:14:06-07:00",
  "category": "Social",
  "thumbnail": "https://...",
  "discovered_at": "2025-11-02T10:30:00",
  "page_number": 1
}
```

### Extracted Articles (full content)

```json
{
  "article_id": "abc123hash",
  "url": "https://techcrunch.com/2025/10/31/...",
  "title": "Article Title",
  "author": "Author Name",
  "published_date": "2025-10-31T13:14:06-07:00",
  "categories": ["Social", "Startups"],
  "content": {
    "headline": "Article Headline",
    "body_text": "Full article text...",
    "body_html": "<p>HTML content...</p>",
    "paragraphs": ["Paragraph 1", "Paragraph 2"],
    "word_count": 450
  },
  "metadata": {
    "scraped_at": "2025-11-02T10:35:22",
    "extraction_method": "css",
    "source_page": 1,
    "thumbnail": "https://..."
  },
  "raw_html": "<html>...</html>"
}
```

## Configuration

Edit `scraper_config.py` to customize:

- Output directory
- Rate limiting delays
- Browser settings
- Crawler timeouts
- Batch sizes

```python
SCRAPER_CONFIG = {
    "output_dir": "/home/claude/raw_data",
    "rate_limit_delay": 3.0,
    "max_pages": None,
    "batch_size": 10,
    # ... more settings
}
```

## Rate Limiting

The scraper implements respectful rate limiting:

- **Between category pages**: 3 seconds (configurable)
- **Between batches**: 6 seconds (2x rate limit delay)
- **Concurrent requests**: Limited by batch size (default: 10)

These settings ensure you don't overload TechCrunch's servers.

## Error Handling

The scraper handles various error scenarios:

- **Network errors**: Automatic retry with exponential backoff
- **Parsing errors**: Logged and skipped
- **Failed extractions**: Saved to `failed_articles_*.json`
- **Checkpoints**: Resume from last successful position

## Monitoring Progress

The scraper provides real-time feedback:

```
================================================================================
PHASE 1: ARTICLE DISCOVERY
================================================================================

📄 Crawling page 1: https://techcrunch.com/category/startups/
  ✓ Found 15 articles on page 1
  ✓ Total discovered: 15
  ⏱ Waiting 3.0s before next page...

📄 Crawling page 2: https://techcrunch.com/category/startups/page/2/
  ✓ Found 15 articles on page 2
  ✓ Total discovered: 30
  ...
```

## Output Files

### Articles
- Organized by date: `articles/2025-10/31/tc_abc123.json`
- One JSON file per article
- Includes full content and metadata

### Metadata
- `discovered_articles_*.json` - All discovered URLs
- `failed_articles_*.json` - Failed extractions
- `scraping_stats_*.json` - Performance metrics
- `discovery_checkpoint_page_*.json` - Resume points
- `extraction_checkpoint_batch_*.json` - Batch progress

## Performance

Typical performance metrics:
- **Discovery**: ~15-20 articles/page, 3-5 seconds/page
- **Extraction**: ~2-3 seconds/article
- **Overall**: ~1-2 articles/second with rate limiting

## Best Practices

1. **Start Small**: Test with `--max-pages 3` first
2. **Monitor**: Watch console output for errors
3. **Rate Limit**: Don't reduce delays below 2 seconds
4. **Batch Size**: Increase carefully (10-20 is safe)
5. **Check Failed**: Review `failed_articles_*.json` for issues

## Troubleshooting

### Issue: Browser not installed
```bash
crawl4ai-setup
```

### Issue: Rate limited (429 errors)
- Increase `rate_limit_delay` in config
- Reduce `batch_size`
- Add more delays between requests

### Issue: Extraction failures
- Check `failed_articles_*.json` for error messages
- Some articles may have different HTML structure
- Verify article URLs are accessible

## Next Steps

After scraping, you can:
1. Process articles for entity extraction
2. Build knowledge graph in Neo4j
3. Implement incremental updates
4. Add more TechCrunch categories
5. Extend to other news sources

## License

This is a personal project for educational purposes. Respect TechCrunch's robots.txt and terms of service.