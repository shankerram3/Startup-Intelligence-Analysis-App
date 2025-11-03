# TechCrunch Knowledge Graph Pipeline

A comprehensive pipeline for building and querying a knowledge graph from TechCrunch articles. This system extracts entities, relationships, and metadata from articles using LLM-based extraction, stores them in Neo4j, and provides advanced analytics capabilities.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
- [Pipeline Components](#pipeline-components)
- [Utilities and Features](#utilities-and-features)
- [Data Validation](#data-validation)
- [Graph Management](#graph-management)
- [Advanced Features](#advanced-features)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)
- [Appendix](#appendix)

---

## 🎯 Overview

This pipeline transforms TechCrunch articles into a structured knowledge graph by:

1. **Web Scraping** (Phase 0): Extracts articles from TechCrunch category pages
2. **Entity Extraction** (Phase 1): Uses LLM (GPT-4o) to identify entities and relationships
3. **Graph Construction** (Phase 2): Builds a Neo4j knowledge graph with nodes and relationships
4. **Post-Processing** (Phase 3): Enhances and cleans the graph with deduplication, validation, and analytics

### Key Capabilities

- ✅ **End-to-End Pipeline**: From scraping to queryable graph
- ✅ **LLM-Based Extraction**: Accurate entity and relationship identification
- ✅ **Graph Database**: Neo4j for efficient querying and relationships
- ✅ **Data Quality**: Multi-layer validation and filtering
- ✅ **Incremental Updates**: Resume capability and checkpoint management
- ✅ **Advanced Analytics**: Temporal analysis, community detection, embeddings

---

## ✨ Features

### Core Pipeline
- ✅ **Web Scraping**: Automated article extraction from TechCrunch
- ✅ **Entity Extraction**: LLM-based extraction of entities and relationships
- ✅ **Graph Building**: Neo4j knowledge graph construction
- ✅ **Pipeline Orchestration**: Complete end-to-end automation

### Data Quality
- ✅ **Multi-Layer Validation**: Article and extraction validation
- ✅ **Entity Deduplication**: Automatic merging of duplicate entities
- ✅ **Enhanced Validation**: Funding amounts, dates, entity names
- ✅ **Quality Filtering**: Prevents unwanted nodes (TechCrunch/Disrupt, MENTIONED_IN)

### Advanced Features
- ✅ **Entity Resolution**: Fuzzy matching and deduplication
- ✅ **Relationship Scoring**: Frequency, recency, credibility-based scoring
- ✅ **Temporal Analysis**: Timeline tracking and trend analysis
- ✅ **Community Detection**: Graph-based community identification
- ✅ **Embedding Generation**: Vector embeddings for semantic search
- ✅ **Entity Classification**: Confidence scores and type refinement
- ✅ **Coreference Resolution**: Pronoun and reference resolution

---

## 🏗️ Architecture

### Pipeline Flow

```
TechCrunch Articles
    ↓
[Phase 0: Web Scraping]
    ↓
Raw Article JSON Files
    ↓
[Phase 1: Entity Extraction]
    ↓
Extracted Entities & Relationships (JSON)
    ↓
[Phase 2: Graph Construction]
    ↓
Neo4j Knowledge Graph
    ↓
[Phase 3: Post-Processing]
    ↓
Enhanced & Cleaned Graph
```

### Component Structure

```
SWM Project/
├── pipeline.py              # Main pipeline orchestrator
├── entity_extractor.py      # LLM-based entity extraction
├── graph_builder.py         # Neo4j graph construction
├── scraper/                 # Web scraping module
│   ├── techcrunch_scraper.py
│   ├── run_scraper.py
│   ├── scraper_config.py
│   └── demo_scraper.py
├── utils/                   # Utility modules
│   ├── data_validation.py   # Validation utilities
│   ├── checkpoint.py        # Resume capability
│   ├── retry.py             # Retry logic
│   ├── entity_normalization.py
│   ├── entity_resolver.py   # Deduplication
│   ├── relationship_scorer.py
│   ├── temporal_analyzer.py
│   ├── entity_classifier.py
│   ├── coreference_resolver.py
│   ├── community_detector.py
│   ├── embedding_generator.py
│   ├── graph_cleanup.py
│   ├── filter_techcrunch.py
│   ├── enhanced_validation.py
│   └── progress_tracker.py
├── data/
│   ├── articles/            # Scraped articles (organized by date)
│   └── processing/          # Extractions & checkpoints
├── cypher queries/          # Query examples
│   └── neo4j_queries.cypher
├── integrate_new_features.py  # Feature integration script
├── delete_techcrunch.py       # Remove TechCrunch nodes
└── requirements.txt          # Python dependencies
```

---

## 🚀 Installation

### Prerequisites

- **Python**: 3.11 or higher
- **Neo4j**: 5.x (running locally or remotely)
- **OpenAI API**: API key for entity extraction
- **Crawl4AI**: For web scraping (browser setup required)

### Step 1: Install Dependencies

```bash
# Navigate to project directory
cd "SWM Project"

# Install all dependencies
pip install -r requirements.txt --break-system-packages

# Setup Crawl4AI browser (required for scraping)
crawl4ai-setup
```

### Step 2: Configure Environment

Create a `.env` file in the project root:

```bash
# OpenAI API Key (required for entity extraction)
OPENAI_API_KEY=your-openai-api-key-here

# Neo4j Connection (required for graph building)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password-here
```

### Step 3: Start Neo4j

**Option A: Docker (Recommended)**
```bash
docker run -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  -v neo4j_data:/data \
  neo4j:latest
```

**Option B: Neo4j Desktop**
- Download from https://neo4j.com/download/
- Create a new database
- Note the connection URI and credentials

### Step 4: Verify Installation

```bash
# Test Neo4j connection
python -c "from neo4j import GraphDatabase; \
  driver = GraphDatabase.driver('bolt://localhost:7687', \
  auth=('neo4j', 'your-password')); \
  driver.verify_connectivity(); \
  print('✅ Neo4j connected!')"

# Test OpenAI API
python -c "from openai import OpenAI; \
  import os; \
  from dotenv import load_dotenv; \
  load_dotenv(); \
  client = OpenAI(api_key=os.getenv('OPENAI_API_KEY')); \
  print('✅ OpenAI API configured!')"
```

---

## 🎬 Quick Start

### 1. Run Complete Pipeline (Small Test)

```bash
# Scrape articles, extract entities, build graph (10 articles)
python pipeline.py \
  --scrape-category startups \
  --scrape-max-pages 2 \
  --max-articles 10
```

### 2. Explore Your Graph

```bash
# Open Neo4j Browser
# URL: http://localhost:7474
# Default login: neo4j / your-password

# Run queries from:
# cypher queries/neo4j_queries.cypher
```

### 3. Run Full Pipeline (Production)

```bash
# Process all articles from a category
python pipeline.py \
  --scrape-category ai \
  --scrape-max-pages 10
```

---

## 📖 Usage Guide

### Pipeline Command-Line Options

```bash
python pipeline.py [options]

Options:
  --articles-dir PATH       Path to scraped articles
                           (default: data/articles)
  
  --output-dir PATH         Path for extracted entities
                           (default: data/processing)
  
  --max-articles N          Limit to N articles (default: all)
  
  --skip-scraping           Skip web scraping phase
  --skip-extraction         Skip entity extraction phase
  --skip-graph              Skip graph construction phase
  
  --scrape-category NAME    Category to scrape (e.g., 'startups', 'ai')
                           Required to enable scraping
  
  --scrape-max-pages N      Maximum pages to scrape (default: unlimited)
  
  --no-resume               Don't resume from checkpoint (start fresh)
  --no-validation          Skip data validation
  --no-cleanup              Skip graph post-processing cleanup
  
  --help-extended           Show extended help with examples
```

### Common Usage Patterns

#### 1. Full Pipeline (Test Run)
```bash
# Scrape 2 pages, extract from 10 articles, build graph
python pipeline.py \
  --scrape-category startups \
  --scrape-max-pages 2 \
  --max-articles 10
```

#### 2. Full Pipeline (Production)
```bash
# Scrape all pages from AI category
python pipeline.py \
  --scrape-category ai \
  --scrape-max-pages 10
```

#### 3. Incremental Update (Resume)
```bash
# Automatically resumes from last checkpoint
python pipeline.py \
  --scrape-category startups \
  --scrape-max-pages 5
```

#### 4. Skip Scraping (Use Existing Articles)
```bash
# Extract entities from existing articles
python pipeline.py \
  --skip-scraping \
  --max-articles 50
```

#### 5. Only Build Graph (Use Existing Extractions)
```bash
# Build graph from existing extractions file
python pipeline.py \
  --skip-scraping \
  --skip-extraction
```

#### 6. Start Fresh (No Resume)
```bash
# Clear checkpoint and start over
python pipeline.py \
  --no-resume \
  --scrape-category startups \
  --scrape-max-pages 3
```

### Standalone Scripts

#### Run Scraper Directly
```bash
cd scraper
python run_scraper.py --category startups --max-pages 3

# See demo (no network required)
python demo_scraper.py
```

#### Build Graph Directly
```bash
python -m graph_builder
```

#### Integrate New Features
```bash
python integrate_new_features.py
```

#### Cleanup Scripts
```bash
# Delete TechCrunch/Disrupt nodes
python delete_techcrunch.py --confirm

# Cleanup MENTIONED_IN relationships (using utils)
python -m utils.graph_cleanup
```

---

## 🔧 Pipeline Components

### Phase 0: Web Scraping

**File**: `scraper/techcrunch_scraper.py`

**What It Does:**
- Discovers articles from TechCrunch category pages
- Extracts full article content (headline, paragraphs)
- Handles pagination automatically
- Implements rate limiting for respectful scraping

**Features:**
- Two-phase architecture (discovery → extraction)
- Pagination handling (follows "Next" buttons)
- Rate limiting (3 seconds between pages, 6 seconds between batches)
- Concurrent batch processing (default: 10 concurrent)
- Error handling with retries
- Progress tracking with checkpoints

**Available Categories:**
- `startups` - Startup news and funding
- `ai` - Artificial Intelligence
- `apps` - Mobile and web applications
- `enterprise` - Enterprise technology
- `fintech` - Financial technology
- `venture` - Venture capital

**Output:**
- Articles saved to `data/articles/YYYY-MM/DD/tc_articleid.json`
- Metadata in `data/articles/metadata/`

**Article Format:**
```json
{
  "article_id": "abc123hash",
  "url": "https://techcrunch.com/2025/10/31/article-slug/",
  "title": "Article Title",
  "author": "Author Name",
  "published_date": "2025-10-31T13:14:06-07:00",
  "categories": ["Startups", "AI"],
  "content": {
    "headline": "Article Headline",
    "body_text": "Full article text...",
    "paragraphs": ["Paragraph 1", "Paragraph 2"],
    "word_count": 450
  },
  "metadata": {
    "scraped_at": "2025-11-02T10:35:22",
    "extraction_method": "css",
    "source_page": 1
  }
}
```

### Phase 1: Entity Extraction

**File**: `entity_extractor.py`

**What It Does:**
- Uses GPT-4o to extract entities and relationships from article text
- Applies entity normalization to reduce duplicates
- Validates extractions before saving
- Saves checkpoints for resume capability

**Entity Types Extracted:**
- `Company` - Companies and organizations
- `Person` - People and individuals
- `Investor` - Investment firms and investors
- `Technology` - Technologies and frameworks
- `Product` - Products and services
- `FundingRound` - Funding rounds
- `Location` - Geographic locations
- `Event` - Events and conferences

**Relationship Types Extracted:**
- `FUNDED_BY` - Company funded by investor
- `FOUNDED_BY` - Company founded by person
- `WORKS_AT` - Person works at company
- `ACQUIRED` - Company acquired another
- `PARTNERS_WITH` - Company partners with company
- `COMPETES_WITH` - Company competes with company
- `USES_TECHNOLOGY` - Entity uses technology
- `LOCATED_IN` - Entity located in location
- `ANNOUNCED_AT` - Announcement at event

**Note**: `MENTIONED_IN` relationships are **NOT** created. Entity-to-article relationships are handled via properties (`source_articles`, `article_count`).

**Output:**
- Extractions saved to `data/processing/extraction_articleid.json`
- All extractions merged to `data/processing/all_extractions.json`
- Checkpoint file: `data/processing/extraction_checkpoint.json`
- Progress report: `data/processing/extraction_progress.json`

**Extraction Format:**
```json
{
  "article_metadata": {
    "url": "https://techcrunch.com/...",
    "title": "Article Title",
    "published_date": "2025-10-31T...",
    "article_id": "abc123"
  },
  "entities": [
    {
      "name": "OpenAI",
      "type": "company",
      "description": "AI company...",
      "normalized_name": "OPENAI"
    }
  ],
  "relationships": [
    {
      "source": "OpenAI",
      "target": "Microsoft",
      "type": "PARTNERS_WITH",
      "description": "OpenAI partners with Microsoft",
      "strength": 10
    }
  ],
  "extraction_timestamp": "2025-11-02T10:40:00"
}
```

### Phase 2: Graph Construction

**File**: `graph_builder.py`

**What It Does:**
- Initializes Neo4j schema (constraints, indexes)
- Creates article nodes
- Creates entity nodes (with deduplication via hash-based IDs)
- Creates relationships between entities
- Links entities to articles via properties (not relationships)

**Graph Structure:**

**Nodes:**
- `Article` - TechCrunch articles
- `Company` - Companies and organizations
- `Person` - People and individuals
- `Investor` - Investment firms
- `Technology` - Technologies and frameworks
- `Product` - Products and services
- `FundingRound` - Funding rounds
- `Location` - Geographic locations
- `Event` - Events and conferences

**Relationships:**
- `FUNDED_BY` - Company → Investor
- `FOUNDED_BY` - Company → Person
- `WORKS_AT` - Person → Company
- `ACQUIRED` - Company → Company
- `PARTNERS_WITH` - Entity ↔ Entity
- `COMPETES_WITH` - Company ↔ Company
- `USES_TECHNOLOGY` - Entity → Technology
- `LOCATED_IN` - Entity → Location
- `ANNOUNCED_AT` - Entity → Event

**Node Properties:**
- `id` - Unique entity ID (hash-based)
- `name` - Entity name
- `description` - Entity description
- `source_articles` - List of article IDs mentioning entity
- `article_count` - Number of articles
- `mention_count` - Number of mentions
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

**Relationship Properties:**
- `type` - Relationship type
- `description` - Relationship description
- `strength` - Relationship strength (0-10)
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

### Phase 3: Post-Processing

**Optional cleanup and enhancement phase.**

**Automatically Runs:**
- Graph cleanup (converts MENTIONED_IN relationships to properties)
- Graph statistics

**Can Be Manually Run:**
- Entity deduplication
- Relationship strength calculation
- Community detection
- Embedding generation
- Temporal analysis setup

---

## 🛠️ Utilities and Features

### 1. Entity Resolution & Deduplication

**File**: `utils/entity_resolver.py`

Finds and merges duplicate entities using fuzzy string matching.

**Features:**
- Fuzzy matching for duplicate detection (Levenshtein distance)
- Automatic merging of duplicate nodes in Neo4j
- Preserves all relationships and properties
- Canonical name selection

**Usage:**
```python
from neo4j import GraphDatabase
from utils.entity_resolver import EntityResolver

driver = GraphDatabase.driver(uri, auth=(user, password))
resolver = EntityResolver(driver)

# Find and merge duplicates (dry run)
stats = resolver.merge_all_duplicates(threshold=0.85, dry_run=True)

# Actually merge duplicates
stats = resolver.merge_all_duplicates(threshold=0.85, dry_run=False)
```

**Integration:**
```bash
python integrate_new_features.py
```

### 2. Enhanced Data Validation

**File**: `utils/enhanced_validation.py`

Validates funding amounts, dates, entity names, and cross-references entities.

**Features:**
- Funding amount validation (`$50M`, `$50 million`, etc.)
- Date format validation (ISO, various formats)
- Entity name format validation
- Cross-referencing against known entities

**Usage:**
```python
from utils.enhanced_validation import (
    validate_funding_amount,
    validate_date_format,
    validate_entity_name_format,
    validate_funding_round
)

# Validate funding amount
is_valid, normalized = validate_funding_amount("$50M")
# Returns: (True, "$50.00M")

# Validate date
is_valid, normalized = validate_date_format("2025-10-31")
# Returns: (True, "2025-10-31")

# Validate entity name
is_valid, error = validate_entity_name_format("OpenAI")
# Returns: (True, None)
```

### 3. Relationship Strength Calculation

**File**: `utils/relationship_scorer.py`

Calculates relationship strength based on multiple factors.

**Factors:**
- **Frequency** (30%): How many times mentioned
- **Recency** (20%): When last mentioned
- **Credibility** (30%): Direct quote vs inference
- **Context** (20%): Main topic vs passing mention

**Usage:**
```python
from utils.relationship_scorer import RelationshipScorer

scorer = RelationshipScorer(driver)

# Calculate strength for a relationship
strength = scorer.calculate_strength(relationship, article_metadata)

# Update all relationship strengths in graph
stats = scorer.update_relationship_strengths()
```

**Integration:**
```bash
python integrate_new_features.py
```

### 4. Temporal Analysis

**File**: `utils/temporal_analyzer.py`

Tracks relationship timelines and analyzes trends over time.

**Features:**
- Relationship timeline tracking
- Funding trends over time
- Sector funding analysis
- Leadership change detection
- Time-range queries

**Usage:**
```python
from utils.temporal_analyzer import TemporalAnalyzer

temporal = TemporalAnalyzer(driver)

# Track funding trends for a company
trends = temporal.track_funding_trends(
    company_name="OpenAI",
    start_date="2024-01-01",
    end_date="2025-10-31"
)

# Find relationship timeline between two entities
timeline = temporal.find_relationship_timeline("OpenAI", "Microsoft")

# Get funding trends by sector
sector_trends = temporal.get_funding_trends_by_sector("AI", months=6)

# Find leadership changes
changes = temporal.find_leadership_changes("OpenAI")
```

### 5. Entity Type Classification Refinement

**File**: `utils/entity_classifier.py`

Refines entity type classification with confidence scores.

**Features:**
- Confidence scores for entity types
- Multi-signal classification (name, description, context)
- Investor subtype classification (VC, Angel, Corporate)
- Entity disambiguation (e.g., "Ford" = company vs person)

**Usage:**
```python
from utils.entity_classifier import EntityClassifier

classifier = EntityClassifier()

# Refine classification
entity_type, confidence = classifier.refine_classification(entity, context)

# Classify investor subtype
subtype = classifier.classify_investor_subtype(investor)

# Disambiguate entity using co-occurring entities
entity_type, confidence = classifier.disambiguate_entity(
    entity, co_occurring_entities
)
```

### 6. Coreference Resolution

**File**: `utils/coreference_resolver.py`

Resolves pronouns and references in text to improve extraction.

**Features:**
- Pronoun resolution ("he", "she", "they", "it")
- Reference resolution ("the company", "the startup")
- Context-aware resolution using previous sentences
- Text enhancement for better extraction

**Usage:**
```python
from utils.coreference_resolver import CoreferenceResolver

resolver = CoreferenceResolver()

# Resolve references in text
resolved_text = resolver.resolve_references(text, entities)

# Enhance text for extraction
enhanced_text = resolver.enhance_text_for_extraction(text, entities)
```

### 7. Community Detection

**File**: `utils/community_detector.py`

Detects communities of related entities using graph algorithms.

**Features:**
- Leiden algorithm (via Neo4j GDS)
- Louvain algorithm
- Label Propagation algorithm
- Simple connected components (fallback if GDS not available)

**Usage:**
```python
from utils.community_detector import CommunityDetector

detector = CommunityDetector(driver)

# Detect communities
communities = detector.detect_communities(
    algorithm="leiden",  # or "louvain", "label_propagation"
    min_community_size=3
)

# Get community summary
summary = detector.get_community_summary(community_id=1)

# Find related communities
related = detector.find_related_communities("OpenAI")
```

**Note**: Requires Neo4j Graph Data Science (GDS) plugin for advanced algorithms. Falls back to simple connected components if GDS is not available.

### 8. Embedding Generation

**File**: `utils/embedding_generator.py`

Generates vector embeddings for entities to enable semantic search.

**Features:**
- OpenAI embeddings support
- Sentence Transformers support
- Entity embedding generation
- Semantic similarity search

**Usage:**
```python
from utils.embedding_generator import EmbeddingGenerator

generator = EmbeddingGenerator(driver, embedding_model="openai")

# Generate embeddings for all entities
stats = generator.generate_embeddings_for_all_entities()

# Find similar entities
similar = generator.find_similar_entities("AI startup", limit=10)
```

**Requirements:**
- OpenAI: `pip install openai` + API key
- Sentence Transformers: `pip install sentence-transformers`

---

## ✅ Data Validation

### Validation Layers

The pipeline has **multiple validation layers**:

#### 1. Article Validation (`utils/data_validation.py`)
- Validates article structure
- Checks required fields (headline, paragraphs, metadata)
- Verifies content length (minimum 100 chars)
- Validates date formats

#### 2. Extraction Validation (`utils/data_validation.py`)
- Validates entity structure and types
- Validates relationship structure and types
- Checks required fields
- Validates value ranges (strength 0-10)
- Filters TechCrunch/Disrupt entities
- Filters MENTIONED_IN relationships

#### 3. Enhanced Validation (`utils/enhanced_validation.py`)
- Validates funding amounts (`$50M`, `$50 million`, etc.)
- Validates date formats (ISO, various formats)
- Validates entity name formats
- Cross-references against known entities

### Validation Examples

```python
from utils.data_validation import validate_article, validate_extraction
from utils.enhanced_validation import validate_funding_amount

# Validate article
is_valid, error = validate_article(article_data)
if not is_valid:
    print(f"Invalid article: {error}")

# Validate extraction
is_valid, errors = validate_extraction(extraction)
if not is_valid:
    print(f"Validation errors: {errors}")

# Validate funding amount
is_valid, normalized = validate_funding_amount("$50M")
if is_valid:
    print(f"Normalized: {normalized}")
```

---

## 🧹 Graph Management

### Automatic Cleanup

The pipeline automatically:
- Converts `MENTIONED_IN` relationships to properties
- Filters out TechCrunch/Disrupt nodes
- Shows graph statistics

### Manual Cleanup

```bash
# Delete TechCrunch/Disrupt nodes
python delete_techcrunch.py --confirm

# Cleanup MENTIONED_IN relationships
python -m utils.graph_cleanup

# Check for remaining issues
# Run queries from: check_mentioned_in.cypher
# Run queries from: check_techcrunch.cypher
```

### Graph Queries

See `cypher queries/neo4j_queries.cypher` for example queries:

```cypher
// Get statistics
MATCH (n)
RETURN labels(n)[0] as type, count(n) as count
ORDER BY count DESC;

// Find most connected companies
MATCH (c:Company)-[r]-()
RETURN c.name, count(r) as connections
ORDER BY connections DESC
LIMIT 10;

// Find funding relationships
MATCH (c:Company)-[r:FUNDED_BY]->(i:Investor)
RETURN c.name as company, i.name as investor, r.strength as strength
ORDER BY r.strength DESC
LIMIT 20;

// Find entities in a specific article
MATCH (e)
WHERE 'article_id' IN e.source_articles
RETURN e.name, labels(e)[0] as type
LIMIT 20;
```

---

## 🔒 Protection Mechanisms

### Preventing MENTIONED_IN Relationships

The pipeline has **5 layers of protection** to prevent `MENTIONED_IN` relationships:

1. **Prompt Filter**: LLM prompt explicitly excludes MENTIONED_IN
2. **Parse Filter**: Filters during parsing
3. **Validation Filter**: Validation rejects MENTIONED_IN
4. **Ingestion Filter**: Filters during graph ingestion
5. **Creation Guard**: Blocks creation in `create_relationship()`

### Preventing TechCrunch/Disrupt Nodes

The pipeline has **8 layers of protection** to prevent TechCrunch/Disrupt nodes:

1. **Parse-time Entity Filtering**: Filters entities during parsing
2. **Post-parse Filtering**: Additional check after parsing
3. **Parse-time Relationship Filtering**: Filters relationships
4. **Data Validation**: Validation rejects TechCrunch/Disrupt entities
5. **Ingestion Entity Filtering**: Filters before node creation
6. **Entity Creation Guard**: Blocks creation in `create_entity_node()`
7. **Ingestion Relationship Filtering**: Filters relationships
8. **Relationship Creation Guard**: Blocks relationship creation

**All layers are automatic** - you'll see warnings if filters catch unwanted entities.

---

## 📊 Advanced Features Integration

### Run All Advanced Features

```bash
python integrate_new_features.py
```

This runs:
1. Entity deduplication (merges duplicates)
2. Relationship strength updates
3. Community detection
4. Embedding generation (if API key available)

### Individual Feature Usage

See [Utilities and Features](#🛠️-utilities-and-features) section above for detailed usage examples.

---

## ⚙️ Configuration

### Environment Variables

Required in `.env` file:

```bash
# OpenAI API (required for entity extraction)
OPENAI_API_KEY=your-openai-api-key

# Neo4j Connection (required for graph building)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
```

### Scraper Configuration

Edit `scraper/scraper_config.py`:

```python
SCRAPER_CONFIG = {
    "output_dir": "data/articles",
    "rate_limit_delay": 3.0,  # Seconds between page requests
    "max_pages": None,        # None = unlimited
    "batch_size": 10,         # Concurrent article extractions
}
```

### Entity Extraction Configuration

Edit `entity_extractor.py`:

```python
# LLM model
model = "gpt-4o"  # or "gpt-4", "gpt-3.5-turbo"

# Temperature (0.0 = deterministic)
temperature = 0.0
```

### Graph Builder Configuration

Edit `graph_builder.py`:

```python
# Relationship strength default
default_strength = 5  # 0-10 scale
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Neo4j Connection Error

**Error**: `Failed to establish connection`

**Solution**:
```bash
# Check Neo4j is running
docker ps | grep neo4j

# Test connection
python -c "from neo4j import GraphDatabase; \
  driver = GraphDatabase.driver('bolt://localhost:7687', \
  auth=('neo4j', 'your-password')); \
  driver.verify_connectivity(); \
  print('✅ Connected!')"
```

#### 2. OpenAI API Error

**Error**: `Invalid API key` or `Rate limit exceeded`

**Solution**:
```bash
# Check .env file
cat .env | grep OPENAI_API_KEY

# Verify API key
export OPENAI_API_KEY=your-key
python -c "from openai import OpenAI; \
  import os; \
  client = OpenAI(api_key=os.getenv('OPENAI_API_KEY')); \
  print('✅ API key valid!')"
```

#### 3. Scraping Fails

**Error**: `Browser not installed` or `Rate limited (429)`

**Solution**:
```bash
# Install browser
crawl4ai-setup

# Increase rate limit delay
# Edit scraper/scraper_config.py
rate_limit_delay = 5.0  # Increase from 3.0

# Reduce batch size
batch_size = 5  # Reduce from 10
```

#### 4. Graph Building Slow

**Issue**: Graph building takes too long

**Solution**:
- Indexes are created automatically
- Process in smaller batches (use `--max-articles`)
- Check Neo4j memory settings
- Use Neo4j on faster hardware

#### 5. Duplicate Entities

**Issue**: Same entity appears multiple times (e.g., "OpenAI" and "Open AI")

**Solution**:
```bash
# Run entity deduplication
python integrate_new_features.py
```

#### 6. MENTIONED_IN Relationships Still Appearing

**Issue**: Despite filters, some MENTIONED_IN relationships exist

**Solution**:
```bash
# Cleanup MENTIONED_IN relationships
python -m utils.graph_cleanup
```

#### 7. TechCrunch/Disrupt Nodes Still Appearing

**Issue**: Some TechCrunch/Disrupt nodes exist in graph

**Solution**:
```bash
# Delete all TechCrunch/Disrupt nodes
python delete_techcrunch.py --confirm
```

---

## 📈 Performance Tips

1. **Batch Processing**: Process articles in batches (checkpoint every 10 articles)
2. **Resume Capability**: Use checkpoint system to resume from failures
3. **Parallel Extraction**: Increase `batch_size` in scraper config (carefully)
4. **Graph Indexes**: Indexes are created automatically for performance
5. **Incremental Updates**: Resume from checkpoint for new articles

### Typical Performance

- **Scraping**: ~15-20 articles/page, 3-5 seconds/page
- **Extraction**: ~2-3 seconds/article (depends on LLM API)
- **Graph Building**: ~0.5-1 second/article
- **Post-Processing**: Varies by feature

---

## 🎯 Next Steps

### Recommended Workflow

1. **Test Pipeline** (5-10 articles)
   ```bash
   python pipeline.py --scrape-category startups --scrape-max-pages 1 --max-articles 5
   ```

2. **Explore Graph**
   - Open Neo4j Browser: http://localhost:7474
   - Run queries from `cypher queries/neo4j_queries.cypher`

3. **Run Full Pipeline** (larger dataset)
   ```bash
   python pipeline.py --scrape-category ai --scrape-max-pages 10
   ```

4. **Integrate Features**
   ```bash
   python integrate_new_features.py
   ```

5. **Build Graph RAG** (Phase 4)
   - Implement query interface
   - Add question-to-Cypher conversion
   - Generate natural language answers

### Future Enhancements

- [ ] Graph RAG implementation
- [ ] Web interface for queries
- [ ] Real-time article updates
- [ ] Multi-source support (other news sites)
- [ ] Advanced analytics dashboard

---

## 📚 Appendix

### Entity Types

| Type | Description | Example |
|------|-------------|---------|
| `Company` | Companies and organizations | "OpenAI", "Microsoft" |
| `Person` | People and individuals | "Sam Altman", "Satya Nadella" |
| `Investor` | Investment firms | "Sequoia Capital", "Andreessen Horowitz" |
| `Technology` | Technologies and frameworks | "GPT-4", "Machine Learning" |
| `Product` | Products and services | "ChatGPT", "Copilot" |
| `FundingRound` | Funding rounds | "Series A", "Seed Round" |
| `Location` | Geographic locations | "San Francisco", "Silicon Valley" |
| `Event` | Events and conferences | "TechCrunch Disrupt", "WWDC" |

**Note**: TechCrunch/Disrupt events are filtered out automatically.

### Relationship Types

| Type | Description | Example |
|------|-------------|---------|
| `FUNDED_BY` | Company funded by investor | OpenAI → Sequoia Capital |
| `FOUNDED_BY` | Company founded by person | OpenAI → Sam Altman |
| `WORKS_AT` | Person works at company | Sam Altman → OpenAI |
| `ACQUIRED` | Company acquired another | Microsoft → GitHub |
| `PARTNERS_WITH` | Company partners with company | OpenAI → Microsoft |
| `COMPETES_WITH` | Company competes with company | OpenAI ↔ Anthropic |
| `USES_TECHNOLOGY` | Entity uses technology | OpenAI → GPT-4 |
| `LOCATED_IN` | Entity located in location | OpenAI → San Francisco |
| `ANNOUNCED_AT` | Announcement at event | OpenAI → TechCrunch Disrupt |

**Note**: `MENTIONED_IN` relationships are **NOT** created. Entity-to-article relationships use properties instead.

### File Formats

#### Article JSON
```json
{
  "article_id": "abc123hash",
  "url": "https://techcrunch.com/...",
  "title": "Article Title",
  "author": "Author Name",
  "published_date": "2025-10-31T13:14:06-07:00",
  "categories": ["Startups", "AI"],
  "content": {
    "headline": "Article Headline",
    "body_text": "Full article text...",
    "paragraphs": ["Paragraph 1", "Paragraph 2"],
    "word_count": 450
  },
  "metadata": {
    "scraped_at": "2025-11-02T10:35:22",
    "extraction_method": "css",
    "source_page": 1
  }
}
```

#### Extraction JSON
```json
{
  "article_metadata": {
    "url": "https://techcrunch.com/...",
    "title": "Article Title",
    "published_date": "2025-10-31T...",
    "article_id": "abc123"
  },
  "entities": [
    {
      "name": "OpenAI",
      "type": "company",
      "description": "AI company...",
      "normalized_name": "OPENAI"
    }
  ],
  "relationships": [
    {
      "source": "OpenAI",
      "target": "Microsoft",
      "type": "PARTNERS_WITH",
      "description": "OpenAI partners with Microsoft",
      "strength": 10
    }
  ],
  "extraction_timestamp": "2025-11-02T10:40:00"
}
```

### Common Cypher Queries

See `cypher queries/neo4j_queries.cypher` for complete query examples.

**Quick Examples:**

```cypher
// Get statistics
MATCH (n)
RETURN labels(n)[0] as type, count(n) as count
ORDER BY count DESC;

// Find most connected companies
MATCH (c:Company)-[r]-()
RETURN c.name, count(r) as connections
ORDER BY connections DESC
LIMIT 10;

// Find funding relationships
MATCH (c:Company)-[r:FUNDED_BY]->(i:Investor)
RETURN c.name as company, i.name as investor, r.strength as strength
ORDER BY r.strength DESC
LIMIT 20;

// Find entities in a specific article
MATCH (e)
WHERE 'article_id' IN e.source_articles
RETURN e.name, labels(e)[0] as type
LIMIT 20;
```

### Dependencies

**Required:**
- `crawl4ai>=0.7.6` - Web scraping
- `langchain-core>=0.3.0` - LLM integration
- `langchain-openai>=0.2.0` - OpenAI integration
- `neo4j>=5.0.0` - Graph database
- `openai>=1.0.0` - OpenAI API
- `python-dotenv>=1.0.0` - Environment variables

**Optional:**
- `openai` - For embeddings (if using OpenAI embeddings)
- `sentence-transformers` - For embeddings (alternative)
- Neo4j Graph Data Science (GDS) - For advanced community detection

### Workflow Summary

**Complete Pipeline Flow:**

1. **Scrape Articles** (optional)
   ```bash
   python pipeline.py --scrape-category startups --scrape-max-pages 3
   ```

2. **Extract Entities** (automatic)
   - Uses GPT-4o to extract entities and relationships
   - Validates and normalizes entities
   - Saves checkpoints for resume capability

3. **Build Graph** (automatic)
   - Creates nodes in Neo4j
   - Creates relationships
   - Links entities to articles via properties

4. **Post-Process** (optional)
   ```bash
   python integrate_new_features.py
   ```
   - Entity deduplication
   - Relationship strength updates
   - Community detection
   - Embedding generation

5. **Query Graph**
   - Use Neo4j Browser or Cypher queries
   - Implement Graph RAG for natural language queries

### Graph RAG Implementation (Phase 4 - Future)

**What is Graph RAG?**
- **Graph RAG**: Retrieval-Augmented Generation using knowledge graphs
- Combines structured graph queries with LLM generation
- More accurate than vector-only RAG for structured data

**Implementation Steps:**

#### A. Create Graph RAG Module (`graph_rag.py`)
```python
class GraphRAG:
    """Graph RAG system for querying knowledge graph"""
    
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, llm):
        # Connect to Neo4j
        # Initialize LLM
    
    def query(self, question: str) -> str:
        # 1. Parse question to extract entities/relationships
        # 2. Generate Cypher query
        # 3. Execute query
        # 4. Format results
        # 5. Generate natural language answer
```

#### B. Query Types to Support:
1. **Entity Lookup**: "Tell me about OpenAI"
2. **Relationship Queries**: "Who funded Anthropic?"
3. **Path Queries**: "What's the connection between X and Y?"
4. **Aggregation**: "Which companies got the most funding?"

#### C. Optional: Add Vector Embeddings
- Add embeddings to nodes for semantic search
- Hybrid approach: Graph structure + semantic similarity
- Use `sentence-transformers` or `openai` embeddings

**Graph RAG Resources:**
- Microsoft GraphRAG: https://github.com/microsoft/graphrag
- Neo4j + LangChain: https://python.langchain.com/docs/integrations/graphs/neo4j
- Knowledge Graph RAG: https://neo4j.com/developer/knowledge-graphs/graph-rag/

### Implementation History

**All Missing Steps Implemented:**

1. ✅ **Entity Resolution & Deduplication** - Fuzzy matching and merging
2. ✅ **Enhanced Data Validation** - Funding amounts, dates, entity names
3. ✅ **Relationship Strength Calculation** - Frequency, recency, credibility scoring
4. ✅ **Temporal Analysis** - Timeline tracking and trend analysis
5. ✅ **Entity Type Classification Refinement** - Confidence scores and multi-signal
6. ✅ **Coreference Resolution** - Pronoun and reference resolution
7. ✅ **Community Detection** - Graph-based community identification
8. ✅ **Embedding Generation** - Vector embeddings for semantic search

**Previously Implemented:**
- ✅ Checkpointing/Resume Capability
- ✅ Data Validation
- ✅ Error Handling & Retry Logic
- ✅ Scraping Integration
- ✅ Entity Normalization
- ✅ Progress Tracking & Reporting
- ✅ Graph Post-Processing Automation

---

## 📝 License

This is a personal project for educational purposes. Respect TechCrunch's robots.txt and terms of service.

---

**Happy Knowledge Graph Building! 🚀**

