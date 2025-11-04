# Quick Start Guide - Azure VM Deployment

This is a streamlined guide to get your GraphRAG application running on your Azure VM quickly.

---

## Your VM Specifications

- **Name**: GraphRAG
- **Size**: Standard_F2ams_v6 (2 vCPUs, ~4GB RAM)
- **OS**: Ubuntu 24.04 LTS
- **Disk**: 30 GB Premium SSD
- **Type**: Spot VM ⚠️ (Can be evicted - regular backups important!)
- **Region**: East US 2
- **Authentication**: SSH Key

---

## Quick Setup (5 Minutes)

### 1. Connect to Your VM

```bash
# SSH into your VM (replace with your actual IP)
ssh azureuser@<your-vm-ip>
```

### 2. Run Automated Setup Script

```bash
# Download and run setup script
cd ~
git clone https://github.com/yourusername/Startup-Intelligence-Analysis-App.git
cd Startup-Intelligence-Analysis-App
bash azure_setup.sh
```

The script will:
- ✅ Update system packages
- ✅ Install Python, Docker, and dependencies
- ✅ Setup Neo4j database
- ✅ Configure firewall
- ✅ Create systemd service
- ✅ Create backup scripts

### 3. Log Out and Back In

```bash
# Log out to apply Docker group permissions
exit

# Log back in
ssh azureuser@<your-vm-ip>
```

### 4. Configure Environment

```bash
cd ~/Startup-Intelligence-Analysis-App

# Edit .env file with your OpenAI API key
vim .env

# Change these lines:
# OPENAI_API_KEY=sk-your-actual-key-here
# NEO4J_PASSWORD=ChangeThisPassword123!
```

Save and exit (`:wq` in vim)

### 5. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies (this may take 5-10 minutes)
pip install -r requirements.txt

# Setup browser for web scraping (if you plan to scrape)
crawl4ai-setup
```

### 6. Build Knowledge Graph (Small Test)

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run pipeline with small dataset
python pipeline.py \
  --scrape-category startups \
  --scrape-max-pages 1 \
  --max-articles 5
```

This will:
1. Scrape 5 TechCrunch articles
2. Extract entities using GPT-4
3. Build Neo4j knowledge graph

### 7. Generate Embeddings

```bash
# Generate embeddings for semantic search
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

### 8. Start the API

```bash
# Start API service
sudo systemctl start graphrag-api

# Check status
sudo systemctl status graphrag-api

# View logs
sudo journalctl -u graphrag-api -f
```

### 9. Test Your Deployment

```bash
# Get your VM public IP
curl ifconfig.me

# From your local machine, test the API
curl http://<your-vm-ip>:8000/health

# Query the knowledge graph
curl -X POST "http://<your-vm-ip>:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Tell me about AI startups", "use_llm": true}'
```

---

## Access Your Services

Once deployed, you can access:

- **API Documentation**: `http://<your-vm-ip>:8000/docs`
- **API Health Check**: `http://<your-vm-ip>:8000/health`
- **Neo4j Browser**: `http://<your-vm-ip>:7474`
  - Username: `neo4j`
  - Password: (from your .env file)

---

## Helper Commands

The setup script created these useful commands:

```bash
# Start all services
~/start_graphrag.sh

# Stop all services
~/stop_graphrag.sh

# Check status
~/status_graphrag.sh

# Backup Neo4j database
~/backup_neo4j.sh
```

---

## Azure Network Security Group (NSG) Configuration

You need to open these ports in Azure Portal:

1. Go to Azure Portal → Your VM → **Networking**
2. Click **Add inbound port rule**
3. Add these rules:

| Port | Service | Source | Notes |
|------|---------|--------|-------|
| 22 | SSH | Your IP | Secure access |
| 8000 | API | Any | Public API |
| 7474 | Neo4j Browser | Your IP | Admin access |
| 7687 | Neo4j Bolt | Your IP | Database access |

**Security Tip**: Restrict ports 7474 and 7687 to your IP address only!

---

## Important: Spot VM Considerations

⚠️ Your VM is a **Spot instance** - it can be evicted by Azure at any time!

### Protect Your Data

1. **Regular Backups**:
   ```bash
   # Run backup
   ~/backup_neo4j.sh

   # Setup daily backups (runs at 2 AM)
   (crontab -l 2>/dev/null; echo "0 2 * * * /home/azureuser/backup_neo4j.sh") | crontab -
   ```

2. **Backup to Azure Blob Storage** (recommended):
   ```bash
   # Install Azure CLI
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

   # Login
   az login

   # Upload backup
   az storage blob upload \
     --account-name yourstorageaccount \
     --container-name backups \
     --name neo4j_backup_$(date +%Y%m%d).tar.gz \
     --file ~/neo4j-backups/neo4j_backup_*.tar.gz
   ```

3. **Monitor for Eviction**:
   - Azure sends eviction notice 30 seconds before eviction
   - Consider setting up Azure Monitor alerts

---

## Common Commands

### Manage Services

```bash
# Start Neo4j
cd ~/Startup-Intelligence-Analysis-App
docker compose up -d

# Stop Neo4j
docker compose down

# View Neo4j logs
docker compose logs -f neo4j

# Start API
sudo systemctl start graphrag-api

# Stop API
sudo systemctl stop graphrag-api

# Restart API
sudo systemctl restart graphrag-api

# View API logs
sudo journalctl -u graphrag-api -f
```

### Check Status

```bash
# Check all services
~/status_graphrag.sh

# Check disk space
df -h

# Check memory usage
free -h

# Check running processes
htop
```

### Update Application

```bash
cd ~/Startup-Intelligence-Analysis-App

# Pull latest code
git pull

# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart API
sudo systemctl restart graphrag-api
```

---

## Troubleshooting

### Issue: Cannot connect to Neo4j

```bash
# Check if Neo4j is running
docker ps | grep neo4j

# View logs
docker compose logs neo4j

# Restart Neo4j
docker compose restart neo4j
```

### Issue: API won't start

```bash
# Check API logs
sudo journalctl -u graphrag-api -f

# Check if port is in use
sudo netstat -tlnp | grep 8000

# Restart API
sudo systemctl restart graphrag-api
```

### Issue: Out of disk space

```bash
# Check disk usage
df -h

# Find large files
du -sh /* | sort -h

# Clean Docker
docker system prune -a

# Clean old backups
rm ~/neo4j-backups/neo4j_backup_old*.tar.gz
```

### Issue: Out of memory

```bash
# Check memory
free -h

# Check which process uses most memory
ps aux --sort=-%mem | head

# Consider upgrading VM size if needed
```

---

## Performance Tips for Small VM

Your VM has limited resources (2 vCPUs, 4GB RAM). Here are optimization tips:

### 1. Use Sentence Transformers Instead of OpenAI

Saves API costs and reduces latency:

```bash
# In .env file
RAG_EMBEDDING_BACKEND=sentence-transformers
SENTENCE_TRANSFORMERS_MODEL=BAAI/bge-small-en-v1.5
```

### 2. Limit Dataset Size

Start with small datasets:

```bash
# Process only 10-50 articles initially
python pipeline.py --skip-scraping --max-articles 10
```

### 3. Optimize Neo4j Memory

Edit `docker-compose.yml`:

```yaml
environment:
  # Reduced settings for 4GB RAM VM
  - NEO4J_dbms_memory_heap_initial__size=512M
  - NEO4J_dbms_memory_heap_max__size=1G
  - NEO4J_dbms_memory_pagecache_size=512M
```

### 4. Process in Batches

Process articles in small batches to avoid memory issues:

```bash
# Process 10 articles at a time
python pipeline.py --skip-scraping --max-articles 10

# Then process next batch
python pipeline.py --skip-scraping --max-articles 20
```

---

## Next Steps

1. **Scale Up** - If you need more resources, upgrade to Standard_D4s_v3 (4 vCPUs, 16GB RAM)

2. **Add HTTPS** - Setup Let's Encrypt SSL certificate:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   ```

3. **Setup Monitoring** - Use Azure Monitor or install Prometheus

4. **Add Authentication** - Secure your API endpoints

5. **Setup CI/CD** - Automate deployments with GitHub Actions

---

## Useful Links

- **Full Documentation**: [README.md](README.md)
- **Complete Azure Guide**: [AZURE_DEPLOYMENT_GUIDE.md](AZURE_DEPLOYMENT_GUIDE.md)
- **API Reference**: [RAG_DOCUMENTATION.md](RAG_DOCUMENTATION.md)
- **Local Development**: [HOW_TO_RUN.md](HOW_TO_RUN.md)

---

## Quick Reference

```bash
# Essential Commands
~/start_graphrag.sh              # Start everything
~/stop_graphrag.sh               # Stop everything
~/status_graphrag.sh             # Check status
~/backup_neo4j.sh                # Backup database

# URLs (replace <your-vm-ip> with actual IP)
http://<your-vm-ip>:8000/docs    # API documentation
http://<your-vm-ip>:8000/health  # Health check
http://<your-vm-ip>:7474         # Neo4j browser
```

---

**You're all set! Happy querying! 🚀**

For issues or questions, refer to the full [Azure Deployment Guide](AZURE_DEPLOYMENT_GUIDE.md).
