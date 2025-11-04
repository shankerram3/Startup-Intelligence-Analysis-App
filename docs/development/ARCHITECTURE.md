# System Architecture

Technical architecture and design decisions for the Startup Intelligence Analysis App.

---

## Overview

The system follows a pipeline architecture with four main phases:

```
Phase 0: Web Scraping
    ↓
Phase 1: Entity Extraction
    ↓
Phase 2: Graph Construction
    ↓
Phase 3: Post-Processing
    ↓
Phase 4: GraphRAG Queries
```

---

## Component Architecture

### 1. Web Scraping Layer

**Components:**
- `scraper/techcrunch_scraper.py` - Main scraper
- `scraper/run_scraper.py` - CLI interface
- `scraper/scraper_config.py` - Configuration

**Tech Stack:**
- Crawl4AI for web scraping
- AsyncIO for concurrent processing
- Playwright for browser automation

**Data Flow:**
```
TechCrunch → Discover URLs → Extract Content → Save JSON
```

**Output:**
```json
{
  "article_id": "abc123",
  "url": "https://...",
  "title": "...",
  "content": {
    "headline": "...",
    "paragraphs": [...]
  },
  "metadata": {...}
}
```

---

### 2. Entity Extraction Layer

**Components:**
- `entity_extractor.py` - LLM-based extraction
- `utils/entity_normalization.py` - Name normalization
- `utils/filter_techcrunch.py` - Noise filtering
- `utils/data_validation.py` - Quality checks

**Tech Stack:**
- OpenAI GPT-4o for entity extraction
- LangChain for LLM orchestration
- Custom parsing logic

**Architecture:**
```
Article JSON → LLM Prompt → Parse Response → Validate → Save
```

**Prompt Engineering:**
- GraphRAG-inspired prompt structure
- Entity types: Company, Person, Investor, Technology, Product, etc.
- Relationship types: FUNDED_BY, FOUNDED_BY, WORKS_AT, etc.

---

### 3. Graph Construction Layer

**Components:**
- `graph_builder.py` - Neo4j graph builder
- `utils/graph_cleanup.py` - Post-processing

**Tech Stack:**
- Neo4j graph database
- Python neo4j driver
- Cypher query language

**Schema:**
```cypher
// Nodes
(:Company), (:Person), (:Investor), (:Technology),
(:Product), (:FundingRound), (:Location), (:Event), (:Article)

// Relationships
-[:FUNDED_BY]-, -[:FOUNDED_BY]-, -[:WORKS_AT]-,
-[:ACQUIRED]-, -[:PARTNERS_WITH]-, -[:COMPETES_WITH]-,
-[:USES_TECHNOLOGY]-, -[:LOCATED_IN]-, -[:ANNOUNCED_AT]-,
-[:REGULATES]-, -[:OPPOSES]-, -[:SUPPORTS]-,
-[:COLLABORATES_WITH]-, -[:INVESTS_IN]-, -[:ADVISES]-, -[:LEADS]-
```

**Node Properties:**
- `id` (hash-based, unique)
- `name`
- `description`
- `source_articles` (array)
- `article_count`
- `mention_count`
- `created_at`, `updated_at`

---

### 4. Post-Processing Layer

**Components:**
- `utils/entity_resolver.py` - Deduplication
- `utils/relationship_scorer.py` - Strength calculation
- `utils/community_detector.py` - Community detection
- `utils/embedding_generator.py` - Vector embeddings
- `utils/temporal_analyzer.py` - Timeline analysis

**Features:**

#### Entity Resolution
- Fuzzy string matching (Levenshtein distance)
- Automatic merging of duplicates
- Canonical name selection

#### Relationship Scoring
- Frequency-based (30%)
- Recency-based (20%)
- Credibility-based (30%)
- Context-based (20%)

#### Community Detection
- Leiden algorithm (Neo4j GDS)
- Louvain algorithm
- Label Propagation
- Connected components (fallback)

#### Embeddings
- OpenAI embeddings (text-embedding-3-small)
- Sentence Transformers (BAAI/bge-small-en-v1.5)
- Stored as node properties

---

### 5. GraphRAG Query Layer

**Components:**
- `rag_query.py` - Query orchestrator
- `query_templates.py` - Cypher templates
- `rag/hybrid_rag.py` - Hybrid RAG
- `rag/vector_index.py` - Vector search

**Tech Stack:**
- FastAPI for REST API
- LangChain for LLM orchestration
- OpenAI for answer generation
- Neo4j for graph queries

**Query Flow:**
```
Question → Intent Classification → Query Routing → 
Graph Query (Cypher) → Context Retrieval → 
LLM Generation → Answer
```

**Query Types:**
1. **Entity Lookup** - Direct node queries
2. **Semantic Search** - Vector similarity
3. **Graph Traversal** - Multi-hop queries
4. **Aggregation** - Statistics and analytics
5. **Hybrid** - Combined approaches

---

## Data Flow Diagram

```
┌─────────────────┐
│  TechCrunch     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Web Scraper    │  (Phase 0)
│  - Crawl4AI     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Article JSON   │
│  Files          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Entity         │  (Phase 1)
│  Extractor      │
│  - GPT-4o       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Extraction     │
│  JSON Files     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Graph Builder  │  (Phase 2)
│  - Neo4j        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Knowledge      │
│  Graph (Neo4j)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Post-          │  (Phase 3)
│  Processing     │
│  - Dedup        │
│  - Embeddings   │
│  - Communities  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Enhanced       │
│  Knowledge      │
│  Graph          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  GraphRAG       │  (Phase 4)
│  Query System   │
│  - REST API     │
│  - RAG          │
└─────────────────┘
```

---

## Technology Stack

### Core Technologies
- **Python 3.11+** - Main language
- **Neo4j 5.x** - Graph database
- **OpenAI GPT-4o** - Entity extraction & LLM generation
- **FastAPI** - REST API framework

### Key Libraries
- **LangChain** - LLM orchestration
- **Crawl4AI** - Web scraping
- **neo4j** - Python driver
- **sentence-transformers** - Local embeddings
- **OpenAI** - API client
- **pydantic** - Data validation
- **python-dotenv** - Environment management

### Optional Dependencies
- **Neo4j GDS** - Advanced graph algorithms
- **Docker** - Containerization
- **Uvicorn** - ASGI server

---

## Design Patterns

### 1. Pipeline Pattern
Sequential processing with checkpoint/resume capability:
```python
Scrape → Extract → Build Graph → Enhance
```

### 2. Factory Pattern
Creation of different entity types:
```python
def _get_node_label(entity_type: str) -> str:
    type_mapping = {
        "COMPANY": "Company",
        "PERSON": "Person",
        # ...
    }
    return type_mapping.get(entity_type, "Entity")
```

### 3. Strategy Pattern
Different embedding backends:
```python
if embedding_model == "openai":
    generator = OpenAIEmbeddingGenerator()
elif embedding_model == "sentence_transformers":
    generator = SentenceTransformerGenerator()
```

### 4. Repository Pattern
Graph database abstraction:
```python
class GraphRepository:
    def create_entity(self, entity: Dict) -> str
    def find_entity(self, name: str) -> Optional[Dict]
    def create_relationship(self, rel: Dict) -> None
```

---

## Performance Considerations

### Scalability

**Current Limits:**
- ~1000 articles: Good performance
- ~10,000 articles: May need optimization
- ~100,000+ articles: Requires scaling strategy

**Optimization Strategies:**

1. **Batch Processing**
   ```python
   # Process in batches of 10-50 articles
   for batch in chunks(articles, batch_size=50):
       process_batch(batch)
   ```

2. **Parallel Extraction**
   ```python
   # Use concurrent processing
   with ThreadPoolExecutor(max_workers=5) as executor:
       futures = [executor.submit(extract, article) for article in articles]
   ```

3. **Graph Indexes**
   ```cypher
   CREATE INDEX IF NOT EXISTS FOR (c:Company) ON (c.id);
   CREATE INDEX IF NOT EXISTS FOR (c:Company) ON (c.name);
   ```

4. **Query Optimization**
   ```python
   # Limit graph traversal depth
   context = get_entity_context(entity_id, max_hops=2)  # Not 5
   
   # Use specific relationship types
   MATCH (c:Company)-[:FUNDED_BY]->(i:Investor)  # Not (c)-[]-(i)
   ```

---

## Security Considerations

### 1. Credential Management
- Store credentials in environment variables
- Never commit `.env` to version control
- Use secret management services in production

### 2. API Security
```python
# Add authentication (not implemented yet)
@app.post("/query")
async def query(request: QueryRequest, api_key: str = Depends(verify_api_key)):
    # ... process query
```

### 3. Input Validation
```python
# Validate all inputs
def validate_entity_name(name: str) -> bool:
    if not name or len(name) > 200:
        return False
    if any(char in name for char in ['<', '>', ';', '&']):
        return False
    return True
```

### 4. Rate Limiting
```python
# Implement rate limiting for API
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)
@limiter.limit("10/minute")
@app.post("/query")
async def query(request: QueryRequest):
    # ... process query
```

---

## Error Handling

### 1. Retry Logic
```python
@retry_with_backoff(max_retries=3, backoff_factor=2)
def extract_entities(article):
    # ... extraction logic
```

### 2. Checkpoint System
```python
# Save progress periodically
if i % 10 == 0:
    checkpoint.save()
    save_extractions()
```

### 3. Graceful Degradation
```python
try:
    # Try advanced algorithm
    communities = detect_communities_leiden()
except:
    # Fallback to simpler algorithm
    communities = detect_communities_connected_components()
```

---

## Future Enhancements

### Short-term (v1.1)
- [ ] API authentication
- [ ] Query result caching
- [ ] Pagination for large result sets
- [ ] Enhanced logging and monitoring

### Medium-term (v1.5)
- [ ] Web UI dashboard
- [ ] Real-time article updates
- [ ] Multi-source support (beyond TechCrunch)
- [ ] Advanced analytics dashboard

### Long-term (v2.0)
- [ ] Multi-region deployment
- [ ] Graph visualization
- [ ] Custom entity types
- [ ] Fine-tuned extraction models
- [ ] Export functionality (PDF reports, CSV)

See [IMPROVEMENTS.md](IMPROVEMENTS.md) for detailed recommendations.

---

## References

- **Neo4j Documentation**: https://neo4j.com/docs/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **LangChain Documentation**: https://python.langchain.com/
- **GraphRAG Paper**: https://arxiv.org/abs/2404.16130

---

For implementation details, see the source code with inline comments.

