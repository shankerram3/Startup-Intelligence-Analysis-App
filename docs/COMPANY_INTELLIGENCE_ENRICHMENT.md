# Company Intelligence Enrichment (Phase 1.5)

**NEW FEATURE**: Deep company intelligence extraction using Playwright to scrape company websites and enrich the knowledge graph with detailed information.

---

## 🎯 Overview

The Company Intelligence Enrichment phase (Phase 1.5) extends the pipeline to automatically:

1. **Extract company URLs** from article content
2. **Scrape company websites** using Playwright for detailed intelligence
3. **Aggregate multi-source data** from articles and websites
4. **Enrich Neo4j graph** with comprehensive company profiles

This transforms basic company mentions into rich, structured profiles with founding information, team details, funding data, products, and technologies.

---

## 🏗️ Pipeline Integration

### **New Pipeline Flow**

```
Phase 0: Web Scraping (TechCrunch articles)
    ↓
Phase 1: Entity Extraction (GPT-4o)
    ↓
Phase 1.5: Company Intelligence Enrichment (NEW!)  ← 🆕
    ├─ Step 1: Extract company URLs from articles
    ├─ Step 2: Scrape company websites with Playwright
    ├─ Step 3: Aggregate intelligence from all sources
    └─ Step 4: Save enriched company data
    ↓
Phase 2: Graph Construction
    ├─ Build knowledge graph
    └─ Phase 2.5: Enrich graph nodes with intelligence
    ↓
Phase 3: Graph Cleanup
    ↓
Phase 4: Post-Processing (embeddings, deduplication, communities)
```

---

## 🚀 Quick Start

### **1. Install Playwright**

```bash
# Install Python package
pip install playwright

# Install browser binaries
playwright install chromium
```

### **2. Run Pipeline with Enrichment**

```bash
# Full pipeline with enrichment (recommended)
python pipeline.py \
  --scrape-category startups \
  --scrape-max-pages 2 \
  --max-articles 10

# Enrichment runs automatically between extraction and graph building
```

### **3. Control Enrichment**

```bash
# Skip enrichment (old behavior)
python pipeline.py \
  --scrape-category startups \
  --max-articles 10 \
  --skip-enrichment

# Limit companies per article
python pipeline.py \
  --scrape-category startups \
  --max-articles 10 \
  --max-companies-per-article 5
```

---

## 📊 What Gets Enriched

### **Before Enrichment**

```json
{
  "name": "Anthropic",
  "type": "Company",
  "description": "AI safety company"
}
```

### **After Enrichment**

```json
{
  "name": "Anthropic",
  "type": "Company",
  "description": "AI safety company",
  "enriched_description": "Anthropic is an AI safety company building reliable, interpretable, and steerable AI systems...",
  "website_url": "https://www.anthropic.com",
  "founded_year": 2021,
  "employee_count": 150,
  "headquarters": "San Francisco, CA",
  "founders": ["Dario Amodei", "Daniela Amodei"],
  "executives": ["Dario Amodei - CEO", "Tom Brown - Chief Scientist"],
  "products": ["Claude", "Constitutional AI"],
  "technologies": ["AI", "machine learning", "Python", "PyTorch"],
  "funding_total": "$1.5B",
  "funding_stage": "Series B",
  "pricing_model": "freemium",
  "enrichment_status": "enriched",
  "enrichment_confidence": 0.92,
  "enrichment_timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 🔧 How It Works

### **Step 1: URL Extraction**

**File**: `utils/company_url_extractor.py`

- Parses article content for company website URLs
- Filters out social media, news sites, TechCrunch
- Matches URLs to company entities using:
  - Domain matching (e.g., "anthropic.com" → "Anthropic")
  - Proximity in text (URL near company mention)
  - Confidence scoring

### **Step 2: Website Scraping**

**File**: `scraper/company_intelligence_scraper.py`

Playwright scrapes multiple pages per company:

| Page Type | Paths Tried | Intelligence Extracted |
|-----------|-------------|------------------------|
| **Homepage** | `/` | Description, overview |
| **About** | `/about`, `/about-us`, `/company` | Founded year, employee count, HQ location |
| **Team** | `/team`, `/our-team`, `/people` | Founders, executives, roles |
| **News/Press** | `/press`, `/news`, `/newsroom`, `/blog` | Funding announcements, recent news |
| **Products** | `/products`, `/solutions` | Product offerings, technologies |
| **Pricing** | `/pricing` | Pricing model (free, freemium, enterprise) |

**Extraction Techniques**:
- Text parsing with regex patterns
- JavaScript execution to extract dynamic content
- Structured data from HTML elements
- Confidence scoring based on source quality

### **Step 3: Intelligence Aggregation**

**File**: `utils/company_intelligence_aggregator.py`

Merges data from multiple sources:

**Source Priority**:
1. **Website scrape** (0.8 confidence) - Most authoritative
2. **Article mention** (0.6 confidence) - Contextual
3. **Inferred** (0.3 confidence) - Derived data

**Conflict Resolution**:
- For simple fields: Prefer website data over article data
- For descriptions: Combine if complementary
- For lists: Merge and deduplicate
- Calculate field-level confidence scores

### **Step 4: Graph Enrichment**

**File**: `graph_builder.py` (new methods)

Updates Neo4j Company nodes with enriched data:
- `enrich_company_node()` - Enrich single company
- `enrich_all_companies()` - Batch enrich all companies

---

## 📁 Output Files

### **Directory Structure**

```
data/
├── articles/                    # Scraped TechCrunch articles
├── processing/
│   ├── all_extractions.json    # Entity extractions
│   ├── enriched_companies.json # Aggregated intelligence (NEW!)
│   └── company_intelligence/   # Individual scrape results (NEW!)
│       ├── Anthropic_abc123.json
│       ├── OpenAI_def456.json
│       └── ...
```

### **enriched_companies.json Structure**

```json
{
  "Anthropic": {
    "company_name": "Anthropic",
    "enrichment_timestamp": "2024-01-15T10:30:00Z",
    "sources": [
      {
        "type": "articles",
        "count": 3,
        "article_ids": ["abc123", "def456", "ghi789"]
      },
      {
        "type": "website_scrape",
        "url": "https://www.anthropic.com",
        "scraped_at": "2024-01-15T10:25:00Z"
      }
    ],
    "confidence_score": 0.92,
    "data": {
      "website_url": "https://www.anthropic.com",
      "founded_year": 2021,
      "employee_count": 150,
      ...
    },
    "field_confidence": {
      "website_url": 0.8,
      "founded_year": 0.8,
      "description": 0.8,
      ...
    }
  }
}
```

---

## 🎛️ Configuration Options

### **Command Line Flags**

| Flag | Description | Default |
|------|-------------|---------|
| `--skip-enrichment` | Skip Phase 1.5 entirely | `False` |
| `--max-companies-per-article` | Limit companies scraped per article | `None` (all) |

### **Environment Variables**

No additional environment variables required. Uses existing:
- `OPENAI_API_KEY` - For entity extraction
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` - For graph enrichment

### **Code Configuration**

In `pipeline.py` Phase 1.5:

```python
scraper = CompanyIntelligenceScraper(
    output_dir=str(intelligence_dir),
    rate_limit_delay=0.5,  # Delay between requests (seconds)
    timeout=30000,          # Page load timeout (ms)
    headless=True           # Run browser headlessly
)
```

---

## 📈 Performance & Stats

### **Example Output**

```
================================================================================
PHASE 1.5: COMPANY INTELLIGENCE ENRICHMENT
================================================================================

Processing 10 articles for company intelligence enrichment

1. Extracting company URLs from articles...
   ✓ Extracted 15 company URLs from 8 articles

2. Scraping company websites with Playwright...

   Article abc123:
   - Companies to scrape: 3
   ✓ Scraped 3 companies

   Article def456:
   - Companies to scrape: 2
   ✓ Scraped 2 companies

   ...

   ✓ Scraping complete:
     - Companies scraped: 12
     - Pages scraped: 48
     - Failed scrapes: 3

3. Aggregating company intelligence...

   ✓ Enrichment Summary:
     - Total companies: 15
     - With website URL: 12
     - With founded year: 8
     - With headquarters: 10
     - With founders: 6
     - With funding data: 4
     - Average confidence: 0.76
     - High confidence (>0.7): 9

✅ Company intelligence enrichment complete!
```

---

## 🎯 **Enriched Embeddings for Semantic Search**

### **How It Works**

The enrichment system **automatically integrates with vector embeddings** for superior semantic search:

#### **Embedding Generation Process**

1. **Phase 2.5**: After enriching company nodes in Neo4j, embeddings are **immediately regenerated** for enriched companies
2. **Phase 4**: All remaining entities get embeddings (including non-enriched ones)
3. **Result**: Enriched companies have embeddings based on comprehensive profiles, not just article mentions

#### **What Goes Into Enriched Embeddings**

For enriched companies, embeddings include:

```python
# Example embedding text for "Anthropic"
"Company: Anthropic. Anthropic is an AI safety company building reliable,
interpretable, and steerable AI systems. Located in San Francisco, CA.
Founded in 2021. Founded by Dario Amodei, Daniela Amodei. Products: Claude,
Constitutional AI. Technologies: AI, machine learning, Python, PyTorch, JAX.
Raised $1.5B in Series B."
```

vs. non-enriched companies:

```python
# Before enrichment
"Company: Anthropic. AI safety company."
```

### **Impact on Semantic Search**

Enriched embeddings make queries **significantly more powerful**:

| Query | Without Enrichment | With Enrichment |
|-------|-------------------|----------------|
| "AI companies in San Francisco" | ❌ No location data | ✅ Matches headquarters |
| "Companies founded after 2020" | ❌ No founding data | ✅ Matches founded_year |
| "Startups using PyTorch" | ❌ Limited tech mentions | ✅ Matches technology stack |
| "Series B companies" | ⚠️ Only if in article | ✅ Matches funding_stage |

### **Automatic Regeneration**

The pipeline **automatically regenerates** embeddings at the right time:

```
Phase 1.5: Scrape company intelligence
    ↓
Phase 2: Build knowledge graph
    ↓
Phase 2.5: Enrich company nodes ← Graph updated with enriched data
    ↓
    ✓ Regenerate embeddings for enriched companies ← AUTOMATIC!
    ↓
Phase 4: Post-processing
    ↓
    ✓ Generate embeddings for all other entities
```

**Result**: Your vector database contains rich, detailed company profiles for semantic search!

---

## 🔍 Querying Enriched Data

### **Cypher Queries**

```cypher
// Find companies with enriched data
MATCH (c:Company)
WHERE c.enrichment_status = 'enriched'
RETURN c.name, c.founded_year, c.headquarters, c.website_url

// Find companies founded after 2020
MATCH (c:Company)
WHERE c.founded_year > 2020
RETURN c.name, c.founded_year, c.founders

// Find companies by technology stack
MATCH (c:Company)
WHERE 'AI' IN c.technologies
RETURN c.name, c.technologies, c.products

// Get high-confidence enrichments
MATCH (c:Company)
WHERE c.enrichment_confidence > 0.7
RETURN c.name, c.enrichment_confidence, c.website_url
ORDER BY c.enrichment_confidence DESC
```

### **GraphRAG API - Powered by Enriched Embeddings**

The enriched fields are automatically available through the RAG API via **semantic search**:

```python
from rag_query import create_rag_query

rag = create_rag_query()

# Semantic search now uses enriched company profiles!
# These queries work because embeddings include enriched data:

# Query by location (uses headquarters from enriched data)
result = rag.query("Which AI companies are based in San Francisco?")
print(result['answer'])

# Query by founding year (uses founded_year from enriched data)
result = rag.query("What companies were founded after 2020?")
print(result['answer'])

# Query by technology stack (uses technologies from enriched data)
result = rag.query("Which startups use PyTorch for machine learning?")
print(result['answer'])

# Query by funding (uses funding_total and funding_stage from enriched data)
result = rag.query("Which Series B companies raised over $100M?")
print(result['answer'])

# Query by founders (uses founders from enriched data)
result = rag.query("What companies did Dario Amodei found?")
print(result['answer'])

# Complex multi-faceted queries
result = rag.query("AI companies in SF founded after 2020 with Series B funding")
print(result['answer'])
```

**How it works:**
1. Your query is embedded using the same sentence-transformers model
2. Semantic search finds companies with similar embeddings
3. Enriched companies match better because their embeddings include:
   - Detailed descriptions from websites
   - Location, founding year, team information
   - Products, technologies, funding details
4. LLM generates answer using enriched context

**Before enrichment**: Only article mentions available
**After enrichment**: Full company profiles in embeddings!

---

## 🐛 Troubleshooting

### **Playwright Not Installed**

```
⚠️  Enrichment not available: No module named 'playwright'
```

**Solution**:
```bash
pip install playwright
playwright install chromium
```

### **No Companies Scraped**

```
✓ Extracted 0 company URLs from 10 articles
```

**Possible Causes**:
- Articles don't contain company website URLs
- URLs were filtered out (social media, news sites)
- Company names don't match domains

**Solution**: Check article content manually, adjust filtering in `company_url_extractor.py`

### **Scraping Failures**

```
✗ Failed to scrape companies for article abc123: Timeout
```

**Possible Causes**:
- Website timeout (slow loading)
- Website blocking automated access
- Network issues

**Solution**:
- Increase timeout in configuration
- Add delays between requests
- Check website accessibility manually

### **Low Confidence Scores**

```
Average confidence: 0.35
```

**Possible Causes**:
- Limited data on company websites
- URLs not matching company names well
- No website data, only article mentions

**Solution**: Normal for some companies. Focus on high-confidence enrichments.

---

## 🎯 Best Practices

### **1. Start Small**

```bash
# Test with a few articles first
python pipeline.py \
  --scrape-category startups \
  --max-articles 5 \
  --max-companies-per-article 3
```

### **2. Monitor Progress**

Watch the console output to see:
- URL extraction success rate
- Scraping progress per article
- Confidence scores
- Failed scrapes

### **3. Respect Rate Limits**

- Default delay: 0.5 seconds between requests
- Increase if getting blocked: `rate_limit_delay=2.0`
- Use `max-companies-per-article` to limit scraping

### **4. Review Enriched Data**

```bash
# Check enriched companies file
cat data/processing/enriched_companies.json | jq '.'

# Check individual scrapes
ls data/processing/company_intelligence/
```

### **5. Query Validation**

After enrichment, validate in Neo4j Browser:

```cypher
MATCH (c:Company)
RETURN c.name, c.enrichment_status, c.enrichment_confidence
ORDER BY c.enrichment_confidence DESC
LIMIT 10
```

---

## 🚧 Limitations

1. **URL Detection**: Only finds URLs explicitly mentioned in articles
2. **Website Structure**: Relies on common page layouts (About, Team, etc.)
3. **Dynamic Content**: Some JavaScript-heavy sites may not fully render
4. **Rate Limiting**: Aggressive scraping may trigger blocking
5. **Data Quality**: Extracted data depends on website structure and content

---

## 🔮 Future Enhancements

- [ ] Crunchbase API integration for additional data
- [ ] LinkedIn company page scraping
- [ ] GitHub organization scraping for tech stack
- [ ] Funding round details from PitchBook
- [ ] Employee count from LinkedIn
- [ ] Real-time data refresh
- [ ] Confidence threshold filtering
- [ ] Manual URL override support

---

## 📚 Related Documentation

- **[Pipeline Architecture](development/ARCHITECTURE.md)** - Overall system design
- **[API Documentation](api/RAG_DOCUMENTATION.md)** - Query API usage
<!-- Azure deployment link removed -->

---

**Built with:** Python, Playwright, BeautifulSoup, Neo4j

**Happy Intelligence Gathering! 🚀**
