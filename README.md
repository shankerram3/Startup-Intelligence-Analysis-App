# Startup Intelligence Analysis App

A comprehensive knowledge graph and GraphRAG system that extracts entities and relationships from TechCrunch articles, stores them in Neo4j, and provides intelligent querying capabilities.

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- Neo4j (Docker recommended)
- OpenAI API key

### 2. Install & Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start Neo4j
docker-compose up -d

# Verify setup
python -c "from neo4j import GraphDatabase; print('✓ Neo4j ready')"
```

### 3. Run Pipeline

```bash
# Small test (10 articles)
python pipeline.py --scrape-category startups --scrape-max-pages 2 --max-articles 10

# Production run
python pipeline.py --scrape-category ai --scrape-max-pages 10 --advanced-features
```

### 4. Start Querying

```bash
# Start API server
python api.py

# Or use Python client
python api_client_example.py

# Or Neo4j Browser
open http://localhost:7474
```

---

## 📚 Documentation

### Getting Started
- **[Getting Started Guide](docs/guides/GETTING_STARTED.md)** - Detailed setup and first steps
- **[How to Run](docs/guides/HOW_TO_RUN.md)** - Complete workflow from scraping to querying

### API & Querying
- **[GraphRAG API Documentation](docs/api/RAG_DOCUMENTATION.md)** - Complete API reference
- **[Query Examples](docs/api/QUERY_EXAMPLES.md)** - Common query patterns

### Deployment
- **[Azure Deployment](docs/deployment/AZURE_DEPLOYMENT.md)** - Deploy to Azure
- **[Neo4j Aura Setup](docs/deployment/AURA_SETUP.md)** - Use Neo4j Aura cloud
- **[SSL Setup](docs/deployment/SSL_SETUP.md)** - Configure HTTPS

### Development
- **[Improvements & Recommendations](docs/development/IMPROVEMENTS.md)** - Enhancement suggestions
- **[Architecture](docs/development/ARCHITECTURE.md)** - System design details

---

## ✨ Features

### Core Pipeline
- ✅ **Web Scraping** - Automated TechCrunch article extraction
- ✅ **Entity Extraction** - LLM-based entity and relationship identification  
- ✅ **Knowledge Graph** - Neo4j graph database construction
- ✅ **Advanced Features** - Deduplication, validation, embeddings

### GraphRAG Query System
- ✅ **Natural Language Queries** - Ask questions in plain English
- ✅ **Semantic Search** - Vector similarity-based retrieval
- ✅ **Hybrid Search** - Combined semantic + keyword search
- ✅ **REST API** - 40+ FastAPI endpoints
- ✅ **Multi-hop Reasoning** - Complex graph traversal
- ✅ **Entity Comparison** - Compare companies, investors, etc.

### Data Quality
- ✅ **Multi-layer Validation** - Article and extraction validation
- ✅ **Entity Deduplication** - Automatic duplicate merging
- ✅ **Quality Filtering** - Removes noise and irrelevant data
- ✅ **Checkpoint System** - Resume capability for long runs

---

## 🏗️ Architecture

```
TechCrunch Articles
    ↓
[Phase 0: Web Scraping] → Raw Article JSON
    ↓
[Phase 1: Entity Extraction] → Entities & Relationships JSON
    ↓
[Phase 2: Graph Construction] → Neo4j Knowledge Graph
    ↓
[Phase 3: Post-Processing] → Enhanced Graph
    ↓
[Phase 4: GraphRAG Queries] → Natural Language Q&A
```

### Key Components

- **Scraper** (`scraper/`) - TechCrunch article extraction
- **Entity Extractor** (`entity_extractor.py`) - GPT-4o based extraction
- **Graph Builder** (`graph_builder.py`) - Neo4j graph construction
- **GraphRAG** (`rag_query.py`, `query_templates.py`) - Query system
- **REST API** (`api.py`) - FastAPI server
- **Utils** (`utils/`) - Helper modules for validation, deduplication, etc.

---

## 📋 Common Commands

### Pipeline Operations

```bash
# Full pipeline (scrape → extract → build graph)
python pipeline.py --scrape-category startups --scrape-max-pages 2 --max-articles 10

# Skip scraping (use existing articles)
python pipeline.py --skip-scraping --max-articles 50

# Skip scraping and extraction (use existing extractions)
python pipeline.py --skip-scraping --skip-extraction

# With advanced features (deduplication, embeddings, etc.)
python pipeline.py --scrape-category ai --max-articles 20 --advanced-features
```

### Query Operations

```bash
# Start REST API
python api.py

# Use Python client
python api_client_example.py

# Direct queries (CLI)
python -m rag.hybrid_rag "Tell me about AI startups" --entities 5 --docs 5
```

### Neo4j Operations

```bash
# Check graph statistics
python -c "from neo4j import GraphDatabase; import os; from dotenv import load_dotenv; load_dotenv(); driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))); session = driver.session(); result = session.run('MATCH (n) RETURN count(n) as count'); print(f'Nodes: {result.single()[\"count\"]}'); session.close(); driver.close()"

# Generate embeddings
python -c "from neo4j import GraphDatabase; from utils.embedding_generator import EmbeddingGenerator; import os; from dotenv import load_dotenv; load_dotenv(); driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))); gen = EmbeddingGenerator(driver, 'openai'); gen.generate_embeddings_for_all_entities(); driver.close()"
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file:

```bash
# OpenAI API (required for entity extraction)
OPENAI_API_KEY=sk-your-openai-api-key

# Neo4j Connection (required)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# API Configuration (optional)
API_HOST=0.0.0.0
API_PORT=8000

# Embeddings (optional)
RAG_EMBEDDING_BACKEND=openai  # or "sentence-transformers"
```

### Scraper Configuration

Edit `scraper/scraper_config.py`:

```python
SCRAPER_CONFIG = {
    "rate_limit_delay": 3.0,  # Seconds between requests
    "max_pages": None,         # None = unlimited
    "batch_size": 10,          # Concurrent extractions
}
```

---

## 📊 Entity Types & Relationships

### Entity Types
- **Company** - Companies and organizations
- **Person** - People and individuals
- **Investor** - Investment firms and VCs
- **Technology** - Technologies and frameworks
- **Product** - Products and services
- **FundingRound** - Funding rounds
- **Location** - Geographic locations
- **Event** - Events and conferences

### Relationship Types
- `FUNDED_BY` - Company ← Investor
- `FOUNDED_BY` - Company ← Person
- `WORKS_AT` - Person → Company
- `ACQUIRED` - Company → Company
- `PARTNERS_WITH` - Entity ↔ Entity
- `COMPETES_WITH` - Company ↔ Company
- `USES_TECHNOLOGY` - Entity → Technology
- `LOCATED_IN` - Entity → Location
- `REGULATES` - Government → Entity
- `OPPOSES` - Entity ↔ Entity
- `SUPPORTS` - Entity → Entity
- `COLLABORATES_WITH` - Entity ↔ Entity
- `INVESTS_IN` - Entity → Entity
- `ADVISES` - Entity → Entity
- `LEADS` - Person → Company

---

## 🐛 Troubleshooting

### Neo4j Connection Error
```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Restart Neo4j
docker-compose restart
```

### OpenAI API Error
```bash
# Check .env file
cat .env | grep OPENAI_API_KEY

# Test API key
python -c "from openai import OpenAI; import os; from dotenv import load_dotenv; load_dotenv(); client = OpenAI(api_key=os.getenv('OPENAI_API_KEY')); print('✓ API key valid')"
```

### Scraping Fails
```bash
# Install browser dependencies
crawl4ai-setup

# Increase rate limit delay (edit scraper/scraper_config.py)
rate_limit_delay = 5.0  # Instead of 3.0
```

### Entity Extraction Issues
```bash
# Check for metadata files being processed
find data/articles -name "*.json" | grep -E "(discovered|failed)_articles"

# If found, they should be in metadata/ directory only
```

---

## 📈 Performance

### Typical Performance
- **Scraping**: ~15-20 articles/page, 3-5 seconds/page
- **Extraction**: ~2-3 seconds/article (GPT-4o dependent)
- **Graph Building**: ~0.5-1 second/article
- **Query Response**: <1 second (with proper indexes)

### Optimization Tips
1. Process in batches (use `--max-articles`)
2. Use checkpoint/resume for large datasets
3. Generate embeddings once, reuse many times
4. Use local embeddings (sentence-transformers) for faster semantic search
5. Limit multi-hop queries to 2-3 hops

---

## 🎯 Use Cases

### 1. Competitive Intelligence
```python
from rag_query import create_rag_query
rag = create_rag_query()

# Get company profile
profile = rag.get_company_profile("Anthropic")

# Get competitors
landscape = rag.get_competitive_landscape("Anthropic")

# Compare
comparison = rag.compare_entities("OpenAI", "Anthropic")
```

### 2. Investment Research
```python
# Find funded companies
funded = rag.query("Which AI startups raised funding recently?")

# Analyze investor
portfolio = rag.get_investor_portfolio("Sequoia Capital")

# Discover trends
tech_trends = rag.get_trending_technologies(limit=10)
```

### 3. Market Analysis
```python
# Recent activity
recent = rag.query("What are the latest AI developments?")

# Semantic search
similar = rag.semantic_search("artificial intelligence startups", top_k=10)

# Multi-hop reasoning
insights = rag.multi_hop_reasoning(
    "What technologies are used by companies funded by top investors?"
)
```

---

## 📝 API Endpoints

### Query Endpoints
- `POST /query` - Natural language questions
- `POST /search/semantic` - Vector similarity search
- `POST /search/hybrid` - Combined semantic + keyword

### Entity Endpoints
- `GET /entity/{name}` - Get entity by name
- `POST /entity/compare` - Compare two entities
- `GET /company/{name}` - Company profile
- `GET /investor/{name}` - Investor portfolio
- `GET /person/{name}` - Person profile

### Analytics Endpoints
- `GET /statistics` - Graph statistics
- `GET /analytics/importance` - Entity importance scores
- `GET /technology/trending` - Trending technologies
- `GET /community/detect` - Detect communities

See [complete API documentation](docs/api/RAG_DOCUMENTATION.md) for all 40+ endpoints.

---

## 🛠️ Development

### Project Structure

```
├── pipeline.py              # Main orchestrator
├── entity_extractor.py      # LLM-based extraction
├── graph_builder.py         # Neo4j construction
├── rag_query.py            # GraphRAG query system
├── query_templates.py      # Cypher query library
├── api.py                  # REST API server
├── scraper/                # Web scraping
│   ├── techcrunch_scraper.py
│   ├── run_scraper.py
│   └── scraper_config.py
├── utils/                  # Helper modules
│   ├── entity_resolver.py
│   ├── embedding_generator.py
│   ├── community_detector.py
│   └── ...
├── rag/                    # RAG modules
│   ├── hybrid_rag.py
│   └── vector_index.py
├── data/
│   ├── articles/           # Scraped articles
│   └── processing/         # Extractions
└── docs/                   # Documentation
    ├── guides/
    ├── api/
    └── deployment/
```

### Running Tests

```bash
# Test Neo4j connection
python -c "from neo4j import GraphDatabase; import os; from dotenv import load_dotenv; load_dotenv(); driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))); driver.verify_connectivity(); print('✓ Neo4j connected'); driver.close()"

# Test entity extraction
python entity_extractor.py

# Test graph building
python graph_builder.py

# Test API
python api_client_example.py
```

---

## 🚢 Deployment

### Local Development
```bash
docker-compose up -d
python api.py
```

### Production (Azure)
See [Azure Deployment Guide](docs/deployment/AZURE_DEPLOYMENT.md)

### Neo4j Cloud (Aura)
See [Neo4j Aura Setup](docs/deployment/AURA_SETUP.md)

### SSL/HTTPS
See [SSL Setup Guide](docs/deployment/SSL_SETUP.md)

---

## 🤝 Contributing

This is an educational project. Feel free to:
- Explore the code
- Suggest improvements
- Report issues
- Fork and extend

---

## 📄 License

This is a personal project for educational purposes. Respect TechCrunch's robots.txt and terms of service when scraping.

---

## 🚀 Future Enhancements

### ✅ Completed Features
- [x] Hybrid RAG implementation
- [x] REST API implementation (40+ endpoints)
- [x] GraphRAG query system
- [x] Semantic search with embeddings
- [x] Multi-hop reasoning
- [x] Entity deduplication
- [x] Community detection
- [x] Relationship scoring

### 🎯 Planned Features

**Phase 1: UI & Visualization**
- [ ] Web UI frontend (React/Vue integration)
- [ ] Interactive graph visualization
- [ ] Query builder interface
- [ ] Real-time query results

**Phase 2: Enhanced Intelligence**
- [ ] Evaluation framework and metrics
- [ ] Query rewriting and expansion
- [ ] Reranking with cross-encoders
- [ ] Automated insight generation

**Phase 3: Data & Integration**
- [ ] Real-time article updates (streaming)
- [ ] Multi-source support (beyond TechCrunch)
- [ ] Custom entity types and relationships
- [ ] Data export functionality (PDF, CSV, JSON)

**Phase 4: Analytics & Scale**
- [ ] Advanced analytics dashboard
- [ ] Temporal trend analysis
- [ ] Predictive analytics
- [ ] Multi-tenant support
- [ ] Query caching and optimization

**Phase 5: Enterprise Features**
- [ ] Authentication & authorization
- [ ] Rate limiting and quotas
- [ ] Audit logging
- [ ] Webhook notifications
- [ ] GraphQL API support

See [ARCHITECTURE.md](docs/development/ARCHITECTURE.md) and [IMPROVEMENTS.md](docs/development/IMPROVEMENTS.md) for detailed roadmap.

---

## 🔗 Quick Links

- **Neo4j Browser**: http://localhost:7474
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

---

## 🤝 Contributing

Interested in contributing? We'd love your help! Here's how:

1. **Report Issues** - Found a bug? Open an issue
2. **Suggest Features** - Have an idea? Let us know
3. **Submit PRs** - Fork, implement, and submit a pull request
4. **Improve Docs** - Help make the documentation better

---

**Built with:** Python, Neo4j, FastAPI, OpenAI GPT-4o, LangChain, Sentence Transformers

**Happy Knowledge Graph Building! 🚀**
