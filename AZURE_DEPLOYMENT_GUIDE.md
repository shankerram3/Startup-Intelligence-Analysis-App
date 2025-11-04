# Azure VM Deployment Guide for GraphRAG Application

This guide provides step-by-step instructions for deploying the TechCrunch Knowledge Graph and GraphRAG application on an Azure Virtual Machine.

---

## 📋 Table of Contents

1. [Azure VM Requirements](#azure-vm-requirements)
2. [Initial VM Setup](#initial-vm-setup)
3. [Install System Dependencies](#install-system-dependencies)
4. [Install Docker](#install-docker)
5. [Clone the Repository](#clone-the-repository)
6. [Setup Neo4j Database](#setup-neo4j-database)
7. [Install Python Dependencies](#install-python-dependencies)
8. [Configure Environment](#configure-environment)
9. [Build Knowledge Graph](#build-knowledge-graph)
10. [Deploy the API](#deploy-the-api)
11. [Configure Firewall & Security](#configure-firewall--security)
12. [Setup System Service](#setup-system-service)
13. [Monitoring & Maintenance](#monitoring--maintenance)
14. [Troubleshooting](#troubleshooting)

---

## Azure VM Requirements

### Recommended VM Specifications

**Minimum Configuration:**
- **VM Size**: Standard_B2s (2 vCPUs, 4 GB RAM)
- **OS**: Ubuntu 22.04 LTS or Ubuntu 20.04 LTS
- **Disk**: 50 GB Standard SSD
- **For small datasets**: 10-1000 articles

**Recommended Configuration:**
- **VM Size**: Standard_D4s_v3 (4 vCPUs, 16 GB RAM)
- **OS**: Ubuntu 22.04 LTS
- **Disk**: 128 GB Premium SSD
- **For medium datasets**: 1000-10000 articles

**Production Configuration:**
- **VM Size**: Standard_D8s_v3 (8 vCPUs, 32 GB RAM)
- **OS**: Ubuntu 22.04 LTS
- **Disk**: 256 GB Premium SSD
- **For large datasets**: 10000+ articles

### Required Ports

| Port | Service | Purpose |
|------|---------|---------|
| 22 | SSH | Remote access |
| 7474 | Neo4j Browser | Graph database UI |
| 7687 | Neo4j Bolt | Database connections |
| 8000 | FastAPI | GraphRAG REST API |
| 80 | HTTP (optional) | Web access |
| 443 | HTTPS (optional) | Secure web access |

---

## Initial VM Setup

### 1. Connect to Your Azure VM

```bash
# From your local machine
ssh azureuser@<your-vm-public-ip>

# If using key-based authentication
ssh -i ~/.ssh/azure_key.pem azureuser@<your-vm-public-ip>
```

### 2. Update System Packages

```bash
# Update package lists
sudo apt update

# Upgrade installed packages
sudo apt upgrade -y

# Install essential tools
sudo apt install -y \
    build-essential \
    curl \
    wget \
    git \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    vim \
    htop \
    net-tools
```

### 3. Set Timezone (Optional)

```bash
# Set to your timezone
sudo timedatectl set-timezone America/Los_Angeles

# Verify
timedatectl
```

---

## Install System Dependencies

### 1. Install Python 3.11+

```bash
# Add deadsnakes PPA for Python 3.11
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Install pip
sudo apt install -y python3-pip

# Verify installation
python3.11 --version
pip3 --version
```

### 2. Set Python 3.11 as Default (Optional)

```bash
# Update alternatives
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Verify
python --version
```

---

## Install Docker

### 1. Install Docker Engine

```bash
# Remove old versions
sudo apt remove -y docker docker-engine docker.io containerd runc

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to docker group
sudo usermod -aG docker $USER

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Verify Docker installation
docker --version
```

### 2. Install Docker Compose

```bash
# Install Docker Compose
sudo apt install -y docker-compose-plugin

# Verify installation
docker compose version
```

### 3. Log out and back in for group changes to take effect

```bash
exit
# Then SSH back in
ssh azureuser@<your-vm-public-ip>
```

---

## Clone the Repository

```bash
# Navigate to home directory
cd ~

# Clone the repository (replace with your repo URL)
git clone https://github.com/yourusername/Startup-Intelligence-Analysis-App.git

# Or if you're deploying existing code, upload it using scp:
# From your local machine:
# scp -r /path/to/Startup-Intelligence-Analysis-App azureuser@<your-vm-public-ip>:~/

# Navigate to project directory
cd Startup-Intelligence-Analysis-App
```

---

## Setup Neo4j Database

### Option A: Using Docker (Recommended)

#### 1. Create Docker Compose File

```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  neo4j:
    image: neo4j:5.13.0
    container_name: neo4j
    restart: unless-stopped
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/your-secure-password-here
      - NEO4J_PLUGINS=["apoc", "graph-data-science"]
      - NEO4J_dbms_memory_heap_initial__size=1G
      - NEO4J_dbms_memory_heap_max__size=2G
      - NEO4J_dbms_memory_pagecache_size=1G
      - NEO4J_dbms_security_procedures_unrestricted=apoc.*,gds.*
      - NEO4J_dbms_security_procedures_allowlist=apoc.*,gds.*
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - neo4j_import:/var/lib/neo4j/import
      - neo4j_plugins:/plugins

volumes:
  neo4j_data:
  neo4j_logs:
  neo4j_import:
  neo4j_plugins:
EOF
```

**Important**: Change `your-secure-password-here` to a strong password!

#### 2. Start Neo4j

```bash
# Start Neo4j container
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f neo4j

# Wait for Neo4j to be ready (about 30 seconds)
sleep 30

# Test connection
docker exec neo4j cypher-shell -u neo4j -p your-secure-password-here "RETURN 'Connected!' as status;"
```

### Option B: Using Azure Managed Services

If you prefer a managed solution, consider:
- **Azure VM with Neo4j from Azure Marketplace**
- **Neo4j Aura** (fully managed cloud service)

---

## Install Python Dependencies

### 1. Create Virtual Environment

```bash
# Navigate to project directory
cd ~/Startup-Intelligence-Analysis-App

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### 2. Install Requirements

```bash
# Install all dependencies
pip install -r requirements.txt

# If you get permission errors, try:
# pip install -r requirements.txt --user

# Install Crawl4AI browser (for web scraping)
crawl4ai-setup
```

### 3. Verify Installation

```bash
# Test imports
python -c "import neo4j; import openai; import fastapi; print('✅ All imports successful!')"
```

---

## Configure Environment

### 1. Create .env File

```bash
cat > .env << 'EOF'
# OpenAI API (Required for entity extraction and LLM generation)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Neo4j Connection (Required)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-secure-password-here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Embedding Backend
RAG_EMBEDDING_BACKEND=sentence-transformers
SENTENCE_TRANSFORMERS_MODEL=BAAI/bge-small-en-v1.5

# Verbose Logging
RAG_VERBOSE=1

# Optional: Azure-specific settings
AZURE_VM_PUBLIC_IP=<your-vm-public-ip>
EOF
```

**Replace the following:**
- `sk-your-openai-api-key-here` → Your actual OpenAI API key
- `your-secure-password-here` → Your Neo4j password
- `<your-vm-public-ip>` → Your Azure VM's public IP address

### 2. Secure the .env File

```bash
# Restrict permissions
chmod 600 .env

# Verify
ls -la .env
```

### 3. Test Configuration

```bash
# Test Neo4j connection
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
print('✅ Neo4j connected!')
driver.close()
"

# Test OpenAI API
python -c "
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
print('✅ OpenAI API configured!')
"
```

---

## Build Knowledge Graph

### 1. Test Run (Small Dataset)

```bash
# Activate virtual environment
source venv/bin/activate

# Run pipeline with a small test
python pipeline.py \
  --scrape-category startups \
  --scrape-max-pages 1 \
  --max-articles 5

# This will:
# 1. Scrape 5 TechCrunch articles
# 2. Extract entities using GPT-4o
# 3. Build Neo4j knowledge graph
```

### 2. Generate Embeddings

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

### 3. Production Build (Optional)

```bash
# For larger dataset (this may take hours)
python pipeline.py \
  --scrape-category ai \
  --scrape-max-pages 10
```

### 4. Verify Graph

```bash
# Check graph statistics
python -c "
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()
driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'),
    auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD'))
)
with driver.session() as session:
    result = session.run('MATCH (n) RETURN count(n) as count')
    nodes = result.single()['count']
    print(f'Total nodes: {nodes}')

    result = session.run('MATCH ()-[r]->() RETURN count(r) as count')
    rels = result.single()['count']
    print(f'Total relationships: {rels}')
driver.close()
"
```

---

## Deploy the API

### 1. Test API Locally

```bash
# Start API server in foreground (for testing)
uvicorn api:app --host 0.0.0.0 --port 8000

# In another terminal, test:
curl http://localhost:8000/health

# If successful, stop the server (Ctrl+C)
```

### 2. Run API in Background

```bash
# Option A: Using nohup
nohup uvicorn api:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &

# Check if running
ps aux | grep uvicorn

# View logs
tail -f api.log

# Option B: Using screen (better for long-running)
screen -S graphrag-api
uvicorn api:app --host 0.0.0.0 --port 8000
# Press Ctrl+A then D to detach

# To reattach:
# screen -r graphrag-api
```

### 3. Test API from Local Machine

```bash
# From your local machine
curl http://<your-vm-public-ip>:8000/health

# Query the API
curl -X POST "http://<your-vm-public-ip>:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Tell me about AI startups", "use_llm": true}'
```

---

## Configure Firewall & Security

### 1. Configure Azure Network Security Group (NSG)

In Azure Portal:

1. Go to your VM → **Networking**
2. Click **Add inbound port rule**
3. Add rules for:

| Priority | Port | Protocol | Source | Destination | Action |
|----------|------|----------|--------|-------------|--------|
| 100 | 22 | TCP | Your IP | Any | Allow |
| 110 | 8000 | TCP | Any | Any | Allow |
| 120 | 7474 | TCP | Your IP | Any | Allow |
| 130 | 7687 | TCP | Your IP | Any | Allow |

**Security Notes:**
- Only allow port 22 (SSH) from your IP address
- Port 8000 can be open to the internet (API)
- Ports 7474 and 7687 should only be accessible from trusted IPs (Neo4j)

### 2. Configure Ubuntu Firewall (UFW)

```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow API
sudo ufw allow 8000/tcp

# Allow Neo4j (only from specific IP if needed)
sudo ufw allow 7474/tcp
sudo ufw allow 7687/tcp

# Check status
sudo ufw status

# If you need to allow only from specific IP:
# sudo ufw allow from YOUR_IP_ADDRESS to any port 7474
# sudo ufw allow from YOUR_IP_ADDRESS to any port 7687
```

### 3. Secure Neo4j Access

If you want to restrict Neo4j to local access only:

```bash
# Edit docker-compose.yml
# Change ports from:
#   - "7474:7474"
#   - "7687:7687"
# To:
#   - "127.0.0.1:7474:7474"
#   - "127.0.0.1:7687:7687"

# Restart Neo4j
docker compose down
docker compose up -d
```

---

## Setup System Service

### Create Systemd Service for API

This ensures the API restarts automatically after reboot.

```bash
# Create service file
sudo tee /etc/systemd/system/graphrag-api.service > /dev/null << 'EOF'
[Unit]
Description=GraphRAG API Service
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=azureuser
WorkingDirectory=/home/azureuser/Startup-Intelligence-Analysis-App
Environment="PATH=/home/azureuser/Startup-Intelligence-Analysis-App/venv/bin"
ExecStart=/home/azureuser/Startup-Intelligence-Analysis-App/venv/bin/uvicorn api:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable graphrag-api

# Start service
sudo systemctl start graphrag-api

# Check status
sudo systemctl status graphrag-api

# View logs
sudo journalctl -u graphrag-api -f
```

### Useful Service Commands

```bash
# Start
sudo systemctl start graphrag-api

# Stop
sudo systemctl stop graphrag-api

# Restart
sudo systemctl restart graphrag-api

# Status
sudo systemctl status graphrag-api

# Logs
sudo journalctl -u graphrag-api -f
```

---

## Monitoring & Maintenance

### 1. Monitor System Resources

```bash
# Install monitoring tools
sudo apt install -y htop ncdu

# Monitor CPU/Memory
htop

# Check disk usage
df -h
ncdu /

# Monitor Docker containers
docker stats
```

### 2. Monitor Neo4j

```bash
# Check Neo4j logs
docker compose logs -f neo4j

# Check Neo4j memory usage
docker stats neo4j

# Access Neo4j shell
docker exec -it neo4j cypher-shell -u neo4j -p your-password
```

### 3. Monitor API Logs

```bash
# If using systemd
sudo journalctl -u graphrag-api -f

# If using nohup
tail -f api.log

# If using screen
screen -r graphrag-api
```

### 4. Backup Neo4j Data

```bash
# Create backup script
cat > ~/backup_neo4j.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/azureuser/neo4j-backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Stop Neo4j
docker compose -f /home/azureuser/Startup-Intelligence-Analysis-App/docker-compose.yml stop neo4j

# Backup data
tar -czf $BACKUP_DIR/neo4j_backup_$DATE.tar.gz -C /var/lib/docker/volumes neo4j_data

# Start Neo4j
docker compose -f /home/azureuser/Startup-Intelligence-Analysis-App/docker-compose.yml start neo4j

echo "Backup completed: $BACKUP_DIR/neo4j_backup_$DATE.tar.gz"
EOF

# Make executable
chmod +x ~/backup_neo4j.sh

# Run backup
~/backup_neo4j.sh

# Setup cron job for daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /home/azureuser/backup_neo4j.sh") | crontab -
```

### 5. Update Application

```bash
cd ~/Startup-Intelligence-Analysis-App

# Pull latest changes
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

### Issue: Cannot Connect to Neo4j

```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Check Neo4j logs
docker compose logs neo4j

# Restart Neo4j
docker compose restart neo4j

# Test connection
docker exec neo4j cypher-shell -u neo4j -p your-password "RETURN 1;"
```

### Issue: API Not Responding

```bash
# Check if API is running
ps aux | grep uvicorn

# Check API logs
sudo journalctl -u graphrag-api -f

# Restart API
sudo systemctl restart graphrag-api

# Check port
sudo netstat -tlnp | grep 8000
```

### Issue: Out of Memory

```bash
# Check memory usage
free -h

# Check which process is using memory
ps aux --sort=-%mem | head

# Adjust Neo4j memory settings in docker-compose.yml
# Reduce heap size:
# NEO4J_dbms_memory_heap_max__size=1G
```

### Issue: Disk Space Full

```bash
# Check disk usage
df -h

# Find large files
du -sh /* | sort -h

# Clean Docker
docker system prune -a

# Clean logs
sudo journalctl --vacuum-time=7d
```

### Issue: OpenAI API Rate Limits

```bash
# Add retry logic or reduce concurrent requests
# Check OpenAI usage dashboard
# Consider using sentence-transformers instead for embeddings
```

---

## Performance Optimization

### 1. Optimize Neo4j Memory

Edit `docker-compose.yml`:

```yaml
environment:
  # For 16GB RAM VM
  - NEO4J_dbms_memory_heap_initial__size=2G
  - NEO4J_dbms_memory_heap_max__size=4G
  - NEO4J_dbms_memory_pagecache_size=4G

  # For 32GB RAM VM
  # - NEO4J_dbms_memory_heap_initial__size=4G
  # - NEO4J_dbms_memory_heap_max__size=8G
  # - NEO4J_dbms_memory_pagecache_size=8G
```

### 2. Use Sentence Transformers Instead of OpenAI

To reduce costs and latency:

```bash
# In .env file
RAG_EMBEDDING_BACKEND=sentence-transformers
SENTENCE_TRANSFORMERS_MODEL=BAAI/bge-small-en-v1.5
```

### 3. Setup Nginx Reverse Proxy (Optional)

```bash
# Install Nginx
sudo apt install -y nginx

# Create config
sudo tee /etc/nginx/sites-available/graphrag << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/graphrag /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Useful URLs

Once deployed, access these URLs:

- **API Documentation**: `http://<your-vm-public-ip>:8000/docs`
- **API Health Check**: `http://<your-vm-public-ip>:8000/health`
- **Neo4j Browser**: `http://<your-vm-public-ip>:7474` (if accessible)

---

## Next Steps

1. **Set up SSL/HTTPS** using Let's Encrypt (if using domain)
2. **Configure automatic backups** to Azure Blob Storage
3. **Set up monitoring** with Azure Monitor or Prometheus
4. **Scale up** VM size if needed for larger datasets
5. **Add authentication** to API endpoints for security

---

## Quick Commands Reference

```bash
# Start Neo4j
cd ~/Startup-Intelligence-Analysis-App && docker compose up -d

# Start API
sudo systemctl start graphrag-api

# Stop API
sudo systemctl stop graphrag-api

# View API logs
sudo journalctl -u graphrag-api -f

# Check Neo4j status
docker compose ps

# View Neo4j logs
docker compose logs -f neo4j

# Backup Neo4j
~/backup_neo4j.sh

# Update application
cd ~/Startup-Intelligence-Analysis-App && git pull && source venv/bin/activate && pip install -r requirements.txt --upgrade && sudo systemctl restart graphrag-api
```

---

**Happy deploying! 🚀**

For more information, see:
- [README.md](README.md) - Complete project documentation
- [HOW_TO_RUN.md](HOW_TO_RUN.md) - Local development guide
- [RAG_DOCUMENTATION.md](RAG_DOCUMENTATION.md) - API reference
