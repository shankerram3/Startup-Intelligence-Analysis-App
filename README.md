# Startup Intelligence Analysis App

A comprehensive knowledge graph and GraphRAG system that extracts entities and relationships from TechCrunch articles, stores them in Neo4j, and provides intelligent querying capabilities with a React frontend.

---

## 🚀 Quick Start (5 Minutes)

### 1. Prerequisites
- Python 3.11+
- Neo4j (Docker or Aura cloud)
- OpenAI API key
- Node.js 18+ (for frontend)

### 2. Install & Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cat > .env << 'EOF'
OPENAI_API_KEY=sk-your-openai-api-key
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io  # or bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
API_HOST=0.0.0.0
API_PORT=8000
RAG_EMBEDDING_BACKEND=sentence-transformers
SENTENCE_TRANSFORMERS_MODEL=BAAI/bge-small-en-v1.5
EOF

# Start Neo4j (if using Docker)
docker-compose up -d
```

### 3. Run Pipeline

```bash
# Build knowledge graph (embeddings generated automatically!)
python pipeline.py \
  --scrape-category startups \
  --scrape-max-pages 2 \
  --max-articles 10
```

This automatically runs all phases:
1. **Web Scraping** - TechCrunch article extraction
2. **Entity Extraction** - GPT-4o NER and relationships
3. **Company Intelligence Enrichment** 🆕 - Deep company data via Playwright
4. **Graph Construction** - Build Neo4j knowledge graph
5. **Post-Processing** - Embeddings, deduplication, communities

### 4. Start Services

```bash
# Start everything
./start_all.sh

# Access from local machine: http://YOUR_VM_IP:5173
# Access locally: http://localhost:5173
```

---

## ✨ Features

### Core Pipeline
- ✅ **Web Scraping** - Automated TechCrunch article extraction
- ✅ **Entity Extraction** - GPT-4o based NER and relationship extraction
- ✅ **Company Intelligence** 🆕 - Playwright-powered deep company data scraping
- ✅ **Knowledge Graph** - Neo4j graph database with enriched company profiles
- ✅ **Auto Post-Processing** - Embeddings, deduplication, communities (automatic!)

### GraphRAG Query System
- ✅ **Natural Language Queries** - Ask questions in plain English
- ✅ **Semantic Search** - Vector similarity search with sentence-transformers
- ✅ **Hybrid Search** - Combined semantic + keyword search
- ✅ **REST API** - 40+ FastAPI endpoints
- ✅ **React Frontend** - Modern web UI with chat & dashboard
- ✅ **Multi-hop Reasoning** - Complex graph traversal
- ✅ **Entity Comparison** - Compare companies, investors, etc.

### Data Quality
- ✅ **Multi-layer Validation** - Article and extraction validation
- ✅ **Entity Deduplication** - Automatic duplicate merging
- ✅ **Quality Filtering** - Removes noise and irrelevant data
- ✅ **Checkpoint System** - Resume capability for long runs

---

## 📋 Common Commands

### Pipeline

```bash
# Full pipeline (automatic embeddings!)
python pipeline.py --scrape-category startups --scrape-max-pages 2 --max-articles 10

# Use existing articles
python pipeline.py --skip-scraping --max-articles 50

# Use existing extractions
python pipeline.py --skip-scraping --skip-extraction
```

### Services

```bash
# Start all (API + Frontend in tmux)
./start_all.sh

# Start API only
python api.py

# Start frontend only
cd frontend && npm run dev

# Stop all
tmux kill-session -t graphrag
```

### Query

```bash
# Via React UI
open http://localhost:5173

# Via API docs
open http://localhost:8000/docs

# Via Python
python -c "from rag_query import create_rag_query; rag = create_rag_query(); print(rag.query('Which AI startups raised funding?')['answer']); rag.close()"

# Via cURL
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"question": "Which AI startups raised funding?", "use_llm": true}'
```

---

## 🔧 Configuration

### Backend (`.env`)

```bash
# Required
OPENAI_API_KEY=sk-your-key
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io  # Aura
# NEO4J_URI=bolt://localhost:7687  # Local Docker
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# Optional
API_HOST=0.0.0.0
API_PORT=8000
RAG_EMBEDDING_BACKEND=sentence-transformers
SENTENCE_TRANSFORMERS_MODEL=BAAI/bge-small-en-v1.5
```

### Frontend (`frontend/.env.local`)

```bash
# Local development
VITE_API_BASE_URL=http://localhost:8000

# Azure VM
VITE_API_BASE_URL=http://YOUR_VM_PUBLIC_IP:8000
```

---

## 🏗️ Architecture

```
Phase 0: Web Scraping → Raw JSON
Phase 1: Entity Extraction → Entities & Relationships
Phase 1.5: Company Intelligence 🆕 → Deep company data via Playwright
Phase 2: Graph Construction → Neo4j Knowledge Graph (with enriched data)
Phase 3: Graph Cleanup → Remove noise
Phase 4: Post-Processing → Embeddings, Deduplication, Communities (AUTOMATIC)
    ↓
Ready for Queries!
```

**NEW**: Phase 1.5 enriches companies with:
- Founded year, employee count, headquarters
- Founders, executives, team information
- Funding rounds and investment data
- Products, technologies, pricing models
- Website URLs and social links

---

## 📊 Entity Types & Relationships

### Entity Types
Company, Person, Investor, Technology, Product, FundingRound, Location, Event

### Relationship Types
`FUNDED_BY`, `FOUNDED_BY`, `WORKS_AT`, `ACQUIRED`, `PARTNERS_WITH`, `COMPETES_WITH`, `USES_TECHNOLOGY`, `LOCATED_IN`, `ANNOUNCED_AT`, `REGULATES`, `OPPOSES`, `SUPPORTS`, `COLLABORATES_WITH`, `INVESTS_IN`, `ADVISES`, `LEADS`

---

## 🐛 Troubleshooting

### Queries Return "No Relevant Context"
```bash
# Check embeddings
python -c "from neo4j import GraphDatabase; import os; from dotenv import load_dotenv; load_dotenv(); driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))); result = driver.session().run('MATCH (n) WHERE n.embedding IS NOT NULL RETURN count(n) as count'); print(f'Embeddings: {result.single()[\"count\"]}'); driver.close()"

# Generate embeddings if needed
python -c "from neo4j import GraphDatabase; from utils.embedding_generator import EmbeddingGenerator; import os; from dotenv import load_dotenv; load_dotenv(); driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))); gen = EmbeddingGenerator(driver, 'sentence-transformers'); gen.generate_embeddings_for_all_entities(); driver.close()"
```

### Neo4j Connection Failed
```bash
# Check Neo4j
docker ps | grep neo4j

# Start Neo4j
docker-compose up -d

# Test connection
python -c "from neo4j import GraphDatabase; import os; from dotenv import load_dotenv; load_dotenv(); driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))); driver.verify_connectivity(); print('✓ Connected'); driver.close()"
```

### Frontend Not Accessible
```bash
# Check services
sudo netstat -tulpn | grep -E '8000|5173'

# Check firewall
sudo ufw status | grep -E '8000|5173'

# Add firewall rules
sudo ufw allow 8000/tcp
sudo ufw allow 5173/tcp

# Add Azure NSG rules (Azure Portal → VM → Networking)
# - Port 8000 (API)
# - Port 5173 (Frontend)
```

### Chat Not Working
```bash
# Hard refresh browser: Ctrl + Shift + R
# Check browser console (F12) for errors
# Verify API: curl http://YOUR_VM_IP:8000/health
```

### Port Already in Use
```bash
# Kill existing services
tmux kill-session -t graphrag

# Restart
./start_all.sh
```

---

## 🚢 Deployment

### Local Development
```bash
docker-compose up -d
python api.py
cd frontend && npm run dev
```

### Azure VM

```bash
# On Azure VM
./start_all.sh

# Access from local browser
http://YOUR_VM_PUBLIC_IP:5173
```

**Required Azure NSG Ports:**
- 5173 (Frontend)
- 8000 (API)
- 7474 (Neo4j Browser)
- 7687 (Neo4j Bolt)

**Configuration:**
- Update `frontend/.env.local` with VM public IP
- Frontend vite.config.ts set to `host: '0.0.0.0'`
- API listens on `0.0.0.0`

---

## 🚀 Future Enhancements

### ✅ Completed
- [x] Hybrid RAG implementation
- [x] REST API (40+ endpoints)
- [x] React frontend with chat & dashboard
- [x] Semantic search with embeddings
- [x] Multi-hop reasoning
- [x] Entity deduplication (automatic)
- [x] Community detection (automatic)
- [x] Relationship scoring (automatic)
- [x] Sentence-transformers support

### 🎯 Planned

**Phase 1: Enhanced UI**
- [ ] Interactive graph visualization
- [ ] Advanced query builder
- [ ] Real-time results streaming

**Phase 2: Intelligence**
- [ ] Evaluation framework
- [ ] Query rewriting
- [ ] Cross-encoder reranking
- [ ] Automated insights

**Phase 3: Data**
- [ ] Real-time updates
- [ ] Multi-source support
- [ ] Custom entity types
- [ ] Data export (PDF, CSV)

**Phase 4: Scale**
- [ ] Analytics dashboard
- [ ] Temporal trend analysis
- [ ] Predictive analytics
- [ ] Query caching

**Phase 5: Enterprise**
- [ ] Authentication
- [ ] Rate limiting
- [ ] Audit logging
- [ ] Webhooks
- [ ] GraphQL API

---

## 🔗 Quick Links

- **React Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474
- **Health Check**: http://localhost:8000/health

---

## 📚 Additional Documentation

- **[Company Intelligence Enrichment](docs/COMPANY_INTELLIGENCE_ENRICHMENT.md)** 🆕 - Deep company scraping
- **[API Reference](docs/api/RAG_DOCUMENTATION.md)** - Complete API documentation
- **[Query Examples](docs/api/QUERY_EXAMPLES.md)** - Query patterns
- **[Azure Deployment](docs/deployment/AZURE_DEPLOYMENT.md)** - Azure setup
- **[Neo4j Aura](docs/deployment/AURA_SETUP.md)** - Managed database
- **[Architecture](docs/development/ARCHITECTURE.md)** - Technical details
- **[Improvements](docs/development/IMPROVEMENTS.md)** - Enhancements

---

## 🤝 Contributing

1. Report issues
2. Suggest features
3. Submit PRs
4. Improve docs

---

**Built with:** Python, Neo4j, FastAPI, React, OpenAI GPT-4o, LangChain, Sentence Transformers

**Happy Knowledge Graph Building! 🚀**
