"""
TechCrunch Scraper using Crawl4AI
Implements two-phase scraping: URL Discovery and Article Extraction
"""

import asyncio
import json
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import re

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel, Field
from bs4 import BeautifulSoup


class ArticleMetadata(BaseModel):
    """Metadata for discovered article"""

    url: str
    title: str
    author: Optional[str] = None
    published_date: Optional[str] = None
    category: Optional[str] = None
    thumbnail: Optional[str] = None
    discovered_at: str
    page_number: int


class ArticleContent(BaseModel):
    """Full article content structure"""

    article_id: str
    url: str
    title: str
    author: Optional[str] = None
    published_date: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    content: Dict = Field(default_factory=dict)
    metadata: Dict = Field(default_factory=dict)
    raw_html: Optional[str] = None


class TechCrunchScraper:
    """Main scraper class for TechCrunch articles"""

    def __init__(
        self,
        output_dir: str = "/data/raw_data",
        rate_limit_delay: float = 3.0,
        max_pages: Optional[int] = None,
    ):
        self.output_dir = Path(output_dir)
        self.rate_limit_delay = rate_limit_delay
        self.max_pages = max_pages

        # Create directory structure
        self.articles_dir = self.output_dir / "articles"
        self.metadata_dir = self.output_dir / "metadata"
        self.articles_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        # Tracking
        self.discovered_articles: List[ArticleMetadata] = []
        self.failed_urls: List[Dict] = []
        self.stats = {
            "pages_crawled": 0,
            "articles_discovered": 0,
            "articles_extracted": 0,
            "extraction_failures": 0,
            "start_time": None,
            "end_time": None,
        }

    def generate_article_id(self, url: str) -> str:
        """Generate unique article ID from URL"""
        return hashlib.md5(url.encode()).hexdigest()[:12]

    def save_checkpoint(self, checkpoint_data: Dict, filename: str):
        """Save checkpoint for resumability"""
        checkpoint_path = self.metadata_dir / filename
        with open(checkpoint_path, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
        print(f"✓ Checkpoint saved: {filename}")

    async def discover_articles(
        self, category_url: str = "https://techcrunch.com/category/startups/"
    ) -> List[ArticleMetadata]:
        """
        Phase 1: Discover article URLs from category pages
        Handles pagination automatically
        """
        print("\n" + "=" * 80)
        print("PHASE 1: ARTICLE DISCOVERY")
        print("=" * 80)

        self.stats["start_time"] = datetime.now().isoformat()

        browser_config = BrowserConfig(
            headless=True,
            viewport_width=1920,
            viewport_height=1080,
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            wait_for_images=False,
            page_timeout=60000,  # Increased to 60 seconds
            delay_before_return_html=2.0,
            wait_until="load",  # Changed from "networkidle" to "load" for faster, more reliable completion
        )

        current_url = category_url
        page_num = 1

        async with AsyncWebCrawler(config=browser_config) as crawler:
            while current_url and (
                self.max_pages is None or page_num <= self.max_pages
            ):
                print(f"\n📄 Crawling page {page_num}: {current_url}")

                try:
                    result = await crawler.arun(url=current_url, config=crawler_config)

                    if not result.success:
                        print(
                            f"✗ Failed to crawl page {page_num}: {result.error_message}"
                        )
                        break

                    # Parse the HTML
                    soup = BeautifulSoup(result.html, "html.parser")

                    # Extract articles from this page
                    articles = self._extract_articles_from_page(soup, page_num)
                    self.discovered_articles.extend(articles)

                    print(f"  ✓ Found {len(articles)} articles on page {page_num}")
                    print(f"  ✓ Total discovered: {len(self.discovered_articles)}")

                    # Look for next page
                    next_url = self._find_next_page(soup, current_url)

                    # Update stats
                    self.stats["pages_crawled"] = page_num
                    self.stats["articles_discovered"] = len(self.discovered_articles)

                    # Save checkpoint after each page
                    self.save_checkpoint(
                        {
                            "last_page": page_num,
                            "last_url": current_url,
                            "articles_discovered": len(self.discovered_articles),
                            "timestamp": datetime.now().isoformat(),
                        },
                        f"discovery_checkpoint_page_{page_num}.json",
                    )

                    if not next_url:
                        print(f"\n✓ Reached last page (page {page_num})")
                        break

                    # Rate limiting
                    print(f"  ⏱ Waiting {self.rate_limit_delay}s before next page...")
                    await asyncio.sleep(self.rate_limit_delay)

                    current_url = next_url
                    page_num += 1

                except Exception as e:
                    print(f"✗ Error on page {page_num}: {str(e)}")
                    self.failed_urls.append(
                        {
                            "url": current_url,
                            "page": page_num,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                    break

        # Save discovered articles
        discovery_file = (
            self.metadata_dir
            / f"discovered_articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(discovery_file, "w", encoding="utf-8") as f:
            json.dump(
                [article.dict() for article in self.discovered_articles],
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"\n{'='*80}")
        print(f"DISCOVERY COMPLETE")
        print(f"{'='*80}")
        print(f"Total pages crawled: {self.stats['pages_crawled']}")
        print(f"Total articles discovered: {len(self.discovered_articles)}")
        print(f"Saved to: {discovery_file}")
        print(f"{'='*80}\n")

        return self.discovered_articles

    def _extract_articles_from_page(
        self, soup: BeautifulSoup, page_num: int
    ) -> List[ArticleMetadata]:
        """Extract article metadata from category page HTML"""
        articles = []

        # Find all article list items
        article_items = soup.find_all("li", class_="wp-block-post")

        for item in article_items:
            try:
                # Extract article URL and title
                title_link = item.find("a", class_="loop-card__title-link")
                if not title_link:
                    continue

                url = title_link.get("href") or title_link.get("data-destinationlink")
                title = title_link.get_text(strip=True)

                if not url or not title:
                    continue

                # Extract author
                author = None
                author_link = item.find("a", class_="loop-card__author")
                if author_link:
                    author = author_link.get_text(strip=True)

                # Extract publication date
                pub_date = None
                time_elem = item.find("time", class_="loop-card__time")
                if time_elem:
                    pub_date = time_elem.get("datetime")

                # Extract category
                category = None
                cat_link = item.find("a", class_="loop-card__cat")
                if cat_link:
                    category = cat_link.get_text(strip=True)

                # Extract thumbnail
                thumbnail = None
                img = item.find("img", class_="wp-post-image")
                if img:
                    thumbnail = img.get("src")

                article = ArticleMetadata(
                    url=url,
                    title=title,
                    author=author,
                    published_date=pub_date,
                    category=category,
                    thumbnail=thumbnail,
                    discovered_at=datetime.now().isoformat(),
                    page_number=page_num,
                )

                articles.append(article)

            except Exception as e:
                print(f"  ⚠ Error extracting article: {str(e)}")
                continue

        return articles

    def _find_next_page(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """Find the next page URL from pagination"""
        # Look for next button
        next_link = soup.find("a", class_="wp-block-query-pagination-next")

        if next_link:
            next_url = next_link.get("href") or next_link.get("data-destinationlink")
            if next_url:
                # Ensure absolute URL
                return urljoin(current_url, next_url)

        return None

    async def extract_articles(
        self, articles: Optional[List[ArticleMetadata]] = None, batch_size: int = 10
    ):
        """
        Phase 2: Extract full content from article pages
        Processes articles in batches with concurrency
        """
        if articles is None:
            articles = self.discovered_articles

        if not articles:
            print("⚠ No articles to extract. Run discovery first.")
            return

        print("\n" + "=" * 80)
        print("PHASE 2: ARTICLE EXTRACTION")
        print("=" * 80)
        print(f"Total articles to extract: {len(articles)}")
        print(f"Batch size: {batch_size}")
        print("=" * 80 + "\n")

        browser_config = BrowserConfig(
            headless=True,
            viewport_width=1920,
            viewport_height=1080,
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            wait_for_images=False,
            page_timeout=60000,  # Increased to 60 seconds
            delay_before_return_html=1.5,
            wait_until="load",  # Changed from "networkidle" to "load" for faster, more reliable completion
        )

        # Process in batches
        for i in range(0, len(articles), batch_size):
            batch = articles[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(articles) + batch_size - 1) // batch_size

            print(
                f"\n📦 Processing batch {batch_num}/{total_batches} ({len(batch)} articles)"
            )

            async with AsyncWebCrawler(config=browser_config) as crawler:
                tasks = [
                    self._extract_single_article(crawler, article, crawler_config)
                    for article in batch
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results
                for article, result in zip(batch, results):
                    if isinstance(result, Exception):
                        print(f"  ✗ Failed: {article.title[:50]}... - {str(result)}")
                        self.stats["extraction_failures"] += 1
                        self.failed_urls.append(
                            {
                                "url": article.url,
                                "title": article.title,
                                "error": str(result),
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                    elif result:
                        print(f"  ✓ Extracted: {article.title[:60]}...")
                        self.stats["articles_extracted"] += 1

            # Rate limiting between batches
            if i + batch_size < len(articles):
                wait_time = self.rate_limit_delay * 2
                print(f"  ⏱ Waiting {wait_time}s before next batch...")
                await asyncio.sleep(wait_time)

            # Save progress checkpoint
            self.save_checkpoint(
                {
                    "batch": batch_num,
                    "total_batches": total_batches,
                    "extracted": self.stats["articles_extracted"],
                    "failed": self.stats["extraction_failures"],
                    "timestamp": datetime.now().isoformat(),
                },
                f"extraction_checkpoint_batch_{batch_num}.json",
            )

        # Save failed URLs
        if self.failed_urls:
            failed_file = (
                self.metadata_dir
                / f"failed_articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(failed_file, "w", encoding="utf-8") as f:
                json.dump(self.failed_urls, f, indent=2, ensure_ascii=False)
            print(f"\n⚠ {len(self.failed_urls)} failures saved to: {failed_file}")

        self.stats["end_time"] = datetime.now().isoformat()
        self._print_final_stats()

    async def _extract_single_article(
        self,
        crawler: AsyncWebCrawler,
        article_meta: ArticleMetadata,
        config: CrawlerRunConfig,
    ) -> Optional[ArticleContent]:
        """Extract content from a single article page"""
        try:
            result = await crawler.arun(url=article_meta.url, config=config)

            if not result.success:
                raise Exception(f"Crawl failed: {result.error_message}")

            # Parse HTML
            soup = BeautifulSoup(result.html, "html.parser")

            # Extract headline
            headline_elem = soup.find("h1", class_="article-hero__title")
            headline = (
                headline_elem.get_text(strip=True)
                if headline_elem
                else article_meta.title
            )

            # Extract main content
            content_div = soup.find("div", class_="entry-content")

            if not content_div:
                raise Exception("Content div not found")

            # Remove ad units and other unwanted elements
            for ad in content_div.find_all(
                ["div", "aside"], class_=re.compile("ad-unit|ad-slot")
            ):
                ad.decompose()

            # Extract paragraphs
            paragraphs = []
            for p in content_div.find_all("p", class_="wp-block-paragraph"):
                text = p.get_text(strip=True)
                if text and len(text) > 20:  # Filter out very short paragraphs
                    paragraphs.append(text)

            body_text = "\n\n".join(paragraphs)

            # Extract published date from article page (more accurate)
            pub_date = article_meta.published_date
            time_elem = soup.find("time")
            if time_elem:
                pub_date = time_elem.get("datetime") or pub_date

            # Extract author from article page
            author = article_meta.author
            author_elem = soup.find("a", class_="loop-card__author") or soup.find(
                "a", href=re.compile("/author/")
            )
            if author_elem:
                author = author_elem.get_text(strip=True)

            # Extract categories
            categories = []
            if article_meta.category:
                categories.append(article_meta.category)

            for cat_link in soup.find_all("a", href=re.compile("/category/")):
                cat = cat_link.get_text(strip=True)
                if cat and cat not in categories:
                    categories.append(cat)

            # Create article content object
            article_id = self.generate_article_id(article_meta.url)

            article_content = ArticleContent(
                article_id=article_id,
                url=article_meta.url,
                title=headline,
                author=author,
                published_date=pub_date,
                categories=categories,
                content={
                    "headline": headline,
                    "body_text": body_text,
                    "body_html": str(content_div) if content_div else "",
                    "paragraphs": paragraphs,
                    "word_count": len(body_text.split()),
                },
                metadata={
                    "scraped_at": datetime.now().isoformat(),
                    "extraction_method": "css",
                    "source_page": article_meta.page_number,
                    "thumbnail": article_meta.thumbnail,
                },
                raw_html=result.html[:50000],  # Limit raw HTML size
            )

            # Save to file
            self._save_article(article_content)

            return article_content

        except Exception as e:
            raise Exception(f"Extraction error: {str(e)}")

    def _save_article(self, article: ArticleContent):
        """Save article to JSON file"""
        # Create date-based directory
        if article.published_date:
            try:
                date_obj = datetime.fromisoformat(
                    article.published_date.replace("Z", "+00:00")
                )
                date_dir = (
                    self.articles_dir
                    / date_obj.strftime("%Y-%m")
                    / date_obj.strftime("%d")
                )
            except:
                date_dir = self.articles_dir / "unknown-date"
        else:
            date_dir = self.articles_dir / "unknown-date"

        date_dir.mkdir(parents=True, exist_ok=True)

        # Create filename from article ID
        filename = f"tc_{article.article_id}.json"
        filepath = date_dir / filename

        # Save to JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(article.dict(), f, indent=2, ensure_ascii=False)

    def _print_final_stats(self):
        """Print final statistics"""
        print("\n" + "=" * 80)
        print("EXTRACTION COMPLETE - FINAL STATISTICS")
        print("=" * 80)
        print(f"Articles discovered:  {self.stats['articles_discovered']}")
        print(f"Articles extracted:   {self.stats['articles_extracted']}")
        print(f"Extraction failures:  {self.stats['extraction_failures']}")

        if self.stats["articles_discovered"] > 0:
            success_rate = (
                self.stats["articles_extracted"] / self.stats["articles_discovered"]
            ) * 100
            print(f"Success rate:         {success_rate:.1f}%")

        if self.stats["start_time"] and self.stats["end_time"]:
            start = datetime.fromisoformat(self.stats["start_time"])
            end = datetime.fromisoformat(self.stats["end_time"])
            duration = (end - start).total_seconds()
            print(
                f"Total time:           {duration:.1f} seconds ({duration/60:.1f} minutes)"
            )

            if self.stats["articles_extracted"] > 0:
                rate = self.stats["articles_extracted"] / duration
                print(f"Extraction rate:      {rate:.2f} articles/second")

        print("=" * 80 + "\n")

        # Save final stats
        stats_file = (
            self.metadata_dir
            / f"scraping_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
        print(f"Statistics saved to: {stats_file}\n")


async def main():
    """Main execution function"""
    from scraper_config import SCRAPER_CONFIG

    # Initialize scraper
    scraper = TechCrunchScraper(
        output_dir=SCRAPER_CONFIG["output_dir"],
        rate_limit_delay=3.0,
        max_pages=3,  # Limit to 3 pages for testing (remove for full scrape)
    )

    # Phase 1: Discover articles
    articles = await scraper.discover_articles(
        category_url="https://techcrunch.com/category/startups/"
    )

    if not articles:
        print("No articles discovered. Exiting.")
        return

    # Phase 2: Extract article content
    await scraper.extract_articles(
        articles=articles, batch_size=5  # Process 5 articles at a time
    )

    print("✅ Scraping complete!")
    print(f"📁 Check output directory: {scraper.output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
