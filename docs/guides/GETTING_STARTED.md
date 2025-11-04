# Getting Started with GraphRAG System

This guide will help you get your GraphRAG system up and running quickly.

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment

Create a `.env` file:

```bash
# Required
OPENAI_API_KEY=sk-your-openai-key
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password

# Optional (API Configuration)
API_HOST=0.0.0.0
API_PORT=8000
```

### Step 3: Verify Neo4j is Running

```bash
# Check Neo4j status
systemctl status neo4j

# Or visit Neo4j Browser
open http://localhost:7474
```

### Step 4: Run the Pipeline (If Starting Fresh)

If you haven't built the graph yet:

```bash
python pipeline.py \
  --articles-dir data/articles \
  --output-dir data/processing \
  --advanced-features
```

This will:
- Extract entities and relationships from articles
- Build Neo4j knowledge graph
- Generate embeddings
- Detect communities
- Score relationships

**Note:** Skip this if you already have a populated graph.

### Step 5: Start the GraphRAG API

```bash
python api.py
```

You should see:

```
🚀 Starting GraphRAG API on 0.0.0.0:8000
📚 API Documentation: http://0.0.0.0:8000/docs
📊 ReDoc Documentation: http://0.0.0.0:8000/redoc
```

### Step 6: Test the API

Open your browser and visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Or test with curl:

```bash
# Health check
curl http://localhost:8000/health

# Ask a question
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What AI startups raised funding?"}'
```

### Step 7: Try the Python Client

```bash
python api_client_example.py
```

This runs 10 example queries demonstrating the API capabilities.

---

## 📖 What Can You Do Now?

### 1. Natural Language Queries

Ask questions in plain English:

```python
from api_client_example import GraphRAGClient

client = GraphRAGClient()
result = client.query("Tell me about AI startups that raised funding")
print(result['answer'])
```

### 2. Semantic Search

Find similar entities using vector embeddings:

```python
results = client.semantic_search("artificial intelligence", top_k=5)
for entity in results['results']:
    print(f"{entity['name']}: {entity['similarity']:.3f}")
```

### 3. Company Research

Get comprehensive company profiles:

```python
profile = client.get_company_profile("Anthropic")
print(f"Founders: {', '.join(profile['founders'])}")
print(f"Investors: {len(profile['investors'])} investors")

landscape = client.get_competitive_landscape("Anthropic")
print(f"Competitors: {landscape['direct_competitors']}")
```

### 4. Investor Analysis

Analyze investor portfolios:

```python
portfolio = client.get_investor_portfolio("Sequoia Capital")
print(f"Portfolio: {portfolio['portfolio_size']} companies")

top_investors = client.get_top_investors(limit=10)
for inv in top_investors['results']:
    print(f"{inv['name']}: {inv['portfolio_size']} investments")
```

### 5. Technology Trends

Discover trending technologies:

```python
tech = client.get_trending_technologies(limit=10)
for t in tech['results']:
    print(f"{t['name']}: {t['company_count']} companies")
```

### 6. Entity Comparison

Compare two entities:

```python
comparison = client.compare_entities("OpenAI", "Anthropic")
print(comparison['comparison'])
```

### 7. Multi-hop Reasoning

Ask complex questions requiring graph traversal:

```python
result = client.multi_hop_reasoning(
    "What technologies are used by companies funded by top investors?",
    max_hops=3
)
print(result['answer'])
```

### 8. Graph Analytics

Get insights from graph structure:

```python
stats = client.get_statistics()
print(f"Total nodes: {sum(c['count'] for c in stats['node_counts'])}")

importance = client.get_importance_scores(limit=10)
for entity in importance['results']:
    print(f"{entity['name']}: {entity['importance_score']}")
```

---

## 🔧 Common Use Cases

### Use Case 1: Competitive Intelligence

```python
from api_client_example import GraphRAGClient

client = GraphRAGClient()

# Get company profile
company = "YourTargetCompany"
profile = client.get_company_profile(company)

# Get competitors
landscape = client.get_competitive_landscape(company)
print(f"Direct competitors: {landscape['direct_competitors']}")
print(f"Similar companies: {landscape['similar_companies']}")

# Compare with main competitor
if landscape['direct_competitors']:
    competitor = landscape['direct_competitors'][0]
    comparison = client.compare_entities(company, competitor)
    print(comparison['comparison'])
```

### Use Case 2: Investment Research

```python
# Find companies in AI sector
companies = client.get_companies_by_sector("artificial intelligence")

# Get funding information
funded = client.get_funded_companies(min_investors=2)

# Analyze investor activity
top_investors = client.get_top_investors(limit=5)
for inv in top_investors['results']:
    portfolio = client.get_investor_portfolio(inv['name'])
    print(f"{inv['name']} invested in: {', '.join(portfolio['portfolio'][:5])}")
```

### Use Case 3: Market Trend Analysis

```python
# Get trending technologies
tech_trends = client.get_trending_technologies(limit=10)

# Get AI insights
insights = client.get_insights("artificial intelligence trends")
print(insights['insights'])

# Recent activity
recent = client._get("/recent-entities", {"days": 30, "limit": 10})
print("Recently mentioned:", [e['name'] for e in recent['results']])
```

### Use Case 4: Relationship Discovery

```python
# Find connections between entities
paths = client._get("/connection-path", {
    "entity1": "Anthropic",
    "entity2": "Google",
    "max_hops": 4
})

for path in paths['paths']:
    print(f"Path length: {path['path_length']}")
    nodes = [n['name'] for n in path['nodes']]
    print(" → ".join(nodes))
```

---

## 🛠️ Advanced Configuration

### Using Local Embeddings

If you don't want to use OpenAI embeddings, use Sentence Transformers:

```python
from rag_query import GraphRAGQuery

rag = GraphRAGQuery(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password",
    embedding_model="sentence_transformers"  # Local model
)
```

### Custom API Port

Change the API port in `.env`:

```bash
API_PORT=9000
```

Or when running:

```bash
export API_PORT=9000
python api.py
```

### Running in Production

For production deployment:

1. **Use a production WSGI server:**

```bash
pip install gunicorn
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

2. **Enable HTTPS:**

```python
# In api.py, add SSL configuration
uvicorn.run(
    "api:app",
    host="0.0.0.0",
    port=8000,
    ssl_keyfile="/path/to/key.pem",
    ssl_certfile="/path/to/cert.pem"
)
```

3. **Add authentication:**

```python
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/query")
async def query(request: QueryRequest, credentials = Security(security)):
    # Verify token
    if not verify_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
    # ... rest of endpoint
```

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "api.py"]
```

Build and run:

```bash
docker build -t graphrag-api .
docker run -p 8000:8000 --env-file .env graphrag-api
```

---

## 📚 Next Steps

1. **Read Full Documentation**: See `RAG_DOCUMENTATION.md` for complete API reference
2. **Explore Examples**: Run `python api_client_example.py` for more examples
3. **Customize Queries**: Add custom Cypher queries to `query_templates.py`
4. **Build Applications**: Use the API to build custom tools and dashboards
5. **Optimize Performance**: See performance tips in documentation

---

## 🐛 Troubleshooting

### API Won't Start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
pip install fastapi uvicorn
```

### No Embeddings Found

**Error:** Semantic search returns empty results

**Solution:**
```bash
python integrate_new_features.py
# Or run embeddings generation
python -c "
from utils.embedding_generator import EmbeddingGenerator
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
embedder = EmbeddingGenerator(driver, 'openai')
embedder.generate_embeddings_for_all_entities()
driver.close()
"
```

### Neo4j Connection Failed

**Error:** `ServiceUnavailable: Unable to retrieve routing information`

**Solution:**
1. Check Neo4j is running: `systemctl status neo4j`
2. Verify credentials in `.env`
3. Test connection: `cypher-shell -u neo4j -p password`

### LLM Generation Not Working

**Error:** `LLM not initialized`

**Solution:**
1. Check `.env` has valid `OPENAI_API_KEY`
2. Verify API key: `echo $OPENAI_API_KEY`
3. Test API key: `curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`

### Slow Queries

**Solution:**
1. Reduce `max_hops` parameter (use 1-2 instead of 3-4)
2. Limit result sizes with `top_k` or `limit`
3. Check Neo4j indexes exist
4. Consider caching frequent queries

---

## 💡 Tips & Best Practices

### 1. Use Semantic Search for Entity Discovery

Instead of exact name matching:

```python
# ❌ Might fail if name doesn't match exactly
profile = client.get_company_profile("anthropic")  # Wrong case

# ✅ Use semantic search first
results = client.semantic_search("anthropic", top_k=1, entity_type="Company")
if results['results']:
    company_name = results['results'][0]['name']
    profile = client.get_company_profile(company_name)
```

### 2. Cache Frequent Queries

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_profile(company_name: str):
    return client.get_company_profile(company_name)
```

### 3. Use Batch Queries

```python
# ❌ Slow: Multiple requests
results = []
for q in questions:
    results.append(client.query(q))

# ✅ Fast: Single batch request
results = client.batch_query(questions)
```

### 4. Combine Search Methods

```python
# Hybrid search combines semantic + keyword matching
results = client.hybrid_search(
    "fintech startup",
    top_k=10,
    semantic_weight=0.7  # 70% semantic, 30% keyword
)
```

### 5. Limit Relationship Hops

```python
# ❌ Slow: Deep traversal
context = rag.get_entity_context(entity_id, max_hops=5)

# ✅ Fast: Shallow traversal
context = rag.get_entity_context(entity_id, max_hops=1)
```

---

## 🎯 Example Workflows

### Workflow 1: Research a Company

```python
client = GraphRAGClient()

# 1. Find company
results = client.semantic_search("anthropic", entity_type="Company")
company = results['results'][0]['name']

# 2. Get profile
profile = client.get_company_profile(company)
print(f"Company: {profile['name']}")
print(f"Founders: {profile['founders']}")
print(f"Investors: {len(profile['investors'])} investors")

# 3. Get competitive landscape
landscape = client.get_competitive_landscape(company)
print(f"Competitors: {landscape['direct_competitors']}")

# 4. Compare with competitor
if landscape['direct_competitors']:
    comp = landscape['direct_competitors'][0]
    comparison = client.compare_entities(company, comp)
    print(comparison['comparison'])
```

### Workflow 2: Analyze Investor

```python
# 1. Find investor
results = client.semantic_search("sequoia", entity_type="Investor")
investor = results['results'][0]['name']

# 2. Get portfolio
portfolio = client.get_investor_portfolio(investor)
print(f"Portfolio: {portfolio['portfolio_size']} companies")

# 3. Analyze investments by sector
for company in portfolio['portfolio']:
    # Check what sector each company is in
    profile = client.get_company_profile(company['name'])
    print(f"{company['name']}: {profile.get('description', '')[:100]}")
```

### Workflow 3: Discover Trends

```python
# 1. Get trending technologies
tech = client.get_trending_technologies(limit=10)

# 2. For each technology, get adoption
for t in tech['results'][:3]:
    adoption = client.get_technology_adoption(t['name'])
    print(f"{t['name']}: {adoption['adoption_count']} companies")
    print(f"  Companies: {', '.join(adoption['companies'][:5])}")

# 3. Get AI insights
insights = client.get_insights("technology trends in AI")
print(insights['insights'])
```

---

## 📞 Support Resources

- **Documentation**: `RAG_DOCUMENTATION.md`
- **API Reference**: http://localhost:8000/docs (when server is running)
- **Example Code**: `api_client_example.py`
- **Source Code**: Browse the Python files with comments

---

**You're all set! Start querying your knowledge graph! 🎉**
