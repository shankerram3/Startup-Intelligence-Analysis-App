# GraphRAG System Documentation

Complete documentation for the TechCrunch Knowledge Graph RAG (Retrieval Augmented Generation) system.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Installation](#installation)
5. [Quick Start](#quick-start)
6. [API Reference](#api-reference)
7. [Usage Examples](#usage-examples)
8. [Advanced Features](#advanced-features)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The GraphRAG system is a complete Retrieval Augmented Generation pipeline built on top of a Neo4j knowledge graph. It combines:

- **Semantic Search**: Vector embeddings for similarity-based entity retrieval
- **Graph Traversal**: Cypher queries for relationship exploration
- **LLM Generation**: GPT-4o for natural language answer generation
- **REST API**: FastAPI endpoints for easy integration

### What Can You Do?

- Ask natural language questions about startups, investors, and technology
- Explore company profiles with funding, founders, and competitors
- Find connections between entities using graph traversal
- Analyze trends and patterns in the startup ecosystem
- Compare companies and discover competitive landscapes
- Get AI-generated insights from knowledge graph data

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       User Interface                         │
│              (HTTP Requests / Python Client)                 │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI REST API                          │
│                        (api.py)                              │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   GraphRAG Query Layer                       │
│                     (rag_query.py)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Semantic   │  │    Query     │  │     LLM      │     │
│  │    Search    │  │   Routing    │  │  Generation  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
           ▼                    ▼                    ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐
│    Embeddings    │  │ Query Templates  │  │   OpenAI     │
│    Generator     │  │  (Cypher)        │  │   GPT-4o     │
│  (embeddings)    │  │(query_templates) │  │              │
└──────────────────┘  └──────────────────┘  └──────────────┘
           ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                   Neo4j Knowledge Graph                      │
│            (Entities, Relationships, Communities)            │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Query** → FastAPI endpoint
2. **Intent Classification** → Determine query type
3. **Query Routing** → Route to appropriate handler
4. **Semantic Search** → Find relevant entities using embeddings
5. **Graph Traversal** → Get context via Cypher queries
6. **Context Aggregation** → Combine entity + relationship data
7. **LLM Generation** → Generate natural language answer
8. **Response** → Return formatted result to user

---

## Components

### 1. **rag_query.py** - GraphRAG Query Module

Main RAG interface combining semantic search, graph traversal, and LLM generation.

**Key Classes:**
- `GraphRAGQuery`: Main query interface
  - `query()`: Natural language question answering
  - `semantic_search()`: Vector similarity search
  - `hybrid_search()`: Combined semantic + keyword search
  - `multi_hop_reasoning()`: Multi-hop graph traversal
  - `compare_entities()`: Entity comparison
  - `get_insights()`: AI-generated insights

### 2. **query_templates.py** - Cypher Query Library

Pre-built Cypher query templates for common patterns.

**Query Categories:**
- Entity queries (get by name/ID/type)
- Company queries (profile, funding, sector)
- Investor queries (portfolio, top investors)
- Person queries (profile, affiliations)
- Relationship queries (connections, paths)
- Community queries (detection results)
- Analytics queries (statistics, importance scores)
- Technology queries (adoption, trends)
- Temporal queries (recent entities, timelines)

### 3. **api.py** - REST API

FastAPI server exposing HTTP endpoints.

**Endpoint Categories:**
- `/query` - Natural language queries
- `/search` - Semantic/hybrid/fulltext search
- `/entity` - Entity operations
- `/company` - Company information
- `/investor` - Investor portfolios
- `/person` - Person profiles
- `/relationships` - Graph traversal
- `/community` - Community detection results
- `/analytics` - Graph analytics
- `/technology` - Technology trends
- `/temporal` - Time-based queries

### 4. **utils/embedding_generator.py** - Vector Embeddings

Generates and stores vector embeddings for entities.

**Features:**
- OpenAI embeddings (text-embedding-3-small)
- Sentence Transformers (local model)
- Cosine similarity search
- Batch embedding generation

---

## Installation

### Prerequisites

- Python 3.8+
- Neo4j 5.0+ (running instance)
- OpenAI API key (for embeddings and LLM)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Environment Setup

Create `.env` file:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key

# API Configuration (optional)
API_HOST=0.0.0.0
API_PORT=8000
```

### Generate Embeddings (First Time)

Before using semantic search, generate embeddings:

```python
from utils.embedding_generator import EmbeddingGenerator
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
embedder = EmbeddingGenerator(driver, embedding_model="openai")
stats = embedder.generate_embeddings_for_all_entities()
print(f"Generated {stats['generated']} embeddings")
driver.close()
```

Or use the integration script:
```bash
python integrate_new_features.py
```

---

## Quick Start

### Option 1: Python Client

```python
from rag_query import create_rag_query

# Create RAG instance
rag = create_rag_query()

# Ask a question
result = rag.query("What AI startups have raised funding?")
print(result['answer'])

# Semantic search
entities = rag.semantic_search("artificial intelligence", top_k=5)
for entity in entities:
    print(f"{entity['name']}: {entity['similarity']:.3f}")

# Company profile
profile = rag.query_templates.get_company_profile("Anthropic")
print(f"Founders: {profile['founders']}")
print(f"Investors: {profile['investors']}")

# Close connection
rag.close()
```

### Option 2: REST API

**Start the API server:**

```bash
python api.py
```

**Access documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Make requests:**

```bash
# Natural language query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the top AI startups?", "use_llm": true}'

# Semantic search
curl -X POST "http://localhost:8000/search/semantic" \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "top_k": 5, "entity_type": "Company"}'

# Company profile
curl "http://localhost:8000/company/Anthropic"

# Top investors
curl "http://localhost:8000/investors/top?limit=10"
```

### Option 3: Python API Client

```python
from api_client_example import GraphRAGClient

client = GraphRAGClient("http://localhost:8000")

# Natural language query
result = client.query("Tell me about AI startups")
print(result['answer'])

# Semantic search
results = client.semantic_search("blockchain", top_k=5)

# Company comparison
comparison = client.compare_entities("OpenAI", "Anthropic")
print(comparison['comparison'])

# Get insights
insights = client.get_insights("artificial intelligence")
print(insights['insights'])
```

---

## API Reference

### Query Endpoints

#### POST /query
Natural language question answering

**Request:**
```json
{
  "question": "What AI companies raised Series A funding?",
  "return_context": false,
  "use_llm": true
}
```

**Response:**
```json
{
  "question": "What AI companies raised Series A funding?",
  "intent": {"intent": "funding_info", "confidence": 0.9},
  "answer": "Based on the knowledge graph, several AI companies...",
  "context": {...}  // if return_context=true
}
```

#### POST /query/batch
Process multiple queries at once

**Request:**
```json
{
  "questions": [
    "What is Anthropic?",
    "Who are the top investors?",
    "What technologies are trending?"
  ]
}
```

#### POST /query/multi-hop
Multi-hop reasoning across graph

**Request:**
```json
{
  "question": "What technologies are used by companies funded by Sequoia?",
  "max_hops": 3
}
```

### Search Endpoints

#### POST /search/semantic
Semantic search using embeddings

**Request:**
```json
{
  "query": "artificial intelligence",
  "top_k": 10,
  "entity_type": "Company"
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "abc123",
      "name": "Anthropic",
      "type": "Company",
      "description": "AI safety startup...",
      "similarity": 0.89
    }
  ],
  "count": 10
}
```

#### POST /search/hybrid
Combine semantic + keyword search

**Request:**
```json
{
  "query": "fintech startup",
  "top_k": 10,
  "semantic_weight": 0.7
}
```

#### GET /search/fulltext
Full-text search in names and descriptions

**Query Params:**
- `query`: Search term
- `limit`: Max results (default: 10)

### Entity Endpoints

#### GET /entity/{entity_id}
Get entity by ID

**Query Params:**
- `include_relationships`: Include related entities (default: false)

#### GET /entity/name/{entity_name}
Get entity by name

**Query Params:**
- `entity_type`: Filter by type (optional)

#### POST /entity/compare
Compare two entities

**Request:**
```json
{
  "entity1": "Anthropic",
  "entity2": "OpenAI"
}
```

### Company Endpoints

#### GET /company/{company_name}
Get comprehensive company profile

**Response:**
```json
{
  "id": "abc123",
  "name": "Anthropic",
  "description": "AI safety startup...",
  "mention_count": 15,
  "investors": [{"name": "Spark Capital", "type": "FUNDED_BY"}],
  "founders": ["Dario Amodei", "Daniela Amodei"],
  "technologies": [...],
  "locations": ["San Francisco"],
  "competitors": ["OpenAI"]
}
```

#### GET /companies/funded
Get funded companies

**Query Params:**
- `min_investors`: Minimum number of investors (default: 1)

#### GET /companies/sector/{sector}
Get companies in sector

**Example:** `/companies/sector/ai`

#### GET /company/{company_name}/competitive-landscape
Get competitive landscape

**Response:**
```json
{
  "company": "Anthropic",
  "description": "...",
  "direct_competitors": ["OpenAI"],
  "similar_companies": ["Cohere", "Adept"],
  "companies_with_shared_investors": [...]
}
```

### Investor Endpoints

#### GET /investor/{investor_name}/portfolio
Get investor portfolio

**Response:**
```json
{
  "id": "inv123",
  "name": "Sequoia Capital",
  "description": "...",
  "portfolio_size": 25,
  "portfolio": [
    {"name": "Anthropic", "description": "...", "mention_count": 15},
    ...
  ]
}
```

#### GET /investors/top
Get most active investors

**Query Params:**
- `limit`: Max results (default: 10)

### Relationship Endpoints

#### GET /relationships/{entity_id}
Get entity's relationship network

**Query Params:**
- `max_hops`: Relationship depth (1-3, default: 2)

#### GET /connection-path
Find shortest path between entities

**Query Params:**
- `entity1`: First entity name
- `entity2`: Second entity name
- `max_hops`: Max path length (1-6, default: 4)

**Response:**
```json
{
  "entity1": "Anthropic",
  "entity2": "Google",
  "paths": [
    {
      "nodes": [
        {"name": "Anthropic", "type": "Company"},
        {"name": "Dario Amodei", "type": "Person"},
        {"name": "Google", "type": "Company"}
      ],
      "relationships": [
        {"type": "FOUNDED_BY", "strength": 10},
        {"type": "WORKS_AT", "strength": 8}
      ],
      "path_length": 2
    }
  ],
  "count": 1
}
```

### Analytics Endpoints

#### GET /analytics/statistics
Get graph statistics

**Response:**
```json
{
  "node_counts": [
    {"label": "Company", "count": 150},
    {"label": "Person", "count": 200},
    {"label": "Investor", "count": 80}
  ],
  "relationship_counts": [
    {"type": "FUNDED_BY", "count": 300},
    {"type": "FOUNDED_BY", "count": 180}
  ],
  "community_count": 15
}
```

#### GET /analytics/most-connected
Get most connected entities

#### GET /analytics/importance
Get entity importance scores

**Response:**
```json
{
  "results": [
    {
      "id": "abc123",
      "name": "OpenAI",
      "type": "Company",
      "mentions": 50,
      "relationships": 25,
      "articles": 30,
      "importance_score": 35.5
    }
  ]
}
```

#### GET /analytics/insights/{topic}
Get AI-generated insights

**Example:** `/analytics/insights/artificial%20intelligence`

### Technology Endpoints

#### GET /technologies/trending
Get trending technologies

#### GET /technology/{technology_name}
Get technology adoption

**Response:**
```json
{
  "technology": "GPT",
  "description": "...",
  "adoption_count": 15,
  "companies": ["OpenAI", "Anthropic", ...]
}
```

---

## Usage Examples

### Example 1: Company Research

```python
from rag_query import create_rag_query

rag = create_rag_query()

# Get company profile
profile = rag.query_templates.get_company_profile("Anthropic")
print(f"Company: {profile['name']}")
print(f"Founders: {', '.join(profile['founders'])}")
print(f"Investors: {len(profile['investors'])} investors")

# Get competitive landscape
landscape = rag.query_templates.get_competitive_landscape("Anthropic")
print(f"Competitors: {landscape['direct_competitors']}")
print(f"Similar companies: {landscape['similar_companies']}")

# Ask natural language question
result = rag.query("What makes Anthropic different from its competitors?")
print(result['answer'])

rag.close()
```

### Example 2: Investor Analysis

```python
from rag_query import create_rag_query

rag = create_rag_query()

# Get top investors
investors = rag.query_templates.get_top_investors(limit=10)
for inv in investors:
    print(f"{inv['name']}: {inv['portfolio_size']} companies")

# Get specific investor portfolio
portfolio = rag.query_templates.get_investor_portfolio("Sequoia Capital")
print(f"Portfolio size: {portfolio['portfolio_size']}")
for company in portfolio['portfolio'][:5]:
    print(f"  - {company['name']}")

# Ask about investment patterns
result = rag.query("What sectors does Sequoia Capital focus on?")
print(result['answer'])

rag.close()
```

### Example 3: Technology Trends

```python
from rag_query import create_rag_query

rag = create_rag_query()

# Get trending technologies
tech = rag.query_templates.get_trending_technologies(limit=10)
for t in tech:
    print(f"{t['name']}: {t['company_count']} companies")

# Get technology adoption
adoption = rag.query_templates.get_technology_adoption("AI")
print(f"Companies using AI: {adoption['adoption_count']}")

# Get AI insights
insights = rag.get_insights("artificial intelligence trends")
print(insights['insights'])

rag.close()
```

### Example 4: Relationship Exploration

```python
from rag_query import create_rag_query

rag = create_rag_query()

# Find connection between entities
paths = rag.query_templates.find_connection_path("Anthropic", "Google", max_hops=4)
for path in paths:
    print(f"Path length: {path['path_length']}")
    for node in path['nodes']:
        print(f"  {node['name']} ({node['type']})")

# Get entity relationships
context = rag.get_entity_context("entity_id_here", max_hops=2)
print(f"Entity: {context['name']}")
print(f"Related entities: {len(context['related_entities'])}")

rag.close()
```

### Example 5: Multi-hop Reasoning

```python
from rag_query import create_rag_query

rag = create_rag_query()

# Complex question requiring graph traversal
result = rag.multi_hop_reasoning(
    "What technologies are used by companies founded by former Google employees?",
    max_hops=3
)

print(f"Starting entity: {result['starting_entity']['name']}")
print(f"Answer: {result['answer']}")

rag.close()
```

---

## Advanced Features

### Custom Query Intent Classification

You can extend intent classification in `rag_query.py`:

```python
def classify_query_intent(self, query: str) -> Dict:
    query_lower = query.lower()

    # Add custom intent
    if "acquisition" in query_lower:
        return {"intent": "acquisition_info", "confidence": 0.9}

    # ... rest of classification logic
```

### Custom Cypher Queries

Add new query templates to `query_templates.py`:

```python
def get_acquisition_timeline(self) -> List[Dict]:
    """Get company acquisitions"""
    with self.driver.session() as session:
        result = session.run("""
            MATCH (c1:Company)-[r:ACQUIRED]->(c2:Company)
            RETURN c1.name as acquirer, c2.name as acquired,
                   r.date as date
            ORDER BY r.date DESC
        """)
        return [dict(record) for record in result]
```

### Batch Processing

Process multiple queries efficiently:

```python
questions = [
    "What is Anthropic?",
    "Who are the top investors?",
    "What technologies are trending?"
]

results = rag.batch_query(questions)
for result in results:
    print(f"Q: {result['question']}")
    print(f"A: {result['answer']}\n")
```

### Context-Aware Generation

Customize LLM prompts for specific use cases:

```python
def generate_investment_advice(self, company_name: str) -> str:
    """Generate investment analysis"""
    profile = self.query_templates.get_company_profile(company_name)
    landscape = self.query_templates.get_competitive_landscape(company_name)

    context = {
        "profile": profile,
        "landscape": landscape
    }

    prompt = f"""Analyze this company for investment potential:
    {json.dumps(context, indent=2)}

    Provide:
    1. Market position
    2. Competitive advantages
    3. Investment risks
    4. Recommendation
    """

    return self.llm.invoke(prompt).content
```

---

## Troubleshooting

### Embeddings Not Working

**Problem:** Semantic search returns no results

**Solutions:**
1. Generate embeddings: `python integrate_new_features.py`
2. Check OpenAI API key in `.env`
3. Verify embeddings are stored: Run `MATCH (e) WHERE e.embedding IS NOT NULL RETURN count(e)` in Neo4j

### API Connection Errors

**Problem:** `ConnectionError: Could not connect to API`

**Solutions:**
1. Start API server: `python api.py`
2. Check API is running: `curl http://localhost:8000/health`
3. Verify port 8000 is not in use: `lsof -i :8000`

### Neo4j Connection Issues

**Problem:** `Neo4j connection failed`

**Solutions:**
1. Verify Neo4j is running: `systemctl status neo4j`
2. Check credentials in `.env`
3. Test connection: `cypher-shell -u neo4j -p password`

### LLM Generation Errors

**Problem:** `LLM not initialized` or `OpenAI API error`

**Solutions:**
1. Check OpenAI API key: `echo $OPENAI_API_KEY`
2. Verify API key has credits
3. Check rate limits: https://platform.openai.com/account/rate-limits

### Slow Queries

**Problem:** Queries take too long

**Solutions:**
1. Check Neo4j indexes: `SHOW INDEXES`
2. Reduce `max_hops` parameter (use 1-2 instead of 3-4)
3. Limit result size with `top_k` or `limit`
4. Consider caching frequent queries

### Empty Results

**Problem:** Queries return no results

**Solutions:**
1. Check graph has data: `MATCH (n) RETURN count(n)`
2. Verify entity names: `MATCH (c:Company) RETURN c.name LIMIT 10`
3. Use semantic search instead of exact name matching
4. Check query spelling and formatting

---

## Performance Tips

### 1. Use Indexes
Ensure Neo4j indexes exist:
```cypher
CREATE INDEX IF NOT EXISTS FOR (c:Company) ON (c.name);
CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.name);
```

### 2. Limit Hops
Keep relationship hops low (1-2) for better performance:
```python
context = rag.get_entity_context(entity_id, max_hops=1)  # Fast
context = rag.get_entity_context(entity_id, max_hops=4)  # Slow
```

### 3. Cache Results
Cache frequent queries:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_company_profile(company_name: str):
    return rag.query_templates.get_company_profile(company_name)
```

### 4. Use Batch Operations
Process multiple queries at once:
```python
# Slow: Multiple round trips
results = [rag.query(q) for q in questions]

# Fast: Single batch request
results = rag.batch_query(questions)
```

### 5. Optimize Embeddings
Use local models for faster embedding generation:
```python
# OpenAI: Slower but better quality
embedder = EmbeddingGenerator(driver, "openai")

# Sentence Transformers: Faster, local
embedder = EmbeddingGenerator(driver, "sentence_transformers")
```

---

## Next Steps

1. **Explore the API**: Try different endpoints at http://localhost:8000/docs
2. **Run Examples**: Execute `python api_client_example.py`
3. **Build Applications**: Use the API client to build custom tools
4. **Extend Queries**: Add custom Cypher queries for your use case
5. **Deploy**: Deploy API with Docker/Kubernetes for production

---

## Support

For issues and questions:
- Check documentation above
- Review code comments in source files
- Test with example scripts
- Verify environment configuration

---

**Built with:** Neo4j, OpenAI GPT-4o, FastAPI, LangChain, Sentence Transformers
