# Documentation Index

Complete documentation for the Startup Intelligence Analysis App.

---

## 📚 Getting Started

Perfect for first-time users:

1. **[Getting Started Guide](guides/GETTING_STARTED.md)** - Quick setup and first queries
2. **[How to Run](guides/HOW_TO_RUN.md)** - Complete workflow from scraping to querying
3. **[Main README](../README.md)** - Project overview and quick commands

---

## 🔌 API & Querying

Learn how to query the knowledge graph:

- **[GraphRAG API Documentation](api/RAG_DOCUMENTATION.md)** - Complete API reference with 40+ endpoints
- **[Query Examples](api/QUERY_EXAMPLES.md)** - Common query patterns and use cases
- **API Docs (Live)**: http://localhost:8000/docs (when API is running)

---

## 🚀 Deployment

Deploy to production:

### Cloud Deployment
- Azure documentation has been removed.

### Database Options
- **[Neo4j Aura Setup](deployment/AURA_SETUP.md)** - Use managed Neo4j cloud (Consolidated)
- **[Aura DB Setup](deployment/AURA_DB_SETUP.md)** - Detailed Aura configuration
- **[Aura Credentials Guide](deployment/AURA_CREDENTIALS_GUIDE.md)** - Managing Aura credentials

### Security
- **[SSL Setup](deployment/SSL_SETUP.md)** - Configure HTTPS/SSL for production

---

## 🛠️ Development

For contributors and advanced users:

- **[Improvements & Recommendations](development/IMPROVEMENTS.md)** - Enhancement suggestions and code review
- **[Architecture](development/ARCHITECTURE.md)** - System design and component details
- **[Contributing Guide](development/CONTRIBUTING.md)** - How to contribute (TODO)

---

## 📖 Component Documentation

### Pipeline Components

1. **Web Scraping** (`scraper/`)
   - TechCrunch article extraction
   - Configurable rate limiting
   - Checkpoint/resume capability

2. **Entity Extraction** (`entity_extractor.py`)
   - GPT-4o based extraction
   - Entity normalization
   - Validation and filtering

3. **Graph Building** (`graph_builder.py`)
   - Neo4j schema creation
   - Entity and relationship creation
   - Deduplication logic

4. **GraphRAG Query** (`rag_query.py`, `query_templates.py`)
   - Natural language queries
   - Semantic search
   - Multi-hop reasoning

### Utility Modules (`utils/`)

- `entity_resolver.py` - Entity deduplication
- `embedding_generator.py` - Vector embeddings
- `community_detector.py` - Community detection
- `relationship_scorer.py` - Relationship strength
- `temporal_analyzer.py` - Timeline analysis
- `data_validation.py` - Data quality checks
- `entity_normalization.py` - Name normalization
- `filter_techcrunch.py` - Noise filtering

---

## 🎯 Use Case Guides

### 1. Competitive Intelligence
- Research companies
- Analyze competitors
- Track market positioning

See: [Getting Started - Use Case 1](guides/GETTING_STARTED.md#use-case-1-competitive-intelligence)

### 2. Investment Research
- Find funded companies
- Analyze investor portfolios
- Discover investment trends

See: [Getting Started - Use Case 2](guides/GETTING_STARTED.md#use-case-2-investment-research)

### 3. Market Trend Analysis
- Track technology trends
- Monitor industry developments
- Analyze recent activity

See: [Getting Started - Use Case 3](guides/GETTING_STARTED.md#use-case-3-market-trend-analysis)

---

## 🐛 Troubleshooting

### Common Issues

- **Neo4j Connection**: See [Aura Setup - Troubleshooting](deployment/AURA_SETUP.md#troubleshooting)
- **Scraping Issues**: See [Main README - Troubleshooting](../README.md#troubleshooting)
- **API Errors**: See [API Documentation](api/RAG_DOCUMENTATION.md#error-handling)
- **Aura Connection**: See [Aura Setup - Troubleshooting](deployment/AURA_SETUP.md#troubleshooting)

---

## 📊 Reference

### Entity Types
Company, Person, Investor, Technology, Product, FundingRound, Location, Event

### Relationship Types
FUNDED_BY, FOUNDED_BY, WORKS_AT, ACQUIRED, PARTNERS_WITH, COMPETES_WITH, USES_TECHNOLOGY, LOCATED_IN, ANNOUNCED_AT, REGULATES, OPPOSES, SUPPORTS, COLLABORATES_WITH, INVESTS_IN, ADVISES, LEADS

See: [Main README - Entity Types & Relationships](../README.md#entity-types--relationships)

---

## 🔗 Quick Links

### Live Interfaces
- **Neo4j Browser**: http://localhost:7474
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### GitHub & Resources
- **Repository**: (your-repo-url)
- **Neo4j Documentation**: https://neo4j.com/docs/
- **OpenAI API**: https://platform.openai.com/docs
- **FastAPI**: https://fastapi.tiangolo.com/

---

## 📝 Document Structure

```
docs/
├── INDEX.md (this file)
├── guides/
│   ├── GETTING_STARTED.md      # Quick start guide
│   └── HOW_TO_RUN.md           # Complete workflow
├── api/
│   ├── RAG_DOCUMENTATION.md    # API reference
│   └── QUERY_EXAMPLES.md       # Query patterns
├── deployment/
│   ├── AURA_SETUP.md          # Neo4j Aura (consolidated)
│   ├── SSL_SETUP.md           # SSL/HTTPS
│   ├── AURA_DB_SETUP.md
│   └── AURA_CREDENTIALS_GUIDE.md
└── development/
    ├── IMPROVEMENTS.md         # Enhancement suggestions
    └── ARCHITECTURE.md         # System design
```

---

**Need help? Start with the [Getting Started Guide](guides/GETTING_STARTED.md)!**

