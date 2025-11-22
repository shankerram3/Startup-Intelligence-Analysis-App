# Neo4j Aura DB Setup Guide

This guide shows you how to use **Neo4j Aura DB** (managed cloud database) instead of self-hosting Neo4j on your own server.

---

## 🎯 Why Use Aura DB?

### Benefits of Using Aura

| Feature | Self-Hosted Neo4j | Neo4j Aura DB |
|---------|-------------------|---------------|
| **Data Safety** | ⚠️ Lost if VM evicted | ✅ Always safe in cloud |
| **Backups** | Manual setup required | ✅ Automatic daily backups |
| **VM Memory** | Uses 1-2GB RAM | ✅ No memory usage |
| **VM Disk** | Uses 5-10GB disk | ✅ No disk usage |
| **Maintenance** | Manual updates | ✅ Fully managed |
| **Performance** | Limited by VM | ✅ Dedicated resources |
| **Cost** | Included in VM | 💰 Separate service fee |

**Recommendation**: Aura DB is **highly recommended** for Spot VMs since your VM can be evicted at any time!

---

## 📋 Table of Contents

1. [Create Aura DB Instance](#create-aura-db-instance)
2. [Configure Your Application](#configure-your-application)
3. [Deploy on Azure VM](#deploy-on-azure-vm)
4. [Migrate from Self-Hosted](#migrate-from-self-hosted)
5. [Pricing Information](#pricing-information)
6. [Troubleshooting](#troubleshooting)

---

## Create Aura DB Instance

### Step 1: Sign Up for Neo4j Aura

1. Go to https://neo4j.com/cloud/aura/
2. Click **"Start Free"** or **"Sign Up"**
3. Create account with email or Google/GitHub

### Step 2: Create Database Instance

1. Click **"Create Database"**
2. Choose your plan:

   **Free Tier (Recommended for Testing):**
   - ✅ Free forever
   - ✅ 200,000 nodes + relationships
   - ✅ ~50MB storage
   - ✅ Good for 100-500 articles
   - ⚠️ Pauses after 3 days of inactivity

   **Professional Tier (Recommended for Production):**
   - 💰 Starting at ~$65/month
   - ✅ 1GB memory, 8GB storage
   - ✅ Daily backups
   - ✅ Good for 1,000-10,000 articles
   - ✅ Always available

3. Configure instance:
   - **Region**: Choose the closest region to your application (e.g., "AWS us-east-1" or "GCP us-east4")
   - **Instance name**: `graphrag-kb` or similar
   - Click **"Create Database"**

### Step 3: Save Connection Credentials

⚠️ **IMPORTANT**: You'll only see the password once!

After creation, you'll see:
```
Connection URI: neo4j+s://xxxxx.databases.neo4j.io
Username: neo4j
Password: [generated-password]
```

**Save these immediately!** You'll need them for your `.env` file.

### Step 4: Download Credentials (Optional)

Click **"Download and continue"** to save credentials as `.txt` file.

---

## Configure Your Application

### Option A: New Installation

If you haven't deployed yet:

1. **SSH into your server**:
   ```bash
   ssh user@<your-server-ip>
   ```

2. **Clone repository**:
   ```bash
   git clone -b claude/virtual-ecommerce-setup-011CUoE6BM8E7QC6cXKtJkxv \
     https://github.com/shankerram3/Startup-Intelligence-Analysis-App.git
   cd Startup-Intelligence-Analysis-App
   ```

3. **Create .env file with Aura DB credentials**:
   ```bash
   cat > .env << 'EOF'
   # OpenAI API
   OPENAI_API_KEY=sk-your-openai-api-key-here

   # Neo4j Aura DB Connection
   NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your-aura-db-password-here

   # API Configuration
   API_HOST=0.0.0.0
   API_PORT=8000

   # Embedding Backend
   RAG_EMBEDDING_BACKEND=sentence-transformers
   SENTENCE_TRANSFORMERS_MODEL=BAAI/bge-small-en-v1.5

   # Verbose Logging
   RAG_VERBOSE=1
   EOF

   chmod 600 .env
   ```

4. **Replace with your actual credentials**:
   ```bash
   vim .env
   # Update NEO4J_URI and NEO4J_PASSWORD with your Aura DB values
   ```

5. **Install dependencies**:
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install Python and dependencies
   sudo apt install -y python3 python3-pip python3-venv python3-dev \
     build-essential git curl wget

   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate

   # Install requirements
   pip install -r requirements.txt
   ```

6. **Test connection**:
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
   print('✅ Connected to Aura DB!')
   driver.close()
   "
   ```

7. **Build knowledge graph**:
   ```bash
   # Start with small test
   python pipeline.py \
     --scrape-category startups \
     --scrape-max-pages 1 \
     --max-articles 5
   ```

8. **Generate embeddings**:
   ```bash
   python -c "
   from neo4j import GraphDatabase
   from utils.embedding_generator import EmbeddingGenerator
   import os
   from dotenv import load_dotenv

   load_dotenv()
   driver = GraphDatabase.driver(
       os.getenv('NEO4J_URI'),
       auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
   )
   generator = EmbeddingGenerator(driver, embedding_model='sentence_transformers')
   stats = generator.generate_embeddings_for_all_entities()
   print(f'Generated {stats[\"generated\"]} embeddings')
   driver.close()
   "
   ```

9. **Setup API service**:
   ```bash
   sudo tee /etc/systemd/system/graphrag-api.service > /dev/null << EOF
   [Unit]
   Description=GraphRAG API Service
   After=network.target

   [Service]
   Type=simple
   User=$USER
   WorkingDirectory=$HOME/Startup-Intelligence-Analysis-App
   Environment="PATH=$HOME/Startup-Intelligence-Analysis-App/venv/bin"
   ExecStart=$HOME/Startup-Intelligence-Analysis-App/venv/bin/uvicorn api:app --host 0.0.0.0 --port 8000
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   EOF

   sudo systemctl daemon-reload
   sudo systemctl enable graphrag-api
   sudo systemctl start graphrag-api
   ```

10. **Test API**:
    ```bash
    # From VM
    curl http://localhost:8000/health

    # From your local machine
    curl http://<your-vm-ip>:8000/health
    ```

### Option B: Switch from Self-Hosted to Aura

If you already have Neo4j running on Docker:

1. **Export existing data** (optional - if you want to keep it):
   ```bash
   cd ~/Startup-Intelligence-Analysis-App

   # Export data to CSV
   docker exec neo4j cypher-shell -u neo4j -p your-password \
     "CALL apoc.export.csv.all('/var/lib/neo4j/import/export.csv', {})"

   # Copy export file
   docker cp neo4j:/var/lib/neo4j/import/export.csv ./neo4j_export.csv
   ```

2. **Stop and remove Neo4j container**:
   ```bash
   docker compose down
   # This frees up 1-2GB RAM!
   ```

3. **Update .env file**:
   ```bash
   vim .env

   # Change these lines:
   # NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
   # NEO4J_PASSWORD=your-aura-db-password
   ```

4. **Restart API**:
   ```bash
   sudo systemctl restart graphrag-api
   ```

5. **Rebuild knowledge graph** (fresh start):
   ```bash
   source venv/bin/activate
   python pipeline.py --skip-scraping --max-articles 10
   ```

---

## Deploy on Azure VM

### Simplified Deployment (No Docker Needed!)

Since you're using Aura DB, you don't need Docker at all! Here's a streamlined setup:

```bash
# 1. SSH into VM
ssh azureuser@<your-vm-ip>

# 2. Update system
sudo apt update && sudo apt upgrade -y

# 3. Install essentials (NO DOCKER!)
sudo apt install -y \
  python3 python3-pip python3-venv python3-dev \
  build-essential git curl wget vim htop

# 4. Clone repository
git clone -b claude/virtual-ecommerce-setup-011CUoE6BM8E7QC6cXKtJkxv \
  https://github.com/shankerram3/Startup-Intelligence-Analysis-App.git
cd Startup-Intelligence-Analysis-App

# 5. Create .env with Aura DB credentials
cat > .env << 'EOF'
OPENAI_API_KEY=sk-your-key-here
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-aura-password-here
API_HOST=0.0.0.0
API_PORT=8000
RAG_EMBEDDING_BACKEND=sentence-transformers
SENTENCE_TRANSFORMERS_MODEL=BAAI/bge-small-en-v1.5
EOF

vim .env  # Edit with your actual credentials

# 6. Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 7. Test connection
python -c "from neo4j import GraphDatabase; import os; from dotenv import load_dotenv; load_dotenv(); driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))); driver.verify_connectivity(); print('✅ Aura DB connected!'); driver.close()"

# 8. Build knowledge graph
python pipeline.py --scrape-category startups --scrape-max-pages 1 --max-articles 5

# 9. Generate embeddings
python -c "from neo4j import GraphDatabase; from utils.embedding_generator import EmbeddingGenerator; import os; from dotenv import load_dotenv; load_dotenv(); driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))); generator = EmbeddingGenerator(driver, embedding_model='sentence_transformers'); generator.generate_embeddings_for_all_entities(); driver.close()"

# 10. Setup API service
sudo tee /etc/systemd/system/graphrag-api.service > /dev/null << EOF
[Unit]
Description=GraphRAG API Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/Startup-Intelligence-Analysis-App
Environment="PATH=$HOME/Startup-Intelligence-Analysis-App/venv/bin"
ExecStart=$HOME/Startup-Intelligence-Analysis-App/venv/bin/uvicorn api:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable graphrag-api
sudo systemctl start graphrag-api

# 11. Test API
curl http://localhost:8000/health
```

### Configure Azure Firewall

You only need these ports with Aura DB:

```bash
# Configure UFW
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8000/tcp  # API only!
# No Neo4j ports needed!
```

In Azure Portal:
- Go to VM → **Networking**
- Add inbound rules for:
  - Port 22 (SSH) - Restrict to your IP
  - Port 8000 (API) - Public or restricted
  - **No Neo4j ports needed!** (7474, 7687)

---

## Migrate from Self-Hosted

### Option 1: Fresh Start (Recommended)

Simply rebuild your knowledge graph with Aura DB:

```bash
# Update .env with Aura credentials
vim .env

# Rebuild graph from scratch
python pipeline.py --skip-scraping --max-articles 100
```

### Option 2: Export/Import Data

If you want to keep existing data:

#### Export from Self-Hosted

```bash
# Export to JSON
python -c "
from neo4j import GraphDatabase

# Connect to old database
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))

with driver.session() as session:
    # Export all nodes
    result = session.run('MATCH (n) RETURN n')
    # ... custom export logic ...

driver.close()
"
```

#### Import to Aura DB

```bash
# Import to Aura
python -c "
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to Aura DB
driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'),
    auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
)

# Import nodes and relationships
# ... custom import logic ...

driver.close()
"
```

**Note**: Fresh rebuild is usually faster and cleaner than migration.

---

## Pricing Information

### Free Tier

- **Cost**: $0 (forever)
- **Storage**: ~50MB
- **Capacity**: 200,000 nodes + relationships
- **Good for**: 100-500 articles
- **Limitations**:
  - Pauses after 3 days of inactivity (resumes instantly on next query)
  - No backups
  - Shared infrastructure

### Professional Tier

**Starter** (~$65/month):
- 1GB memory, 8GB storage
- Good for 1,000-10,000 articles
- Daily automated backups
- 99.95% SLA

**Small** (~$165/month):
- 2GB memory, 16GB storage
- Good for 10,000-50,000 articles

**Medium** (~$330/month):
- 4GB memory, 32GB storage
- Good for 50,000-100,000 articles

**Pricing Calculator**: https://neo4j.com/pricing/

### Cost Comparison

| Setup | Monthly Cost | Pros | Cons |
|-------|-------------|------|------|
| **Azure VM + Self-Hosted Neo4j** | ~$15-30 (VM only) | Lower cost, full control | VM can be evicted, manual backups |
| **Azure VM + Aura Free** | ~$15-30 (VM only) | Safe data, managed | Limited capacity |
| **Azure VM + Aura Pro** | ~$80-95 (VM + Aura) | Safe, scalable, managed | Higher cost |

**Recommendation**:
- Start with **Aura Free** for testing
- Upgrade to **Aura Pro** when you exceed capacity or need backups

---

## Access Aura DB Browser

### Via Neo4j Aura Console

1. Go to https://console.neo4j.io/
2. Login with your account
3. Click on your database
4. Click **"Open with"** → **"Neo4j Browser"**
5. Run Cypher queries

### Via Neo4j Desktop (Local)

1. Download Neo4j Desktop
2. Add remote connection:
   - URI: `neo4j+s://xxxxx.databases.neo4j.io`
   - Username: `neo4j`
   - Password: Your Aura password
3. Connect and query

### Query Examples

```cypher
// Check graph statistics
MATCH (n)
RETURN labels(n)[0] as type, count(n) as count
ORDER BY count DESC;

// Check storage usage
CALL dbms.queryJmx('org.neo4j:*')
YIELD name, attributes
WHERE name CONTAINS 'Primitive'
RETURN name, attributes;

// Find most connected entities
MATCH (n)
WITH n, size((n)--()) as connections
WHERE connections > 0
RETURN labels(n)[0] as type, n.name as name, connections
ORDER BY connections DESC
LIMIT 20;
```

---

## Troubleshooting

### Issue: Connection Failed

```bash
# Test connection
python -c "
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

print(f'URI: {os.getenv(\"NEO4J_URI\")}')
print(f'User: {os.getenv(\"NEO4J_USER\")}')

try:
    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
    )
    driver.verify_connectivity()
    print('✅ Connected!')
    driver.close()
except Exception as e:
    print(f'❌ Error: {e}')
"
```

**Common fixes**:
- Check URI format: Must be `neo4j+s://` (not `bolt://`)
- Verify password is correct
- Check if Aura DB is paused (Free tier)
- Verify VM has outbound internet access

### Issue: Database Paused (Free Tier)

Free tier databases pause after 3 days of inactivity.

**Solution**: Just run a query - it resumes automatically:
```bash
curl http://localhost:8000/health
```

Or in Aura Console, click **"Resume"**.

### Issue: Capacity Exceeded (Free Tier)

Free tier has 200k nodes + relationships limit.

**Solutions**:
1. Delete old data:
   ```cypher
   // Delete old articles (keep last 100)
   MATCH (a:Article)
   WITH a ORDER BY a.published_date ASC
   LIMIT 1000
   DETACH DELETE a;
   ```

2. Upgrade to Professional tier

### Issue: Slow Queries

Aura DB can be slower than local for small queries due to network latency.

**Solutions**:
- Use batch operations
- Add indexes (automatic in Aura)
- Cache frequent queries
- Consider larger Aura instance

### Issue: Firewall Blocking Connections

Some networks block Neo4j ports.

**Check**:
```bash
# Test connectivity
nc -zv xxxxx.databases.neo4j.io 7687

# Or
curl https://xxxxx.databases.neo4j.io
```

**Solution**: Ensure VM's network security group allows outbound HTTPS/7687.

---

## Best Practices

### 1. Connection Pooling

The Neo4j driver handles connection pooling automatically. Keep one driver instance:

```python
# Good - single driver instance
class GraphRAG:
    def __init__(self):
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        self.driver.close()

# Bad - creating driver for each query
def query():
    driver = GraphDatabase.driver(uri, auth=auth)  # Don't do this!
    # ...
    driver.close()
```

### 2. Monitor Usage

Check your usage in Aura Console:
- **Database** → **Metrics**
- Watch storage and node count
- Set up alerts for limits

### 3. Optimize Queries

```cypher
// Bad - scans all nodes
MATCH (n) WHERE n.name = 'OpenAI' RETURN n;

// Good - uses index
MATCH (n:Company {name: 'OpenAI'}) RETURN n;
```

### 4. Regular Cleanup

```python
# Delete temporary data
with driver.session() as session:
    session.run("""
        MATCH (n:Temporary)
        WHERE n.created_at < datetime() - duration('P7D')
        DETACH DELETE n
    """)
```

### 5. Backups (Professional Tier)

- Automatic daily backups
- Point-in-time recovery available
- Download backups from Aura Console

---

## Advantages of Aura DB for Your Setup

### Resource Savings on Your VM

| Resource | Self-Hosted | Aura DB | Savings |
|----------|-------------|---------|---------|
| **RAM** | 1-2GB | 0GB | ✅ 1-2GB freed |
| **Disk** | 5-10GB | 0GB | ✅ 5-10GB freed |
| **CPU** | 10-30% | 0% | ✅ More for API |

### Safety for Spot VM

- ✅ Data persists even if VM is evicted
- ✅ No backup scripts needed
- ✅ No data loss risk
- ✅ Faster VM replacement

### Operational Benefits

- ✅ No Neo4j maintenance
- ✅ Automatic updates
- ✅ Scaling without VM changes
- ✅ Professional backups

---

## Quick Reference

### Connection Format

```bash
# Self-Hosted Neo4j (Docker)
NEO4J_URI=bolt://localhost:7687

# Neo4j Aura DB
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
```

### Test Connection

```bash
python -c "from neo4j import GraphDatabase; import os; from dotenv import load_dotenv; load_dotenv(); driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))); driver.verify_connectivity(); print('✅ Connected!'); driver.close()"
```

### Access Aura Console

https://console.neo4j.io/

### Get Help

- Documentation: https://neo4j.com/docs/aura/
- Support: support@neo4j.com
- Community: https://community.neo4j.com/

---

## Next Steps

1. **Create Aura DB instance**: https://console.neo4j.io/
2. **Save credentials**: Download .txt file
3. **Update .env**: Use Aura URI and password
4. **Test connection**: Run connection test
5. **Build graph**: Run pipeline
6. **Access data**: Via Aura Console or API

---

**Your data is now safe in the cloud! 🎉**

Even if your Spot VM gets evicted, your knowledge graph is secure in Aura DB.

For more information:
- [Azure Deployment Guide](AZURE_DEPLOYMENT_GUIDE.md)
- [Quick Start Guide](QUICKSTART_AZURE.md)
- [Main README](README.md)
