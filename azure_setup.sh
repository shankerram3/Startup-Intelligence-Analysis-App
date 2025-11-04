#!/bin/bash
# Azure VM Setup Script for GraphRAG Application
# For Ubuntu 24.04 LTS on Standard_F2ams_v6 (2 vCPUs, 4GB RAM)
#
# Usage: bash azure_setup.sh
# Or: curl -sSL https://raw.githubusercontent.com/yourusername/repo/main/azure_setup.sh | bash

set -e  # Exit on error

echo "=================================="
echo "GraphRAG Azure VM Setup"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root"
    exit 1
fi

# Get VM public IP (if available)
VM_PUBLIC_IP=$(curl -s ifconfig.me || echo "unknown")

print_status "Starting setup on Azure VM (Public IP: $VM_PUBLIC_IP)"
echo ""

# ============================================================================
# STEP 1: Update System
# ============================================================================
echo "Step 1: Updating system packages..."
sudo apt update && sudo apt upgrade -y
print_status "System updated"
echo ""

# ============================================================================
# STEP 2: Install Essential Tools
# ============================================================================
echo "Step 2: Installing essential tools..."
sudo apt install -y \
    build-essential \
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    ncdu \
    unzip
print_status "Essential tools installed"
echo ""

# ============================================================================
# STEP 3: Install Python 3.11
# ============================================================================
echo "Step 3: Installing Python 3.11..."

# Ubuntu 24.04 should have Python 3.12 by default, but we'll ensure 3.11 is available
sudo apt install -y python3 python3-pip python3-venv python3-dev

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_status "Python $PYTHON_VERSION installed"
echo ""

# ============================================================================
# STEP 4: Install Docker
# ============================================================================
echo "Step 4: Installing Docker..."

# Remove old versions
sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Install Docker
curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
sudo sh /tmp/get-docker.sh
rm /tmp/get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

print_status "Docker installed"
echo ""

# ============================================================================
# STEP 5: Install Docker Compose
# ============================================================================
echo "Step 5: Installing Docker Compose..."
sudo apt install -y docker-compose-plugin

DOCKER_COMPOSE_VERSION=$(docker compose version | cut -d' ' -f4 || echo "unknown")
print_status "Docker Compose $DOCKER_COMPOSE_VERSION installed"
echo ""

# ============================================================================
# STEP 6: Setup Project Directory
# ============================================================================
echo "Step 6: Setting up project directory..."

# Check if directory already exists
if [ -d "$HOME/Startup-Intelligence-Analysis-App" ]; then
    print_warning "Project directory already exists. Skipping clone."
    cd "$HOME/Startup-Intelligence-Analysis-App"
else
    # Clone repository (user needs to provide repo URL)
    print_warning "Project directory not found."
    echo "Please clone your repository manually:"
    echo "  git clone https://github.com/yourusername/Startup-Intelligence-Analysis-App.git"
    echo "Or upload files using scp:"
    echo "  scp -r /local/path azureuser@$VM_PUBLIC_IP:~/"
    echo ""

    # Create directory for now
    mkdir -p "$HOME/Startup-Intelligence-Analysis-App"
    cd "$HOME/Startup-Intelligence-Analysis-App"
fi

PROJECT_DIR="$HOME/Startup-Intelligence-Analysis-App"
print_status "Project directory: $PROJECT_DIR"
echo ""

# ============================================================================
# STEP 7: Create Docker Compose for Neo4j
# ============================================================================
echo "Step 7: Creating Neo4j Docker Compose configuration..."

cat > "$PROJECT_DIR/docker-compose.yml" << 'EOF'
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
      # IMPORTANT: Change this password!
      - NEO4J_AUTH=neo4j/ChangeThisPassword123!
      - NEO4J_PLUGINS=["apoc"]
      # Memory settings optimized for 4GB RAM VM
      - NEO4J_dbms_memory_heap_initial__size=512M
      - NEO4J_dbms_memory_heap_max__size=1G
      - NEO4J_dbms_memory_pagecache_size=512M
      - NEO4J_dbms_security_procedures_unrestricted=apoc.*
      - NEO4J_dbms_security_procedures_allowlist=apoc.*
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

print_status "Neo4j Docker Compose created"
print_warning "IMPORTANT: Edit docker-compose.yml and change the Neo4j password!"
echo ""

# ============================================================================
# STEP 8: Start Neo4j
# ============================================================================
echo "Step 8: Starting Neo4j..."

cd "$PROJECT_DIR"

# Check if Docker is accessible without sudo
if ! docker ps > /dev/null 2>&1; then
    print_warning "Docker requires group membership. You may need to log out and back in."
    print_warning "Attempting to start Neo4j with sudo for now..."
    sudo docker compose up -d
else
    docker compose up -d
fi

# Wait for Neo4j to start
echo "Waiting for Neo4j to start (30 seconds)..."
sleep 30

print_status "Neo4j started"
echo ""

# ============================================================================
# STEP 9: Create .env Template
# ============================================================================
echo "Step 9: Creating .env template..."

cat > "$PROJECT_DIR/.env.template" << 'EOF'
# OpenAI API (Required for entity extraction and LLM generation)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Neo4j Connection (Required)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=ChangeThisPassword123!

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Embedding Backend (sentence-transformers recommended for cost savings)
RAG_EMBEDDING_BACKEND=sentence-transformers
SENTENCE_TRANSFORMERS_MODEL=BAAI/bge-small-en-v1.5

# Verbose Logging
RAG_VERBOSE=1
EOF

if [ ! -f "$PROJECT_DIR/.env" ]; then
    cp "$PROJECT_DIR/.env.template" "$PROJECT_DIR/.env"
    chmod 600 "$PROJECT_DIR/.env"
    print_status ".env file created from template"
    print_warning "IMPORTANT: Edit .env file and add your OpenAI API key!"
else
    print_warning ".env file already exists. Not overwriting."
fi

echo ""

# ============================================================================
# STEP 10: Configure Firewall
# ============================================================================
echo "Step 10: Configuring firewall..."

sudo ufw --force enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8000/tcp  # API
sudo ufw allow 7474/tcp  # Neo4j Browser
sudo ufw allow 7687/tcp  # Neo4j Bolt

print_status "Firewall configured"
echo ""

# ============================================================================
# STEP 11: Create Systemd Service
# ============================================================================
echo "Step 11: Creating systemd service for API..."

sudo tee /etc/systemd/system/graphrag-api.service > /dev/null << EOF
[Unit]
Description=GraphRAG API Service
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/uvicorn api:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable graphrag-api

print_status "Systemd service created (not started yet)"
echo ""

# ============================================================================
# STEP 12: Create Backup Script
# ============================================================================
echo "Step 12: Creating backup script..."

cat > "$HOME/backup_neo4j.sh" << 'EOF'
#!/bin/bash
BACKUP_DIR="$HOME/neo4j-backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

echo "Creating Neo4j backup..."

# Stop Neo4j
cd ~/Startup-Intelligence-Analysis-App
docker compose stop neo4j

# Backup data using docker volume
docker run --rm \
  -v neo4j_data:/data \
  -v $BACKUP_DIR:/backup \
  ubuntu tar czf /backup/neo4j_backup_$DATE.tar.gz -C /data .

# Start Neo4j
docker compose start neo4j

echo "Backup completed: $BACKUP_DIR/neo4j_backup_$DATE.tar.gz"

# Keep only last 7 backups
cd $BACKUP_DIR
ls -t neo4j_backup_*.tar.gz | tail -n +8 | xargs -r rm

echo "Old backups cleaned up (keeping last 7)"
EOF

chmod +x "$HOME/backup_neo4j.sh"

print_status "Backup script created: ~/backup_neo4j.sh"
echo ""

# ============================================================================
# STEP 13: Create Helper Scripts
# ============================================================================
echo "Step 13: Creating helper scripts..."

# Start script
cat > "$HOME/start_graphrag.sh" << EOF
#!/bin/bash
cd $PROJECT_DIR
docker compose up -d
sleep 5
sudo systemctl start graphrag-api
echo "GraphRAG started"
sudo systemctl status graphrag-api
EOF
chmod +x "$HOME/start_graphrag.sh"

# Stop script
cat > "$HOME/stop_graphrag.sh" << EOF
#!/bin/bash
sudo systemctl stop graphrag-api
cd $PROJECT_DIR
docker compose down
echo "GraphRAG stopped"
EOF
chmod +x "$HOME/stop_graphrag.sh"

# Status script
cat > "$HOME/status_graphrag.sh" << EOF
#!/bin/bash
echo "=== Neo4j Status ==="
cd $PROJECT_DIR
docker compose ps

echo ""
echo "=== API Status ==="
sudo systemctl status graphrag-api --no-pager

echo ""
echo "=== Disk Usage ==="
df -h | grep -E "Filesystem|/$"

echo ""
echo "=== Memory Usage ==="
free -h
EOF
chmod +x "$HOME/status_graphrag.sh"

print_status "Helper scripts created:"
echo "  - ~/start_graphrag.sh"
echo "  - ~/stop_graphrag.sh"
echo "  - ~/status_graphrag.sh"
echo ""

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
print_status "What's been installed:"
echo "  ✓ System packages updated"
echo "  ✓ Python 3 installed"
echo "  ✓ Docker and Docker Compose installed"
echo "  ✓ Neo4j database configured and started"
echo "  ✓ Firewall configured"
echo "  ✓ Systemd service created"
echo "  ✓ Backup and helper scripts created"
echo ""
print_warning "Next steps:"
echo ""
echo "1. LOG OUT AND BACK IN to apply Docker group permissions:"
echo "   exit"
echo "   ssh azureuser@$VM_PUBLIC_IP"
echo ""
echo "2. Clone/upload your project code to:"
echo "   $PROJECT_DIR"
echo ""
echo "3. Edit the .env file with your API keys:"
echo "   vim $PROJECT_DIR/.env"
echo ""
echo "4. Install Python dependencies:"
echo "   cd $PROJECT_DIR"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo ""
echo "5. Build the knowledge graph:"
echo "   source venv/bin/activate"
echo "   python pipeline.py --scrape-category startups --scrape-max-pages 1 --max-articles 5"
echo ""
echo "6. Start the API:"
echo "   sudo systemctl start graphrag-api"
echo ""
echo "7. Access your services:"
echo "   - API: http://$VM_PUBLIC_IP:8000/docs"
echo "   - Neo4j: http://$VM_PUBLIC_IP:7474"
echo ""
echo "Helper commands:"
echo "   ~/start_graphrag.sh    - Start all services"
echo "   ~/stop_graphrag.sh     - Stop all services"
echo "   ~/status_graphrag.sh   - Check status"
echo "   ~/backup_neo4j.sh      - Backup Neo4j database"
echo ""
print_warning "IMPORTANT: This is a SPOT VM - it can be evicted!"
echo "  - Setup regular backups: ~/backup_neo4j.sh"
echo "  - Consider Azure Blob Storage for backup storage"
echo ""
echo "=================================="
