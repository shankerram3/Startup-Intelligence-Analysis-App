# Performance Optimization Guide

This document outlines strategies to improve the performance of the Startup Intelligence Analysis App.

## 📊 Current Performance Status

### ✅ Already Implemented
- ✅ Redis caching for query results
- ✅ Rate limiting (30 requests/minute)
- ✅ Async API endpoints
- ✅ Connection pooling (Neo4j driver handles this)
- ✅ Health checks and monitoring

### 🔧 Optimization Opportunities

---

## 1. Caching Optimizations

### 1.1 Expand Cache Coverage

**Current State:** Only query results are cached.

**Recommendations:**

```python
# Add caching to frequently accessed endpoints
@async_cached(ttl=1800)  # 30 minutes
async def fetch_neo4j_overview():
    # Cache Neo4j overview stats
    pass

@async_cached(ttl=3600)  # 1 hour
async def fetch_aura_communities(min_size: int, limit: int):
    # Cache community detection results
    pass

@async_cached(ttl=7200)  # 2 hours
async def fetch_analytics_dashboard(hours: int):
    # Cache analytics dashboard
    pass
```

**Implementation:**
- Cache Neo4j overview stats (30 min TTL)
- Cache community detection results (1 hour TTL)
- Cache analytics dashboard (2 hour TTL)
- Cache entity lookups (1 hour TTL)

### 1.2 Optimize Cache TTLs

**Current:** Default TTL is 3600 seconds (1 hour)

**Recommendations:**
- Query results: 1 hour (current) ✅
- Entity data: 2 hours (increase from current)
- Analytics: 30 minutes (frequent updates)
- Graph stats: 15 minutes (can change with new data)

### 1.3 Redis Connection Pooling

**Current:** Single Redis connection per request

**Recommendation:** Use connection pooling

```python
# In utils/cache.py, update CacheManager.__init__
self._client = Redis.from_url(
    CacheConfig.REDIS_URL,
    decode_responses=False,
    socket_connect_timeout=5,
    socket_timeout=5,
    max_connections=50,  # Add connection pool
    retry_on_timeout=True,
)
```

---

## 2. Database Query Optimizations

### 2.1 Neo4j Query Optimization

**Current:** Queries may not be optimized for large graphs

**Recommendations:**

1. **Add indexes** (if not already present):
```cypher
// Create indexes for frequently queried properties
CREATE INDEX entity_id_index IF NOT EXISTS FOR (e:Entity) ON (e.id);
CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name);
CREATE INDEX article_id_index IF NOT EXISTS FOR (a:Article) ON (a.id);
CREATE INDEX company_name_index IF NOT EXISTS FOR (c:Company) ON (c.name);
```

2. **Optimize graph traversal queries:**
```cypher
// Use LIMIT early in queries
MATCH (n:Company)-[r]-(m)
WHERE n.name = $name
WITH n, r, m
LIMIT 50  // Limit early, not at the end
RETURN n, r, m
```

3. **Use query hints:**
```cypher
// Use USING INDEX for better performance
MATCH (c:Company)
USING INDEX c:Company(name)
WHERE c.name = $name
RETURN c
```

### 2.2 Batch Database Operations

**Current:** Individual queries for each entity

**Recommendation:** Batch operations where possible

```python
# Instead of:
for entity_id in entity_ids:
    result = session.run("MATCH (e {id: $id}) RETURN e", id=entity_id)

# Use:
result = session.run("""
    UNWIND $ids as id
    MATCH (e {id: id})
    RETURN e
""", ids=entity_ids)
```

### 2.3 Connection Pool Configuration

**Current:** Default Neo4j driver connection pool

**Recommendation:** Configure connection pool size

```python
# In rag_query.py, update driver initialization
self.driver = GraphDatabase.driver(
    neo4j_uri,
    auth=(neo4j_user, neo4j_password),
    max_connection_lifetime=3600,  # 1 hour
    max_connection_pool_size=50,  # Increase pool size
    connection_acquisition_timeout=60,  # 60 seconds
)
```

---

## 3. API Performance Optimizations

### 3.1 Parallel Processing

**Current:** Sequential processing in some endpoints

**Recommendation:** Use `asyncio.gather()` for parallel operations

```python
# Instead of:
most_connected = await fetch_most_connected()
importance = await fetch_importance()

# Use:
most_connected, importance = await asyncio.gather(
    fetch_most_connected(),
    fetch_importance()
)
```

### 3.2 Response Compression

**Current:** No compression

**Recommendation:** Enable Gzip compression

```python
# In api.py, add compression middleware
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB
```

### 3.3 Pagination

**Current:** Some endpoints return all data

**Recommendation:** Add pagination to large result sets

```python
@app.get("/entities")
async def get_entities(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    skip = (page - 1) * page_size
    # Use SKIP and LIMIT in Cypher queries
    return results[skip:skip + page_size]
```

### 3.4 Background Tasks

**Current:** Some operations block the request

**Recommendation:** Use FastAPI BackgroundTasks for non-critical operations

```python
from fastapi import BackgroundTasks

@app.post("/query")
async def query(
    request: QueryRequest,
    background_tasks: BackgroundTasks
):
    # Process query immediately
    result = await process_query(request)
    
    # Log analytics in background
    background_tasks.add_task(log_analytics, request, result)
    
    return result
```

---

## 4. Docker & Container Optimizations

### 4.1 Resource Limits

**Current:** No resource limits specified

**Recommendation:** Add resource limits to docker-compose.yml

```yaml
services:
  graphrag-api:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### 4.2 Multi-stage Build Optimization

**Current:** Already using multi-stage builds ✅

**Recommendation:** Optimize layer caching

```dockerfile
# Copy only requirements first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Then copy application code
COPY . .
```

### 4.3 Python Optimizations

**Recommendation:** Add Python optimizations

```dockerfile
# In Dockerfile, add:
ENV PYTHONOPTIMIZE=1  # Remove assert statements
ENV PYTHONDONTWRITEBYTECODE=1  # Don't create .pyc files
```

---

## 5. Frontend Optimizations

### 5.1 Code Splitting

**Current:** May load all code upfront

**Recommendation:** Implement lazy loading

```typescript
// In frontend/src/App.tsx
import { lazy, Suspense } from 'react';

const DashboardView = lazy(() => import('./components/DashboardView'));
const QueryView = lazy(() => import('./components/QueryView'));

// Use Suspense for loading states
<Suspense fallback={<Loading />}>
  <DashboardView />
</Suspense>
```

### 5.2 Bundle Size Optimization

**Recommendation:** Analyze and optimize bundle size

```bash
# In frontend directory
npm run build -- --analyze
```

### 5.3 API Request Batching

**Current:** Multiple individual API calls

**Recommendation:** Batch related requests

```typescript
// Instead of:
const overview = await fetch('/admin/neo4j/overview');
const communities = await fetch('/aura/communities');
const stats = await fetch('/aura/community-stats');

// Use Promise.all:
const [overview, communities, stats] = await Promise.all([
  fetch('/admin/neo4j/overview'),
  fetch('/aura/communities'),
  fetch('/aura/community-stats')
]);
```

### 5.4 Debounce Search Inputs

**Recommendation:** Debounce search/query inputs

```typescript
import { debounce } from 'lodash';

const debouncedSearch = debounce((query: string) => {
  performSearch(query);
}, 300);  // Wait 300ms after user stops typing
```

---

## 6. Infrastructure Optimizations

### 6.1 Redis Configuration

**Recommendation:** Optimize Redis settings

```bash
# In Redis configuration or .env
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
REDIS_RETRY_ON_TIMEOUT=true
```

### 6.2 Neo4j AuraDB Optimization

**Recommendations:**
- Use appropriate AuraDB instance size for your graph size
- Enable query result caching in AuraDB
- Use read replicas for read-heavy workloads

### 6.3 CDN for Static Assets

**Current:** Vercel handles this ✅

**Recommendation:** Ensure Vercel CDN is enabled for all static assets

---

## 7. Monitoring & Profiling

### 7.1 Add Performance Monitoring

**Recommendation:** Track slow queries and endpoints

```python
# In api.py, add timing middleware
@app.middleware("http")
async def log_slow_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    if duration > 1.0:  # Log requests > 1 second
        logger.warning("slow_request", 
            path=request.url.path,
            duration=duration,
            method=request.method
        )
    
    return response
```

### 7.2 Database Query Profiling

**Recommendation:** Profile Neo4j queries

```python
# Add query profiling
with driver.session() as session:
    result = session.run("PROFILE MATCH (n) RETURN n LIMIT 10")
    # Check query plan and execution time
```

---

## 8. Quick Wins (High Impact, Low Effort)

### Priority 1: Immediate Impact
1. ✅ **Enable Gzip compression** (5 min) - Reduces response size by 70-90%
2. ✅ **Add connection pooling for Redis** (10 min) - Improves concurrent request handling
3. ✅ **Cache Neo4j overview endpoint** (15 min) - Reduces database load
4. ✅ **Batch API requests in frontend** (20 min) - Reduces network overhead

### Priority 2: Medium Impact
5. **Add pagination to large endpoints** (1 hour)
6. **Optimize Neo4j indexes** (30 min)
7. **Implement lazy loading in frontend** (2 hours)
8. **Add background tasks for analytics** (1 hour)

### Priority 3: Long-term
9. **Query optimization and profiling** (ongoing)
10. **Database query result caching** (2 hours)
11. **Advanced monitoring and alerting** (4 hours)

---

## 9. Performance Testing

### Recommended Tools
- **Load Testing:** `locust` or `k6`
- **API Profiling:** `py-spy` or `cProfile`
- **Database Profiling:** Neo4j query profiler
- **Frontend:** Lighthouse, WebPageTest

### Example Load Test

```python
# locustfile.py
from locust import HttpUser, task, between

class GraphRAGUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def query(self):
        self.client.post("/query", json={
            "question": "Which AI startups raised funding?",
            "use_llm": True
        })
    
    @task(3)
    def health_check(self):
        self.client.get("/health")
```

---

## 10. Expected Performance Improvements

| Optimization | Expected Improvement | Effort |
|-------------|---------------------|--------|
| Gzip compression | 70-90% response size reduction | Low |
| Redis connection pooling | 20-30% faster cache operations | Low |
| Caching Neo4j overview | 80-90% faster dashboard load | Low |
| Frontend code splitting | 30-50% faster initial load | Medium |
| Query optimization | 20-40% faster queries | Medium |
| Database indexes | 50-80% faster lookups | Medium |
| Batch API requests | 30-50% fewer requests | Low |

---

## Implementation Checklist

- [ ] Enable Gzip compression
- [ ] Add Redis connection pooling
- [ ] Cache frequently accessed endpoints
- [ ] Optimize Neo4j indexes
- [ ] Add pagination to large endpoints
- [ ] Implement frontend code splitting
- [ ] Batch API requests in frontend
- [ ] Add performance monitoring
- [ ] Profile slow queries
- [ ] Set Docker resource limits

---

## Monitoring Performance

After implementing optimizations, monitor:
- **API Response Times:** Track p50, p95, p99 latencies
- **Cache Hit Rates:** Should be > 80% for cached endpoints
- **Database Query Times:** Track slow queries (> 1 second)
- **Frontend Load Times:** Track First Contentful Paint (FCP), Time to Interactive (TTI)
- **Error Rates:** Should remain < 1%

---

## Questions or Issues?

If you encounter performance issues:
1. Check Redis connection and cache hit rates
2. Profile Neo4j queries for slow operations
3. Monitor API response times in logs
4. Use browser DevTools to identify frontend bottlenecks
5. Review Docker container resource usage

