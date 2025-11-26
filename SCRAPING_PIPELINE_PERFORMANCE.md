# Scraping & Pipeline Performance Optimization Guide

This guide provides strategies to significantly improve scraping and pipeline processing performance.

---

## 📊 Current Performance Characteristics

### Scraping
- **Batch size**: 10 articles (configurable)
- **Rate limit**: 3.0 seconds between pages
- **Retry logic**: 3 attempts with exponential backoff
- **Concurrency**: Sequential page discovery, parallel article extraction

### Pipeline
- **Entity extraction**: Sequential processing
- **Checkpoint frequency**: Every 10 articles
- **Validation**: Per-article validation
- **Graph building**: Sequential node/relationship creation

---

## 🚀 Quick Wins (High Impact, Low Effort)

### 1. Increase Scraper Batch Size

**Current**: `batch_size=10` in pipeline.py  
**Recommended**: `batch_size=20-30` (depending on system resources)

**Impact**: 2-3x faster article extraction  
**Risk**: Low - may increase memory usage slightly

**Implementation**:
```python
# In pipeline.py line 194, change:
asyncio.run(scraper.extract_articles(articles=articles, batch_size=20))  # Increased from 10
```

### 2. Reduce Rate Limiting Delays

**Current**: `rate_limit_delay=3.0` seconds  
**Recommended**: `rate_limit_delay=1.0-1.5` seconds (be respectful of TechCrunch's servers)

**Impact**: 2x faster page discovery  
**Risk**: Medium - may hit rate limits if too aggressive

**Implementation**:
```python
# In pipeline.py line 167, change:
scraper = TechCrunchScraper(
    output_dir=articles_dir,
    rate_limit_delay=1.0,  # Reduced from 3.0
    max_pages=scrape_max_pages,
)
```

### 3. Optimize Browser Configuration

**Current**: Full browser with images  
**Recommended**: Disable images, reduce viewport size

**Impact**: 30-50% faster page loads  
**Risk**: Low - may miss some dynamic content

**Implementation**:
```python
# In scraper/techcrunch_scraper.py, update browser_config:
browser_config = BrowserConfig(
    headless=True,
    viewport_width=1280,  # Reduced from 1920
    viewport_height=720,  # Reduced from 1080
    user_agent="...",
    disable_images=True,  # NEW: Skip image loading
    disable_javascript=False,  # Keep JS for dynamic content
)
```

### 4. Increase Checkpoint Frequency

**Current**: Every 10 articles  
**Recommended**: Every 25-50 articles (or use async checkpointing)

**Impact**: 5-10% faster extraction (less I/O overhead)  
**Risk**: Low - slightly more data loss risk on crash

**Implementation**:
```python
# In entity_extractor.py, change checkpoint frequency:
if i % 25 == 0:  # Changed from 10
    checkpoint.save()
```

---

## 🔧 Medium-Term Optimizations

### 5. Parallel Entity Extraction

**Current**: Sequential processing  
**Recommended**: Batch OpenAI API calls or use async processing

**Impact**: 3-5x faster entity extraction  
**Risk**: Medium - requires careful rate limit handling

**Implementation Options**:

#### Option A: Batch OpenAI Calls
```python
# In entity_extractor.py, modify to batch articles:
async def extract_batch(articles_batch: List[Dict], extractor):
    """Extract entities from multiple articles in parallel"""
    tasks = [extractor.extract_from_article_async(article) for article in articles_batch]
    return await asyncio.gather(*tasks, return_exceptions=True)

# Process in batches of 5-10 articles
batch_size = 5
for i in range(0, len(articles), batch_size):
    batch = articles[i:i+batch_size]
    extractions = await extract_batch(batch, extractor)
```

#### Option B: Use OpenAI Batch API
```python
# For large-scale processing, use OpenAI's batch API
# This allows queuing multiple requests and processing asynchronously
```

### 6. Optimize Database Operations

**Current**: Individual node/relationship creation  
**Recommended**: Batch transactions

**Impact**: 5-10x faster graph building  
**Risk**: Low - standard Neo4j optimization

**Implementation**:
```python
# In graph_builder.py, use batch transactions:
BATCH_SIZE = 1000

def create_nodes_batch(entities: List[Dict], driver):
    """Create nodes in batches"""
    with driver.session() as session:
        for i in range(0, len(entities), BATCH_SIZE):
            batch = entities[i:i+BATCH_SIZE]
            query = """
            UNWIND $entities as entity
            MERGE (e:Entity {id: entity.id})
            SET e += entity.properties
            """
            session.run(query, entities=batch)

def create_relationships_batch(relationships: List[Dict], driver):
    """Create relationships in batches"""
    with driver.session() as session:
        for i in range(0, len(relationships), BATCH_SIZE):
            batch = relationships[i:i+BATCH_SIZE]
            query = """
            UNWIND $rels as rel
            MATCH (a {id: rel.from_id})
            MATCH (b {id: rel.to_id})
            MERGE (a)-[r:REL_TYPE]->(b)
            SET r += rel.properties
            """
            session.run(query, rels=batch)
```

### 7. Parallel Graph Building Phases

**Current**: Sequential phases  
**Recommended**: Run independent phases in parallel

**Impact**: 20-30% faster overall pipeline  
**Risk**: Low - only if phases are truly independent

**Implementation**:
```python
# Run embedding generation and community detection in parallel
async def parallel_postprocessing(driver):
    """Run post-processing steps in parallel where possible"""
    tasks = [
        generate_embeddings_async(driver),
        detect_communities_async(driver),
        calculate_relationship_scores_async(driver),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### 8. Optimize File I/O

**Current**: Frequent file writes  
**Recommended**: Buffer writes, use async I/O

**Impact**: 10-20% faster processing  
**Risk**: Low - standard optimization

**Implementation**:
```python
import aiofiles

# Use async file operations
async def save_extraction_async(output_file: Path, extraction: Dict):
    """Save extraction using async I/O"""
    async with aiofiles.open(output_file, 'w') as f:
        await f.write(json.dumps(extraction, indent=2, ensure_ascii=False))

# Batch file writes
async def save_extractions_batch(extractions: List[Dict], output_dir: Path):
    """Save multiple extractions in parallel"""
    tasks = [
        save_extraction_async(output_dir / f"extraction_{e['article_id']}.json", e)
        for e in extractions
    ]
    await asyncio.gather(*tasks, return_exceptions=True)
```

---

## 🎯 Advanced Optimizations

### 9. Implement Request Caching

**Cache discovered articles and scraped content**

**Impact**: Avoid re-scraping on retries  
**Risk**: Low - use with care to avoid stale data

**Implementation**:
```python
# Add caching layer for scraped articles
from functools import lru_cache
import hashlib

class CachedScraper(TechCrunchScraper):
    def __init__(self, *args, cache_dir=".cache", **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cache_key(self, url: str) -> str:
        """Generate cache key from URL"""
        return hashlib.md5(url.encode()).hexdigest()
    
    async def extract_article_cached(self, article: ArticleMetadata):
        """Extract article with caching"""
        cache_key = self.get_cache_key(article.url)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        # Check cache
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        
        # Scrape and cache
        result = await self.extract_article(article)
        with open(cache_file, 'w') as f:
            json.dump(result, f)
        
        return result
```

### 10. Use Connection Pooling for Neo4j

**Current**: Single connection per operation  
**Recommended**: Connection pool

**Impact**: 20-30% faster database operations  
**Risk**: Low - standard practice

**Implementation**:
```python
# Neo4j driver already uses connection pooling
# Just ensure optimal configuration:
driver = GraphDatabase.driver(
    neo4j_uri,
    auth=(neo4j_user, neo4j_password),
    max_connection_lifetime=3600,
    max_connection_pool_size=50,  # Increase pool size
    connection_acquisition_timeout=60,
)
```

### 11. Optimize Validation

**Current**: Validate every article  
**Recommended**: Sample validation or async validation

**Impact**: 5-10% faster extraction  
**Risk**: Medium - may miss invalid data

**Implementation**:
```python
# Only validate every Nth article
VALIDATE_SAMPLE_RATE = 0.1  # Validate 10% of articles

if validate_data and (i % (1/VALIDATE_SAMPLE_RATE) == 0):
    is_valid, error_msg = validate_article(article_data)
    # ...
```

### 12. Implement Progress Tracking with ETA

**Better visibility into performance**

**Implementation**:
```python
import time
from collections import deque

class PerformanceTracker:
    def __init__(self):
        self.start_time = time.time()
        self.recent_times = deque(maxlen=10)
        self.processed = 0
    
    def record(self):
        """Record processing time for current item"""
        self.processed += 1
        elapsed = time.time() - self.start_time
        avg_time = elapsed / self.processed
        self.recent_times.append(avg_time)
    
    def get_eta(self, remaining: int) -> float:
        """Estimate time remaining"""
        if not self.recent_times:
            return 0
        avg_recent = sum(self.recent_times) / len(self.recent_times)
        return avg_recent * remaining
    
    def print_progress(self, current: int, total: int):
        """Print progress with ETA"""
        remaining = total - current
        eta = self.get_eta(remaining)
        print(f"Progress: {current}/{total} ({current/total*100:.1f}%) - ETA: {eta:.1f}s")
```

### 13. Optimize Company Intelligence Scraping

**Current**: Sequential company scraping  
**Recommended**: Parallel batch processing

**Impact**: 5-10x faster company intelligence gathering  
**Risk**: Medium - requires rate limit management

**Implementation**:
```python
# In pipeline.py, modify company scraping:
async def scrape_companies_parallel(
    scraper: CompanyIntelligenceScraper,
    company_urls: List[str],
    batch_size: int = 10
):
    """Scrape companies in parallel batches"""
    results = []
    for i in range(0, len(company_urls), batch_size):
        batch = company_urls[i:i+batch_size]
        batch_results = await asyncio.gather(
            *[scraper.scrape_company(url) for url in batch],
            return_exceptions=True
        )
        results.extend(batch_results)
        await asyncio.sleep(1.0)  # Rate limit between batches
    return results
```

---

## 📈 Configuration Recommendations

### For Development/Testing
```python
# Fast, but may hit rate limits
SCRAPER_CONFIG = {
    "batch_size": 20,
    "rate_limit_delay": 1.0,
    "max_concurrent": 10,
}

PIPELINE_CONFIG = {
    "checkpoint_frequency": 25,
    "validate_sample_rate": 0.1,  # Validate 10%
    "batch_size": 1000,  # For Neo4j operations
}
```

### For Production
```python
# Balanced performance and reliability
SCRAPER_CONFIG = {
    "batch_size": 15,
    "rate_limit_delay": 1.5,
    "max_concurrent": 8,
}

PIPELINE_CONFIG = {
    "checkpoint_frequency": 20,
    "validate_sample_rate": 0.2,  # Validate 20%
    "batch_size": 500,  # For Neo4j operations
}
```

### For Maximum Speed (if rate limits allow)
```python
# Aggressive, use with caution
SCRAPER_CONFIG = {
    "batch_size": 30,
    "rate_limit_delay": 0.5,
    "max_concurrent": 20,
}

PIPELINE_CONFIG = {
    "checkpoint_frequency": 50,
    "validate_sample_rate": 0.05,  # Validate 5%
    "batch_size": 2000,  # For Neo4j operations
}
```

---

## 🛠️ Implementation Priority

### Phase 1: Quick Wins (1-2 hours)
1. ✅ Increase batch size to 20
2. ✅ Reduce rate limit delay to 1.0s
3. ✅ Optimize browser configuration
4. ✅ Increase checkpoint frequency

### Phase 2: Medium Optimizations (4-8 hours)
5. ✅ Batch database operations
6. ✅ Optimize file I/O (async)
7. ✅ Parallel company scraping
8. ✅ Implement progress tracking

### Phase 3: Advanced (1-2 days)
9. ✅ Parallel entity extraction
10. ✅ Request caching
11. ✅ Parallel post-processing
12. ✅ Optimize validation

---

## 📊 Expected Performance Improvements

| Optimization | Speed Improvement | Effort | Priority |
|-------------|------------------|--------|----------|
| Increase batch size | 2-3x faster | Low | High |
| Reduce rate limiting | 2x faster | Low | High |
| Optimize browser config | 1.3-1.5x faster | Low | High |
| Batch DB operations | 5-10x faster | Medium | High |
| Parallel extraction | 3-5x faster | High | Medium |
| Optimize file I/O | 1.1-1.2x faster | Medium | Medium |
| Parallel company scraping | 5-10x faster | Medium | Medium |
| Request caching | Variable | Low | Low |

**Total Expected Improvement**: 10-20x faster overall pipeline (with all optimizations)

---

## ⚠️ Important Considerations

### Rate Limiting
- TechCrunch may block aggressive scraping
- Start conservative and gradually increase
- Monitor for 429 (Too Many Requests) errors
- Implement exponential backoff on rate limit errors

### Resource Usage
- Increased parallelism = higher memory usage
- Monitor system resources (CPU, RAM, network)
- Adjust batch sizes based on available resources

### Data Quality
- Faster processing shouldn't compromise quality
- Keep validation at reasonable levels
- Monitor error rates

### OpenAI API Limits
- Batch processing increases API usage
- Monitor rate limits and costs
- Use OpenAI batch API for large-scale processing

---

## 🔍 Monitoring Performance

### Key Metrics to Track
1. **Scraping Speed**: Articles per minute
2. **Extraction Speed**: Articles per minute
3. **API Response Times**: OpenAI latency
4. **Database Performance**: Queries per second
5. **Memory Usage**: Peak memory consumption
6. **Error Rates**: Failed requests/scrapes

### Performance Logging
```python
# Add performance logging
import time
import logging

logger = logging.getLogger(__name__)

def log_performance(phase: str, duration: float, count: int):
    """Log performance metrics"""
    rate = count / duration if duration > 0 else 0
    logger.info(
        "performance_metric",
        phase=phase,
        duration=duration,
        count=count,
        rate=rate,
        unit="items/sec"
    )
```

---

## 🚨 Troubleshooting

### High Memory Usage
- Reduce batch sizes
- Process in smaller chunks
- Clear caches periodically

### Rate Limiting Issues
- Increase rate limit delays
- Reduce concurrent requests
- Use exponential backoff

### Slow Database Operations
- Check Neo4j connection pool size
- Verify indexes are created
- Use batch transactions
- Monitor query execution times

### API Timeouts
- Increase timeout values
- Reduce batch sizes
- Implement retry logic with backoff

---

## 📝 Example Optimized Configuration

```python
# scraper_config.py
SCRAPER_CONFIG = {
    "output_dir": "data/raw_data",
    "rate_limit_delay": 1.0,  # Optimized
    "max_pages": None,
    "batch_size": 20,  # Optimized
    "browser_config": {
        "headless": True,
        "viewport_width": 1280,  # Optimized
        "viewport_height": 720,  # Optimized
        "disable_images": True,  # Optimized
    },
    "timeout": 60000,  # 60 seconds
}

# pipeline_config.py
PIPELINE_CONFIG = {
    "checkpoint_frequency": 25,  # Optimized
    "validate_sample_rate": 0.1,  # Optimized
    "neo4j_batch_size": 1000,  # Optimized
    "extraction_batch_size": 5,  # For parallel extraction
    "company_scraping_batch_size": 10,  # Optimized
}
```

---

## 🎯 Next Steps

1. **Start with quick wins** (1-2 hours of work)
2. **Monitor performance** and measure improvements
3. **Gradually implement** medium-term optimizations
4. **Advanced optimizations** only if needed

Remember: Profile first, optimize second. Measure the impact of each change!

