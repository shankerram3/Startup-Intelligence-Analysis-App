# Azure VM Deployment - Complete Guide

Welcome! This document provides a roadmap for deploying your GraphRAG application on Azure VM.

---

## 📚 Available Documentation

I've created comprehensive guides for your Azure deployment:

### 1. **QUICKSTART_AZURE.md** ⚡ (START HERE!)
   - **For**: Quick 5-minute setup
   - **Best for**: Getting started fast
   - **Includes**: Step-by-step commands optimized for your VM specs
   - **Start with this if**: You want to get up and running immediately

### 2. **AZURE_DEPLOYMENT_GUIDE.md** 📖
   - **For**: Complete production deployment
   - **Best for**: Understanding the full setup process
   - **Includes**: Detailed explanations, troubleshooting, monitoring, backups
   - **Use this when**: You need comprehensive documentation and production setup

### 3. **SSL_SETUP_GUIDE.md** 🔒
   - **For**: Setting up HTTPS with SSL certificates
   - **Best for**: Securing your API with HTTPS
   - **Includes**: Let's Encrypt setup, Nginx configuration, custom domains
   - **Use this when**: You need HTTPS for production or custom domain

### 4. **AURA_DB_SETUP.md** ☁️ (RECOMMENDED FOR SPOT VM!)
   - **For**: Using Neo4j Aura DB (managed cloud database)
   - **Best for**: Spot VM deployments - data stays safe even if VM is evicted
   - **Includes**: Complete Aura setup, no Docker needed, saves 1-2GB RAM
   - **Use this when**: You want maximum data safety and minimal VM resources

### 5. **azure_setup.sh** 🤖
   - **For**: Automated setup with self-hosted Neo4j (Docker)
   - **Best for**: Scripted deployment with local database
   - **Includes**: Complete system setup with Docker Neo4j
   - **Use this when**: You want everything on your VM

### 6. **azure_setup_aura.sh** 🤖☁️ (NEW!)
   - **For**: Automated setup with Neo4j Aura DB
   - **Best for**: Quick setup with cloud database (no Docker!)
   - **Includes**: System setup + Aura DB connection
   - **Use this when**: You want managed database with automated setup

---

## ☁️ Database Choice: Self-Hosted vs Aura DB

**IMPORTANT**: Choose your database deployment strategy:

### Option 1: Neo4j Aura DB ☁️ (RECOMMENDED for Spot VM)

**Pros:**
- ✅ **Data survives VM eviction** - Your knowledge graph is safe in the cloud
- ✅ **No Docker needed** - Saves 1-2GB RAM, 5-10GB disk
- ✅ **Automatic backups** - Daily backups on Professional tier
- ✅ **Fully managed** - No database maintenance
- ✅ **Free tier available** - 50MB storage, 200k nodes (good for 100-500 articles)

**Cons:**
- 💰 Professional tier costs ~$65/month (after free tier)
- 🌐 Requires internet connectivity
- ⏱️ Slightly higher latency than local

**When to use:**
- ✅ Spot VM (can be evicted)
- ✅ Limited VM resources (2-4GB RAM)
- ✅ Want managed backups
- ✅ Testing/development (free tier)

**Setup:** See [AURA_DB_SETUP.md](AURA_DB_SETUP.md) or run `bash azure_setup_aura.sh`

### Option 2: Self-Hosted Neo4j (Docker) 🐳

**Pros:**
- ✅ **Lower cost** - Only VM cost (~$15-30/month)
- ✅ **Full control** - Complete database access
- ✅ **No external dependencies** - Everything local
- ✅ **Lower latency** - Direct local access

**Cons:**
- ⚠️ **Data at risk** - Lost if VM is evicted
- 📦 **Uses VM resources** - 1-2GB RAM, 5-10GB disk
- 🔧 **Manual maintenance** - Updates, backups, monitoring
- 💾 **Manual backups required** - Must setup backup scripts

**When to use:**
- ✅ Regular VM (not Spot)
- ✅ Sufficient resources (8GB+ RAM)
- ✅ Want full control
- ✅ Need offline capability

**Setup:** See [QUICKSTART_AZURE.md](QUICKSTART_AZURE.md) or run `bash azure_setup.sh`

### Quick Comparison

| Feature | Self-Hosted (Docker) | Aura DB (Cloud) |
|---------|---------------------|-----------------|
| **VM Memory** | 1-2GB used | 0GB used ✅ |
| **VM Disk** | 5-10GB used | 0GB used ✅ |
| **Data Safety (Spot VM)** | ⚠️ At risk | ✅ Safe in cloud |
| **Backups** | Manual setup | ✅ Automatic |
| **Cost** | VM only (~$15-30) | VM + Aura (~$80-95) |
| **Maintenance** | Manual | ✅ Managed |
| **Free tier** | N/A | ✅ Available |

**Recommendation for your Spot VM:** Use **Aura DB** to protect your data from eviction!

---

## 🚀 Quick Start (Choose Your Path)

### Path A: Aura DB Setup ☁️ (Recommended for Spot VM!)

```bash
# 1. Create Neo4j Aura DB instance
# Go to: https://neo4j.com/cloud/aura/
# Create free account and database
# Save credentials: URI, username, password

# 2. SSH into your Azure VM
ssh azureuser@<your-vm-ip>

# 3. Clone this repository
git clone https://github.com/shankerram3/Startup-Intelligence-Analysis-App.git
cd Startup-Intelligence-Analysis-App

# 4. Run Aura DB setup script
bash azure_setup_aura.sh

# 5. Enter your Aura DB credentials when prompted
# The script will guide you through the rest!
```

**Benefits:** No Docker, saves 1-2GB RAM, data safe from VM eviction!

### Path B: Self-Hosted Setup 🐳 (Local Database)

```bash
# 1. SSH into your Azure VM
ssh azureuser@<your-vm-ip>

# 2. Clone this repository
git clone https://github.com/shankerram3/Startup-Intelligence-Analysis-App.git
cd Startup-Intelligence-Analysis-App

# 3. Run self-hosted setup script
bash azure_setup.sh

# 4. Follow the on-screen instructions
# Installs Docker + Neo4j locally
```

**Benefits:** Lower cost, full control, no external dependencies.

### Path C: Manual Setup (Advanced Users)

Follow **QUICKSTART_AZURE.md** or **AURA_DB_SETUP.md** for guided manual setup.

---

## 📊 Your Azure VM Specifications

Based on your VM configuration:

```
Name:     GraphRAG
Size:     Standard_F2ams_v6
CPUs:     2 vCPUs
RAM:      ~4 GB
Disk:     30 GB Premium SSD
OS:       Ubuntu 24.04 LTS
Type:     Spot VM (can be evicted!)
Region:   East US 2
```

### ⚠️ Important: Spot VM Considerations

Your VM is a **Spot instance** which means:
- ✅ **Much cheaper** than regular VMs (up to 90% savings)
- ⚠️ **Can be evicted** by Azure with 30 seconds notice
- 🔄 **Requires regular backups** to prevent data loss

**Solution**: The setup script includes automated backup functionality. Run daily backups with `~/backup_neo4j.sh`

---

## 🎯 What Gets Deployed

After following the guides, you'll have:

### Services
- ✅ **Neo4j Database** (Graph database) - Port 7474, 7687
- ✅ **GraphRAG REST API** (FastAPI) - Port 8000
- ✅ **Nginx** (Reverse proxy, optional) - Port 80, 443

### Features
- ✅ **Knowledge Graph** with TechCrunch articles
- ✅ **Entity Extraction** using GPT-4
- ✅ **Semantic Search** with embeddings
- ✅ **REST API** with 40+ endpoints
- ✅ **Automatic Backups**
- ✅ **Systemd Service** (auto-restart)
- ✅ **Firewall Configuration**

### Access URLs (After Deployment)
```
API Documentation:  http://<your-vm-ip>:8000/docs
API Health:         http://<your-vm-ip>:8000/health
Neo4j Browser:      http://<your-vm-ip>:7474
```

---

## 📋 Deployment Checklist

Use this checklist to track your progress:

### Phase 1: Initial Setup
- [ ] SSH into Azure VM
- [ ] Clone repository
- [ ] Run `azure_setup.sh` or follow QUICKSTART_AZURE.md
- [ ] Configure `.env` with OpenAI API key
- [ ] Log out and back in (for Docker permissions)

### Phase 2: Install Dependencies
- [ ] Create Python virtual environment
- [ ] Install requirements.txt
- [ ] Setup Crawl4AI browser (if scraping)

### Phase 3: Build Knowledge Graph
- [ ] Run pipeline with test data (5-10 articles)
- [ ] Generate embeddings
- [ ] Verify graph in Neo4j Browser

### Phase 4: Deploy API
- [ ] Start API service
- [ ] Test API endpoints
- [ ] Verify from local machine

### Phase 5: Secure & Optimize
- [ ] Configure Azure Network Security Group (NSG)
- [ ] Setup firewall rules
- [ ] Setup SSL/HTTPS (optional, see SSL_SETUP_GUIDE.md)
- [ ] Configure automated backups
- [ ] Test backup script

---

## 🔧 Essential Commands

Once deployed, use these commands:

```bash
# Start all services
~/start_graphrag.sh

# Stop all services
~/stop_graphrag.sh

# Check status
~/status_graphrag.sh

# Backup database
~/backup_neo4j.sh

# View API logs
sudo journalctl -u graphrag-api -f

# View Neo4j logs
cd ~/Startup-Intelligence-Analysis-App
docker compose logs -f neo4j

# Restart API
sudo systemctl restart graphrag-api
```

---

## 🌐 Network & Security

### Ports to Open in Azure NSG

| Port | Service | Access | Required |
|------|---------|--------|----------|
| 22 | SSH | Your IP only | Yes |
| 8000 | API | Public or restricted | Yes |
| 7474 | Neo4j Browser | Your IP only | Optional |
| 7687 | Neo4j Bolt | Your IP only | Optional |
| 80 | HTTP | Public | If using SSL |
| 443 | HTTPS | Public | If using SSL |

### Configure in Azure Portal
1. Go to **VM → Networking → Add inbound port rule**
2. Add each required port
3. Restrict SSH and Neo4j to your IP address

---

## 💡 Tips for Your VM Size

Your VM has 2 vCPUs and 4GB RAM. Here are optimization tips:

### 1. Start with Small Datasets
```bash
# Process only 10 articles initially
python pipeline.py --skip-scraping --max-articles 10
```

### 2. Use Sentence Transformers (Saves API costs)
```bash
# In .env file
RAG_EMBEDDING_BACKEND=sentence-transformers
```

### 3. Monitor Resources
```bash
# Check memory usage
free -h

# Check disk space
df -h

# Monitor processes
htop
```

### 4. Consider Upgrading If Needed
- **For 100-1000 articles**: Current VM is fine
- **For 1000-10000 articles**: Upgrade to Standard_D4s_v3 (4 vCPU, 16GB)
- **For 10000+ articles**: Upgrade to Standard_D8s_v3 (8 vCPU, 32GB)

---

## 📞 Getting Help

### If Something Goes Wrong

1. **Check the logs**:
   ```bash
   sudo journalctl -u graphrag-api -f
   docker compose logs -f neo4j
   ```

2. **Check service status**:
   ```bash
   ~/status_graphrag.sh
   ```

3. **Restart services**:
   ```bash
   ~/stop_graphrag.sh
   ~/start_graphrag.sh
   ```

4. **Consult troubleshooting sections**:
   - AZURE_DEPLOYMENT_GUIDE.md → Troubleshooting section
   - SSL_SETUP_GUIDE.md → Troubleshooting section

### Common Issues

| Issue | Solution |
|-------|----------|
| Neo4j won't start | Check Docker: `docker compose logs neo4j` |
| API returns 502 | Check if API is running: `sudo systemctl status graphrag-api` |
| Out of disk space | Clean Docker: `docker system prune -a` |
| Out of memory | Reduce Neo4j memory in docker-compose.yml |
| Can't access from internet | Check Azure NSG rules |

---

## 🎓 Learning Resources

### Understanding the Stack

- **Neo4j**: Graph database storing entities and relationships
- **FastAPI**: Python web framework for REST API
- **Docker**: Containerization for Neo4j
- **Nginx**: Reverse proxy for HTTPS (optional)
- **Systemd**: Linux service manager for auto-restart

### Documentation Order

1. Start with **QUICKSTART_AZURE.md** to deploy
2. Read **AZURE_DEPLOYMENT_GUIDE.md** for deep understanding
3. Add HTTPS with **SSL_SETUP_GUIDE.md** when ready
4. Explore main **README.md** for application features
5. Check **RAG_DOCUMENTATION.md** for API reference

---

## 📈 Next Steps After Deployment

### Immediate Next Steps
1. ✅ Test your API with sample queries
2. ✅ Access Neo4j Browser and explore the graph
3. ✅ Setup automated daily backups
4. ✅ Test backup and restore process

### Within First Week
1. Build larger knowledge graph (100+ articles)
2. Test semantic search functionality
3. Setup monitoring (disk space, memory)
4. Configure SSL/HTTPS if using custom domain

### Production Readiness
1. Setup authentication for API endpoints
2. Configure rate limiting
3. Setup Azure Blob Storage for backups
4. Add monitoring with Azure Monitor
5. Setup CI/CD pipeline for updates
6. Consider upgrading from Spot VM to regular VM

---

## 🚨 Critical Reminders

1. **Your VM is a Spot instance** - It can be evicted!
   - ⚠️ Setup backups immediately
   - ⚠️ Test backup restoration
   - ⚠️ Consider Azure Blob Storage for backups

2. **Secure your endpoints**:
   - ✅ Restrict SSH to your IP only
   - ✅ Restrict Neo4j ports to your IP only
   - ✅ Use strong passwords
   - ✅ Keep your .env file private

3. **Monitor resources**:
   - ⚠️ 30 GB disk fills up quickly
   - ⚠️ 4 GB RAM is limited for large datasets
   - ⚠️ Watch for eviction notices

---

## 🎉 You're Ready!

Choose your path:

- **Quick Setup**: Run `bash azure_setup.sh`
- **Manual Setup**: Follow `QUICKSTART_AZURE.md`
- **Deep Dive**: Read `AZURE_DEPLOYMENT_GUIDE.md`
- **Add HTTPS**: Follow `SSL_SETUP_GUIDE.md`

---

## 📝 Quick Reference Card

```bash
# === DEPLOYMENT ===
bash azure_setup.sh                    # Automated setup
# OR
# Follow QUICKSTART_AZURE.md           # Manual setup

# === SERVICES ===
~/start_graphrag.sh                    # Start everything
~/stop_graphrag.sh                     # Stop everything
~/status_graphrag.sh                   # Check status

# === OPERATIONS ===
sudo systemctl restart graphrag-api    # Restart API
docker compose restart neo4j           # Restart Neo4j
~/backup_neo4j.sh                      # Backup database

# === LOGS ===
sudo journalctl -u graphrag-api -f     # API logs
docker compose logs -f neo4j           # Neo4j logs

# === MONITORING ===
htop                                   # CPU/Memory
df -h                                  # Disk space
free -h                                # Memory usage
docker stats                           # Container stats

# === URLS ===
# http://<your-vm-ip>:8000/docs        # API documentation
# http://<your-vm-ip>:8000/health      # Health check
# http://<your-vm-ip>:7474             # Neo4j browser
```

---

**Good luck with your deployment! 🚀**

If you run into any issues, check the troubleshooting sections in the guides or refer back to this document.
