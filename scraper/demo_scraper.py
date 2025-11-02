"""
Demo script showing how the TechCrunch scraper works
Uses the example HTML you provided to demonstrate extraction
"""

from bs4 import BeautifulSoup
import json
from datetime import datetime
from pathlib import Path


# Sample HTML from TechCrunch category page (from your example)
CATEGORY_PAGE_HTML = '''
<li class="wp-block-post post-3064339 post type-post status-publish format-standard has-post-thumbnail hentry category-startups category-apps category-social tag-social-media tag-bluesky">
    <div class="wp-block-techcrunch-card wp-block-null">
        <div class="loop-card loop-card--post-type-post loop-card--default loop-card--horizontal loop-card--wide loop-card--force-storyline-aspect-ratio">
            <figure class="loop-card__figure">
                <img width="563" height="375" src="https://techcrunch.com/wp-content/uploads/2025/01/bluesky-GettyImages-2185142051.jpg?w=563" class="attachment-card-block-16x9 size-card-block-16x9 wp-post-image" alt="Bluesky logo">
            </figure>
            <div class="loop-card__content">
                <div class="loop-card__cat-group">
                    <a data-destinationlink="https://techcrunch.com/category/social/" href="https://techcrunch.com/category/social/" class="loop-card__cat">Social</a>
                </div>
                <h3 class="loop-card__title">
                    <a data-destinationlink="https://techcrunch.com/2025/10/31/bluesky-hits-40-million-users-introduces-dislikes-beta/" href="https://techcrunch.com/2025/10/31/bluesky-hits-40-million-users-introduces-dislikes-beta/" class="loop-card__title-link">Bluesky hits 40 million users, introduces 'dislikes' beta</a>
                </h3>
                <div class="loop-card__meta">
                    <ul class="loop-card__meta-item loop-card__author-list">
                        <li><a data-destinationlink="https://techcrunch.com/author/sarah-perez/" class="loop-card__author" href="https://techcrunch.com/author/sarah-perez/">Sarah Perez</a></li>
                    </ul>
                    <time datetime="2025-10-31T13:14:06-07:00" class="loop-card__meta-item loop-card__time wp-block-tc23-post-time-ago">2 days ago</time>
                </div>
            </div>
        </div>
    </div>
</li>
'''


def demo_article_discovery():
    """Demonstrate article discovery from category page"""
    print("\n" + "="*80)
    print("DEMO: Article Discovery from Category Page")
    print("="*80 + "\n")
    
    soup = BeautifulSoup(CATEGORY_PAGE_HTML, 'html.parser')
    
    # Find article item
    article_item = soup.find('li', class_='wp-block-post')
    
    if article_item:
        # Extract URL and title
        title_link = article_item.find('a', class_='loop-card__title-link')
        url = title_link.get('href') or title_link.get('data-destinationlink')
        title = title_link.get_text(strip=True)
        
        # Extract author
        author_link = article_item.find('a', class_='loop-card__author')
        author = author_link.get_text(strip=True) if author_link else None
        
        # Extract date
        time_elem = article_item.find('time', class_='loop-card__time')
        pub_date = time_elem.get('datetime') if time_elem else None
        
        # Extract category
        cat_link = article_item.find('a', class_='loop-card__cat')
        category = cat_link.get_text(strip=True) if cat_link else None
        
        # Extract thumbnail
        img = article_item.find('img', class_='wp-post-image')
        thumbnail = img.get('src') if img else None
        
        article_metadata = {
            "url": url,
            "title": title,
            "author": author,
            "published_date": pub_date,
            "category": category,
            "thumbnail": thumbnail,
            "discovered_at": datetime.now().isoformat(),
            "page_number": 1
        }
        
        print("✓ Successfully extracted article metadata:\n")
        print(json.dumps(article_metadata, indent=2))
        
        return article_metadata
    
    return None


def demo_article_extraction():
    """Demonstrate article content extraction"""
    print("\n" + "="*80)
    print("DEMO: Article Content Extraction")
    print("="*80 + "\n")
    
    # Sample article HTML structure
    article_html = '''
    <article>
        <h1 class="article-hero__title wp-block-post-title">Bluesky hits 40 million users, introduces 'dislikes' beta</h1>
        <time datetime="2025-10-31T13:14:06-07:00">October 31, 2025</time>
        
        <div class="entry-content wp-block-post-content">
            <p class="wp-block-paragraph">Social network Bluesky, which on Friday announced a new <a href="#">milestone of 40 million users</a>, will soon start testing "dislikes" as a way to improve personalization on its main Discover feed and others.</p>
            
            <p class="wp-block-paragraph">The news was shared alongside a host of other <a href="#">conversation control updates and changes</a>, which include smaller tweaks to replies, improved detection of toxic comments, and other ways to prioritize more relevant conversations to the individual user.</p>
            
            <div class="ad-unit" style="display: none;">
                <!-- This ad unit will be removed -->
            </div>
            
            <p class="wp-block-paragraph">With the "dislikes" beta rolling out soon, Bluesky will take into account the new signal to improve user personalization. As users "dislike" posts, the system will learn what sort of content they want to see less of.</p>
            
            <p class="wp-block-paragraph">The company explained the changes are designed to make Bluesky a place for more "fun, genuine, and respectful exchanges" — an edict that follows a month of unrest on the platform.</p>
        </div>
    </article>
    '''
    
    soup = BeautifulSoup(article_html, 'html.parser')
    
    # Extract headline
    headline_elem = soup.find('h1', class_='article-hero__title')
    headline = headline_elem.get_text(strip=True) if headline_elem else "No headline"
    
    # Extract content
    content_div = soup.find('div', class_='entry-content')
    
    if content_div:
        # Remove ad units
        for ad in content_div.find_all('div', class_='ad-unit'):
            ad.decompose()
        
        # Extract paragraphs
        paragraphs = []
        for p in content_div.find_all('p', class_='wp-block-paragraph'):
            text = p.get_text(strip=True)
            if text and len(text) > 20:
                paragraphs.append(text)
        
        body_text = '\n\n'.join(paragraphs)
        
        article_content = {
            "article_id": "demo_abc123",
            "url": "https://techcrunch.com/2025/10/31/bluesky-hits-40-million-users-introduces-dislikes-beta/",
            "title": headline,
            "author": "Sarah Perez",
            "published_date": "2025-10-31T13:14:06-07:00",
            "categories": ["Social", "Startups"],
            "content": {
                "headline": headline,
                "body_text": body_text,
                "paragraphs": paragraphs,
                "word_count": len(body_text.split())
            },
            "metadata": {
                "scraped_at": datetime.now().isoformat(),
                "extraction_method": "css",
                "source_page": 1
            }
        }
        
        print("✓ Successfully extracted article content:\n")
        print(f"Headline: {headline}")
        print(f"Paragraphs: {len(paragraphs)}")
        print(f"Word count: {len(body_text.split())}")
        print(f"\nFirst paragraph:\n{paragraphs[0][:200]}...")
        print(f"\nFull extraction:")
        print(json.dumps(article_content, indent=2))
        
        return article_content
    
    return None


def demo_file_saving():
    """Demonstrate file saving structure"""
    print("\n" + "="*80)
    print("DEMO: File Organization")
    print("="*80 + "\n")
    
    base_dir = Path("/home/claude/raw_data")
    
    # Example file structure
    structure = """
    /home/claude/raw_data/
    ├── articles/                          # Extracted articles
    │   ├── 2025-10/                       # Organized by year-month
    │   │   ├── 31/                        # Then by day
    │   │   │   ├── tc_abc123.json        # Individual article files
    │   │   │   ├── tc_def456.json
    │   │   │   └── tc_ghi789.json
    │   │   └── 30/
    │   │       └── tc_jkl012.json
    │   └── 2025-11/
    │       └── 01/
    │           └── tc_mno345.json
    │
    └── metadata/                          # Metadata and logs
        ├── discovered_articles_20251102_140348.json
        ├── failed_articles_20251102_141522.json
        ├── scraping_stats_20251102_142105.json
        ├── discovery_checkpoint_page_1.json
        ├── discovery_checkpoint_page_2.json
        ├── extraction_checkpoint_batch_1.json
        └── extraction_checkpoint_batch_2.json
    """
    
    print(structure)
    
    # Create sample file
    articles_dir = base_dir / "articles" / "2025-10" / "31"
    articles_dir.mkdir(parents=True, exist_ok=True)
    
    sample_article = {
        "article_id": "demo_sample",
        "title": "Sample Article",
        "content": {
            "body_text": "This is a sample article to demonstrate the file structure."
        },
        "metadata": {
            "scraped_at": datetime.now().isoformat()
        }
    }
    
    sample_file = articles_dir / "tc_demo_sample.json"
    with open(sample_file, 'w', encoding='utf-8') as f:
        json.dump(sample_article, f, indent=2)
    
    print(f"\n✓ Sample file created: {sample_file}")
    print(f"✓ File exists: {sample_file.exists()}")
    
    # List files
    if articles_dir.exists():
        files = list(articles_dir.glob("*.json"))
        print(f"✓ Files in directory: {len(files)}")


def demo_pagination_logic():
    """Demonstrate pagination navigation"""
    print("\n" + "="*80)
    print("DEMO: Pagination Logic")
    print("="*80 + "\n")
    
    # Sample pagination HTML
    pagination_html = '''
    <nav class="wp-block-query-pagination">
        <a data-destinationlink="https://techcrunch.com/category/startups/page/2/" 
           href="https://techcrunch.com/category/startups/page/2/" 
           class="wp-block-query-pagination-next">
            <span>Next</span>
        </a>
    </nav>
    '''
    
    soup = BeautifulSoup(pagination_html, 'html.parser')
    
    next_link = soup.find('a', class_='wp-block-query-pagination-next')
    
    if next_link:
        next_url = next_link.get('href') or next_link.get('data-destinationlink')
        print(f"✓ Found next page URL: {next_url}")
        print(f"✓ Would continue to page 2")
    else:
        print("✓ No next page found - would stop pagination")
    
    print("\nPagination Flow:")
    print("1. Start: https://techcrunch.com/category/startups/")
    print("2. Extract articles from page 1")
    print("3. Find 'Next' button → https://techcrunch.com/category/startups/page/2/")
    print("4. Wait 3 seconds (rate limiting)")
    print("5. Extract articles from page 2")
    print("6. Find 'Next' button → https://techcrunch.com/category/startups/page/3/")
    print("7. Continue until no 'Next' button found")


def main():
    """Run all demonstrations"""
    print("\n" + "="*80)
    print("TechCrunch Scraper - Functionality Demonstration")
    print("="*80)
    print("This demo shows how the scraper extracts data from TechCrunch")
    print("="*80)
    
    # Demo 1: Article Discovery
    article_meta = demo_article_discovery()
    
    # Demo 2: Article Extraction
    article_content = demo_article_extraction()
    
    # Demo 3: File Organization
    demo_file_saving()
    
    # Demo 4: Pagination
    demo_pagination_logic()
    
    print("\n" + "="*80)
    print("✅ DEMONSTRATION COMPLETE")
    print("="*80)
    print("\nKey Points:")
    print("• The scraper uses BeautifulSoup to parse HTML")
    print("• Article metadata is extracted from category pages")
    print("• Full content is extracted from individual article pages")
    print("• Data is saved in organized JSON files")
    print("• Pagination is handled automatically")
    print("• Rate limiting prevents server overload")
    print("\nNote: The actual scraper uses Crawl4AI to fetch live pages")
    print("      This demo uses sample HTML to show the extraction logic")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()