# Query Examples

Common query patterns and use cases for the GraphRAG API.

---

## Natural Language Queries

### Company Research

```python
from rag_query import create_rag_query

rag = create_rag_query()

# Basic company information
result = rag.query("Tell me about Anthropic")
print(result['answer'])

# Funding information
result = rag.query("Which companies raised funding recently?")
print(result['answer'])

# Technology focus
result = rag.query("What AI startups are working on large language models?")
print(result['answer'])
```

### Investment Research

```python
# Investor analysis
result = rag.query("What companies has Sequoia Capital invested in?")
print(result['answer'])

# Funding trends
result = rag.query("Which sectors received the most funding in 2024?")
print(result['answer'])

# Top investors
result = rag.query("Who are the most active AI investors?")
print(result['answer'])
```

### Market Intelligence

```python
# Competitive landscape
result = rag.query("Who are Anthropic's main competitors?")
print(result['answer'])

# Technology trends
result = rag.query("What emerging technologies are gaining traction?")
print(result['answer'])

# Recent developments
result = rag.query("What happened in the AI space last week?")
print(result['answer'])
```

---

## Semantic Search

### Find Similar Entities

```python
# Find AI companies
results = rag.semantic_search("artificial intelligence startups", top_k=10)
for entity in results:
    print(f"{entity['name']} ({entity['type']}): {entity['similarity']:.3f}")

# Find investors
results = rag.semantic_search("venture capital firms", top_k=5, entity_type="Investor")
for entity in results:
    print(f"{entity['name']}: {entity['description']}")

# Find technologies
results = rag.semantic_search("machine learning frameworks", top_k=10, entity_type="Technology")
for entity in results:
    print(entity['name'])
```

---

## Structured Queries

### Company Profile

```python
# Get complete company profile
profile = rag.get_company_profile("Anthropic")

print(f"Name: {profile['name']}")
print(f"Description: {profile['description']}")
print(f"Founders: {', '.join(profile['founders'])}")
print(f"Investors: {', '.join(profile['investors'])}")
print(f"Technologies: {', '.join(profile['technologies'])}")
print(f"Competitors: {', '.join(profile['competitors'])}")
```

### Investor Portfolio

```python
# Get investor portfolio
portfolio = rag.get_investor_portfolio("Sequoia Capital")

print(f"Portfolio Size: {portfolio['portfolio_size']}")
print(f"Companies:")
for company in portfolio['portfolio']:
    print(f"  - {company['name']}: {company['description']}")
```

### Competitive Landscape

```python
# Analyze competitive landscape
landscape = rag.get_competitive_landscape("OpenAI")

print(f"Direct Competitors: {landscape['direct_competitors']}")
print(f"Similar Companies: {landscape['similar_companies']}")
print(f"Market Position: {landscape['market_position']}")
```

---

## Multi-Hop Reasoning

### Complex Queries

```python
# Multi-hop query with graph traversal
result = rag.multi_hop_reasoning(
    "What technologies are used by companies funded by Sequoia Capital?",
    max_hops=3
)
print(result['answer'])
print(f"Reasoning path: {result['reasoning_path']}")

# Investment network
result = rag.multi_hop_reasoning(
    "Which investors co-invested with Andreessen Horowitz?",
    max_hops=2
)
print(result['answer'])
```

---

## Comparison Queries

### Entity Comparison

```python
# Compare two companies
comparison = rag.compare_entities("OpenAI", "Anthropic")

print("Similarities:")
for sim in comparison['similarities']:
    print(f"  - {sim}")

print("\nDifferences:")
for diff in comparison['differences']:
    print(f"  - {diff}")

print(f"\nSummary: {comparison['comparison']}")
```

### Competitive Analysis

```python
# Compare investors
comparison = rag.compare_entities("Sequoia Capital", "Andreessen Horowitz")
print(comparison['comparison'])

# Compare technologies
comparison = rag.compare_entities("GPT-4", "Claude")
print(comparison['comparison'])
```

---

## Analytics Queries

### Graph Statistics

```python
# Overall statistics
stats = rag.get_statistics()

print(f"Total Entities: {stats['total_entities']}")
print("\nEntity Breakdown:")
for entity_type in stats['node_counts']:
    print(f"  {entity_type['label']}: {entity_type['count']}")

print(f"\nTotal Relationships: {stats['total_relationships']}")
```

### Importance Scores

```python
# Most important entities
importance = rag.get_importance_scores(limit=10)

print("Top 10 Most Important Entities:")
for i, entity in enumerate(importance['results'], 1):
    print(f"{i}. {entity['name']} ({entity['type']}): {entity['importance_score']:.2f}")
```

### Trending Technologies

```python
# Get trending technologies
trends = rag.get_trending_technologies(limit=10)

print("Trending Technologies:")
for tech in trends['results']:
    print(f"  - {tech['name']}: {tech['company_count']} companies using it")
```

---

## Temporal Queries

### Recent Activity

```python
# Recent entities (last 30 days)
recent = rag.get_recent_entities(days=30, limit=10)

print("Recent Activity:")
for entity in recent['results']:
    print(f"  - {entity['name']} ({entity['type']}): {entity['last_mentioned']}")
```

### Time-Range Queries

```python
# Funding events in date range
result = rag.query(
    "Which companies raised funding in October 2024?",
    date_range={"start": "2024-10-01", "end": "2024-10-31"}
)
print(result['answer'])
```

---

## Community Detection

### Find Communities

```python
# Detect communities
communities = rag.detect_communities(min_size=3)

print(f"Found {communities['total_communities']} communities")

for i, community in enumerate(communities['communities'][:5], 1):
    print(f"\nCommunity {i} ({community['size']} members):")
    print(f"  Members: {', '.join(community['members'][:10])}")
    print(f"  Description: {community['description']}")
```

### Related Communities

```python
# Find communities related to an entity
related = rag.find_related_communities("OpenAI")

print(f"Communities involving OpenAI:")
for community in related['communities']:
    print(f"  - Community {community['id']}: {community['description']}")
```

---

## Advanced Patterns

### Batch Queries

```python
# Process multiple queries
questions = [
    "What is Anthropic?",
    "Who founded OpenAI?",
    "Which companies use GPT-4?"
]

results = rag.batch_query(questions)
for q, r in zip(questions, results):
    print(f"Q: {q}")
    print(f"A: {r['answer']}\n")
```

### Hybrid Search

```python
# Combine semantic and keyword search
results = rag.hybrid_search(
    query="AI safety research",
    top_k=10,
    semantic_weight=0.7,  # 70% semantic, 30% keyword
    entity_type="Company"
)

for entity in results['results']:
    print(f"{entity['name']}: {entity['combined_score']:.3f}")
```

### Filtered Queries

```python
# Query with entity type filter
result = rag.query(
    "Tell me about recent AI developments",
    entity_types=["Company", "Technology"],
    limit=5
)
print(result['answer'])
```

---

## REST API Examples

### cURL Examples

```bash
# Natural language query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What AI startups raised funding?",
    "use_llm": true
  }'

# Semantic search
curl -X POST "http://localhost:8000/search/semantic" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence",
    "top_k": 10
  }'

# Company profile
curl "http://localhost:8000/company/Anthropic"

# Compare entities
curl -X POST "http://localhost:8000/entity/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "entity1": "OpenAI",
    "entity2": "Anthropic"
  }'
```

### Python Requests

```python
import requests

# Query endpoint
response = requests.post(
    "http://localhost:8000/query",
    json={
        "question": "Which companies are working on AI safety?",
        "return_context": True,
        "use_llm": True
    }
)
result = response.json()
print(result['answer'])

# Semantic search
response = requests.post(
    "http://localhost:8000/search/semantic",
    json={
        "query": "machine learning startups",
        "top_k": 5,
        "entity_type": "Company"
    }
)
entities = response.json()['results']
for entity in entities:
    print(entity['name'])
```

---

## Best Practices

### 1. Use Semantic Search for Discovery

```python
# Instead of exact matching
# ❌ profile = rag.get_company_profile("anthropic")  # Might fail

# Use semantic search first
# ✅ results = rag.semantic_search("anthropic", top_k=1)
#    company_name = results[0]['name']
#    profile = rag.get_company_profile(company_name)
```

### 2. Limit Result Sizes

```python
# Control result sizes for faster queries
results = rag.semantic_search("AI companies", top_k=10)  # Not 100
context = rag.get_entity_context(entity_id, max_hops=1)  # Not 5
```

### 3. Cache Frequent Queries

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_profile(company_name):
    return rag.get_company_profile(company_name)
```

### 4. Use Appropriate Query Types

```python
# For specific entity information → get_company_profile()
# For discovery → semantic_search()
# For relationships → multi_hop_reasoning()
# For trends → get_trending_technologies()
# For general questions → query()
```

---

For complete API documentation, see [RAG_DOCUMENTATION.md](RAG_DOCUMENTATION.md)

