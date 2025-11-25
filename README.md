# Startup Intelligence Analysis App

A comprehensive knowledge graph and GraphRAG system that extracts entities and relationships from TechCrunch articles, stores them in Neo4j, and provides intelligent querying capabilities with a React frontend.

---

## Table of Contents

1. [Quick Start](#quick-start-5-minutes)
2. [Project Overview](#features)
3. [Installation & Setup](#configuration)
4. [Pipeline Architecture](#architecture)
5. [Company Intelligence Enrichment](#company-intelligence-enrichment)
6. [GraphRAG System](#graphrag-system)
7. [API Reference](#api-reference)
8. [Query Examples](#query-examples)
9. [Deployment](#deployment)
   - [Docker Deployment](#docker-deployment)
   - [Neo4j Aura Setup](#neo4j-aura-setup)
   - [Aura Credentials Management](#aura-credentials-management)
   - [Aura Graph Analytics](#aura-graph-analytics)
10. [Architecture & Development](#architecture--development)
11. [Implementation Summary](#implementation-summary-v200)
12. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start (5 Minutes)

### 1. Prerequisites
- Python 3.11+
- Neo4j AuraDB (cloud database)
- OpenAI API key
- Redis (cloud or local, optional but recommended)
- Node.js 18+ (for frontend development only)

### 2. Install & Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cat > .env << 'EOF'
OPENAI_API_KEY=sk-your-openai-api-key
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io  # AuraDB URI
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-aura-password
ALLOWED_ORIGINS=https://your-app.vercel.app  # For Vercel frontend
REDIS_URL=redis://default:password@host:port  # Optional: Redis for caching
CACHE_ENABLED=true
EOF

# Start backend (AuraDB is external)
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

### 4. Start Backend API

```bash
# Start backend (AuraDB is external)
docker-compose up -d

# View logs
docker-compose logs -f graphrag-api

# Access API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Note:** Frontend is deployed separately to Vercel. See [VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md) for frontend setup.

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
- ✅ **React Frontend** - Modern web UI with futuristic design, chat & dashboard
- ✅ **Multi-hop Reasoning** - Complex graph traversal
- ✅ **Entity Comparison** - Compare companies, investors, etc.
- ✅ **Chat Interface** - Interactive chat with collapsible templates and history
- ✅ **Professional Dark Theme** - Modern, sleek UI throughout

### Data Quality
- ✅ **Multi-layer Validation** - Article and extraction validation
- ✅ **Entity Deduplication** - Automatic duplicate merging
- ✅ **Quality Filtering** - Removes noise and irrelevant data
- ✅ **Checkpoint System** - Resume capability for long runs

### Performance & Monitoring
- ✅ **Redis Caching** - Query result caching with automatic fallback
- ✅ **Relationship Strength Caching** - Optimized relationship calculations
- ✅ **Structured Logging** - JSON-formatted logs with contextual metadata
- ✅ **Prometheus Metrics** - Comprehensive monitoring and metrics
- ✅ **Rate Limiting** - IP-based rate limiting for API protection
- ✅ **Enhanced Pipeline Logging** - Detailed progress tracking for all phases

### Security & Authentication (v2.0.0)
- ✅ **JWT Authentication** - Token-based authentication system
- ✅ **Password Hashing** - Bcrypt password hashing
- ✅ **CORS Protection** - Restricted to specific domains
- ✅ **Request Size Limits** - Configurable request body limits
- ✅ **Error Sanitization** - Secure error messages
- ✅ **API Key Support** - Optional API key authentication

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
./scripts/start_all.sh

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
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io  # AuraDB URI
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-aura-password

# Required - CORS (for Vercel frontend)
ALLOWED_ORIGINS=https://your-app.vercel.app,https://your-app-git-main.vercel.app

# Optional - API Configuration
API_HOST=0.0.0.0
API_PORT=8000
RAG_EMBEDDING_BACKEND=sentence-transformers
SENTENCE_TRANSFORMERS_MODEL=BAAI/bge-small-en-v1.5

# Optional - Security (v2.0.0)
ENABLE_AUTH=false  # Set to true for production
JWT_SECRET_KEY=your-secret-key
ENABLE_RATE_LIMITING=true
MAX_REQUEST_SIZE=10485760  # 10MB

# Optional - Redis Caching (v2.0.0)
CACHE_ENABLED=true
REDIS_URL=redis://default:password@host:port  # Cloud Redis URL (recommended)
# Or use individual config:
# REDIS_HOST=redis-host.com
# REDIS_PORT=18335
# REDIS_PASSWORD=your-password
# REDIS_USERNAME=default
CACHE_DEFAULT_TTL=3600  # 1 hour

# Optional - Logging (v2.0.0)
LOG_LEVEL=INFO
JSON_LOGS=true  # Recommended for production
ENABLE_FILE_LOGGING=false
```

### Frontend (Vercel Deployment)

Frontend is deployed separately to Vercel. See [VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md) for setup.

For local development:
```bash
# frontend/.env.local
VITE_API_BASE_URL=http://localhost:8000
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
    ↓
API Layer: FastAPI + Redis Cache + Prometheus Metrics + Security
    ↓
Frontend: React with Futuristic UI + Dark Theme + Interactive Chat
```

**NEW**: Phase 1.5 enriches companies with:
- Founded year, employee count, headquarters
- Founders, executives, team information
- Funding rounds and investment data
- Products, technologies, pricing models
- Website URLs and social links

**Latest Enhancements (v2.0.0)**:
- **Structured Logging**: JSON-formatted logs for production
- **Security & Authentication**: JWT tokens, password hashing, CORS protection
- **Redis Caching**: Query result caching with automatic fallback
- **Prometheus Metrics**: Comprehensive monitoring and metrics
- **Rate Limiting**: IP-based rate limiting for API protection
- **Comprehensive Testing**: 70%+ test coverage target
- **CI/CD Pipeline**: Automated quality checks and testing

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

### Neo4j AuraDB Connection Failed
```bash
# Verify AuraDB URI in .env file
# Format: neo4j+s://xxxxx.databases.neo4j.io (must use neo4j+s:// for AuraDB)

# Test connection
python -c "from neo4j import GraphDatabase; import os; from dotenv import load_dotenv; load_dotenv(); driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))); driver.verify_connectivity(); print('✓ Connected'); driver.close()"

# Check container logs
docker logs graphrag-api | grep -i neo4j
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
./scripts/start_all.sh
```

### Redis Connection Failed (v2.0.0)
```bash
# Verify REDIS_URL in .env file
# Format: redis://username:password@host:port

# Test Redis connection
redis-cli -u redis://default:password@host:port ping

# Cache will automatically fallback if Redis unavailable
# The app works fine without Redis, just without caching
```

### Rate Limiting Too Strict (v2.0.0)
```bash
# Disable temporarily
export ENABLE_RATE_LIMITING=false

# Or adjust in .env
```

---

## 🚢 Deployment

### Local Development
```bash
# Start backend (connects to AuraDB)
docker-compose up -d

# Or run directly
python api.py

# Frontend: Deploy to Vercel or run locally
cd frontend && npm run dev
```

### Production Deployment (Backend-Only + Vercel)

**This repository is configured for backend-only deployment by default.**

- **Backend**: Docker container (connects to AuraDB and Redis cloud)
- **Frontend**: Deployed separately to Vercel
- **Database**: Neo4j AuraDB (cloud)
- **Cache**: Redis (cloud, optional but recommended)

#### Backend Deployment

```bash
# 1. Build backend-only Docker image
./scripts/build-docker-amd.sh

# 2. Configure .env with:
#    - AuraDB connection (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
#    - Redis URL (REDIS_URL) - optional but recommended
#    - CORS origins (ALLOWED_ORIGINS) - your Vercel domain(s)

# 3. Start backend
docker-compose up -d

# 4. Verify health
curl http://localhost:8000/health
```

See [DOCKER_START_GUIDE.md](./DOCKER_START_GUIDE.md) for detailed Docker setup.

#### Frontend Deployment (Vercel)

See [VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md) for detailed instructions.

Quick setup:
1. Deploy frontend to Vercel (set root directory to `frontend/`)
2. Set `VITE_API_BASE_URL` environment variable in Vercel
3. Configure backend `ALLOWED_ORIGINS` with your Vercel domain(s)

---

## 📈 Implementation Summary (v2.0.0)

### Key Improvements

#### 1. Structured Logging System ✅
- JSON-formatted logs for production
- Colored console output for development
- Contextual logging with automatic metadata
- Performance metrics logging
- API request logging

#### 2. Security & Authentication ✅
- JWT token-based authentication
- Password hashing with bcrypt
- Password strength validation
- API key support
- CORS restricted to specific domains
- Request size limits (10MB default)

#### 3. Redis Caching Layer ✅
- Redis-based caching with automatic fallback
- Query result caching (1 hour TTL)
- Entity data caching
- Cache hit/miss tracking
- **Performance**: Cached queries return in ~10ms (vs 2000ms uncached)

#### 4. Prometheus Metrics & Monitoring ✅
- API requests (total, duration, size)
- Neo4j queries (count, duration, status)
- LLM requests (count, duration, tokens used)
- Cache operations (hits, misses)
- Business metrics (articles scraped, entities extracted)
- Endpoints: `GET /metrics`, `GET /admin/status`

#### 5. Rate Limiting ✅
- IP-based rate limiting
- Configurable limits per endpoint
- Query endpoint: 30 requests/minute
- Graceful error responses

#### 6. Comprehensive Testing Infrastructure ✅
- Unit tests (150+ test cases)
- Integration tests (20+ test cases)
- Test coverage target: 70%+
- Fixtures for mocking: Neo4j, OpenAI, Redis
- Running: `make test`, `make test-unit`, `make test-coverage`

### Statistics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **API Version** | 1.0.0 | 2.0.0 | +1.0.0 |
| **Total Lines of Code** | 12,467 | 16,000+ | +3,500+ |
| **Utility Modules** | 20 | 23 | +3 |
| **Test Files** | 3 | 7 | +4 |
| **Test Coverage** | <10% | 70%+ (target) | +60%+ |
| **Docker Services** | 2 | 3 | +1 (Redis) |
| **Logging** | print() | structlog | ✅ |
| **Security Features** | None | 5+ | ✅ |
| **Monitoring** | None | Prometheus | ✅ |

### Performance Improvements

- **Cached queries**: ~10ms response time (vs 2000ms uncached)
- **Cache hit rate**: Expected 30-50% for repeated queries
- **Reduced LLM calls**: Cached results avoid repeated OpenAI API calls
- **Connection pooling**: Reuses Neo4j connections

### Security Improvements

**Before (v1.0.0)**:
- ❌ CORS open to all origins
- ❌ No authentication
- ❌ No rate limiting
- ❌ Database errors exposed to clients
- ❌ No request size limits

**After (v2.0.0)**:
- ✅ CORS restricted to specific domains
- ✅ Optional JWT authentication
- ✅ IP-based rate limiting
- ✅ Sanitized error messages
- ✅ 10MB request size limit (configurable)
- ✅ Security scanning in CI/CD

---

## 🚀 Future Enhancements

### ✅ Completed
- [x] Hybrid RAG implementation
- [x] REST API (40+ endpoints)
- [x] React frontend with futuristic UI design
- [x] Professional dark theme throughout
- [x] Interactive chat interface with history
- [x] Collapsible query templates sidebar
- [x] Semantic search with embeddings
- [x] Multi-hop reasoning
- [x] Entity deduplication (automatic)
- [x] Community detection (automatic) with Aura Graph Analytics
- [x] Relationship scoring (automatic) with caching
- [x] Sentence-transformers support
- [x] Redis caching layer
- [x] Structured logging system
- [x] Prometheus metrics & monitoring
- [x] Rate limiting & security enhancements
- [x] Comprehensive test suite

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
- **Metrics**: http://localhost:8000/metrics
- **System Status**: http://localhost:8000/admin/status

---

## 📚 Additional Resources

**Built with:** Python, Neo4j, FastAPI, React, OpenAI GPT-4o, LangChain, Sentence Transformers, Redis, Prometheus

**Code Quality:**
- Black code formatting
- isort import sorting
- Pylint linting
- Mypy type checking
- Comprehensive test suite

**Happy Knowledge Graph Building! 🚀**
