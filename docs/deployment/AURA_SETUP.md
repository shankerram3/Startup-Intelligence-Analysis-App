# Neo4j Aura Setup Guide

Guide for using Neo4j Aura (managed cloud Neo4j) with the Startup Intelligence Analysis App.

---

## Overview

Neo4j Aura is a fully managed cloud graph database service. Benefits:
- ✅ No server management required
- ✅ Automatic backups
- ✅ High availability
- ✅ Automatic scaling
- ✅ Free tier available

---

## Quick Start

### 1. Create Aura Instance

1. Go to https://console.neo4j.io/
2. Sign up or log in
3. Click "Create Instance"
4. Choose:
   - **Free tier** (for testing): 0.5GB storage
   - **Professional** (for production): Custom size
5. Wait for provisioning (~5 minutes)

### 2. Get Connection Details

After creation, you'll receive:
- **Connection URI**: `neo4j+s://xxxxx.databases.neo4j.io`
- **Username**: `neo4j`
- **Password**: (auto-generated, save this!)

**⚠️ IMPORTANT**: Save the password immediately - it's only shown once!

### 3. Configure Application

Update your `.env` file:

```bash
# Neo4j Aura connection
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=<your-aura-password>

# OpenAI (required)
OPENAI_API_KEY=sk-your-key

# API settings
API_HOST=0.0.0.0
API_PORT=8000
```

### 4. Test Connection

```bash
python -c "
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()
driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'),
    auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
)
driver.verify_connectivity()
print('✅ Neo4j Aura connected!')
driver.close()
"
```

---

## Security Best Practices

### 1. IP Allowlist

In Aura console:
1. Go to your instance → "Connection"
2. Click "Edit" next to IP Allowlist
3. Add specific IPs instead of allowing all (0.0.0.0/0)

### 2. Rotate Password

```bash
# In Aura console, reset password
# Update .env file with new password
```

### 3. Use Environment Variables

Never hardcode credentials:
```python
# ❌ BAD
driver = GraphDatabase.driver("neo4j+s://...", auth=("neo4j", "password123"))

# ✅ GOOD
driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'),
    auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
)
```

---

## Connection URI Formats

### Aura (Encrypted)
```
neo4j+s://xxxxx.databases.neo4j.io
```
- `neo4j+s://` = Neo4j protocol with SSL/TLS
- Port 7687 is used by default (encrypted)

### Local Docker (Unencrypted)
```
bolt://localhost:7687
```
- `bolt://` = Bolt protocol without encryption
- For local development only

---

## Monitoring

### Aura Console

Access at https://console.neo4j.io/

Monitor:
- Database size
- Query performance
- Memory usage
- Connection count

### Query Performance

```cypher
// Check slow queries
CALL dbms.listQueries()
YIELD query, elapsedTimeMillis, queryId, username
WHERE elapsedTimeMillis > 1000
RETURN query, elapsedTimeMillis
ORDER BY elapsedTimeMillis DESC;

// Create indexes for better performance
CREATE INDEX IF NOT EXISTS FOR (c:Company) ON (c.name);
CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.name);
```

---

## Backups

### Automatic Backups (Aura)

- Backups run automatically
- Point-in-time recovery available
- No manual backup needed

### Manual Export

```bash
# Export data via Neo4j Browser
CALL apoc.export.json.all("export.json", {})
```

---

## Pricing

### Free Tier
- 0.5 GB storage
- Good for testing/development
- 1 instance per account

### Professional Tier
- Starting at $65/month
- Custom storage
- High availability
- Priority support

### Enterprise
- Custom pricing
- Multi-region
- Advanced security
- SLA guarantees

Check current pricing: https://neo4j.com/pricing/

---

## Migration

### From Local to Aura

```bash
# 1. Export from local Neo4j
docker exec neo4j neo4j-admin dump --to=/backups/export.dump

# 2. Upload to Aura via support
# Contact Neo4j support for large imports

# 3. Or use APOC for smaller datasets
CALL apoc.export.cypher.all("export.cypher", {})
```

### From Aura to Local

```bash
# Export via Neo4j Browser or APOC
CALL apoc.export.json.all("export.json", {})

# Import to local
docker exec -i neo4j neo4j-admin load --from=/backups/export.dump --force
```

---

## Troubleshooting

### Connection Timeout

**Error**: `Unable to connect to neo4j+s://...`

**Solutions**:
1. Check IP allowlist in Aura console
2. Verify connection string (should start with `neo4j+s://`)
3. Check if password is correct

### Certificate Errors

**Error**: `SSL certificate verification failed`

**Solution**:
```python
# Python - ensure using neo4j+s:// URI
driver = GraphDatabase.driver(
    "neo4j+s://xxxxx.databases.neo4j.io",
    auth=("neo4j", "password"),
    encrypted=True
)
```

### Out of Memory

**Error**: `OutOfMemoryError`

**Solutions**:
1. Upgrade to larger Aura instance
2. Optimize queries (use LIMIT, indexes)
3. Break large operations into batches

### Slow Queries

```cypher
// Check for missing indexes
CALL db.indexes()

// Create needed indexes
CREATE INDEX IF NOT EXISTS FOR (c:Company) ON (c.id);
CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (c.id);
```

---

## Best Practices

### 1. Use Connection Pooling

```python
# Create driver once, reuse
driver = GraphDatabase.driver(uri, auth=auth)

# Use sessions for queries
with driver.session() as session:
    result = session.run("MATCH (n) RETURN count(n)")
```

### 2. Batch Operations

```python
# ❌ BAD: One query per item
for item in items:
    session.run("CREATE (n:Node {prop: $val})", val=item)

# ✅ GOOD: Batch create
session.run("""
    UNWIND $items AS item
    CREATE (n:Node {prop: item})
""", items=items)
```

### 3. Close Connections

```python
try:
    driver = GraphDatabase.driver(uri, auth=auth)
    # ... use driver
finally:
    driver.close()  # Always close!
```

---

## Additional Resources

- [Neo4j Aura Documentation](https://neo4j.com/docs/aura/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/)
- [Aura Console](https://console.neo4j.io/)

---

For detailed Aura-specific instructions, see:
- `AURA_DB_SETUP.md` - Complete Aura setup
- `AURA_CREDENTIALS_GUIDE.md` - Managing credentials

