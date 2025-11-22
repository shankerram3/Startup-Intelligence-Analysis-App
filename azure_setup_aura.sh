#!/bin/bash
# Azure VM Setup Script for GraphRAG with Neo4j Aura DB
# This version does NOT install Docker - uses Aura DB cloud service
#
# Usage: bash azure_setup_aura.sh

set -e  # Exit on error

echo "========================================="
echo "GraphRAG Azure VM Setup (Aura DB)"
echo "========================================="
echo ""
echo "This script sets up GraphRAG WITHOUT Docker"
echo "You'll use Neo4j Aura DB (cloud database)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root"
    exit 1
fi

# Get VM public IP (if available)
VM_PUBLIC_IP=$(curl -s ifconfig.me || echo "unknown")

print_info "VM Public IP: $VM_PUBLIC_IP"
echo ""

# ============================================================================
# STEP 1: Check for Aura DB Credentials
# ============================================================================
echo "========================================="
echo "Step 1: Neo4j Aura DB Setup"
echo "========================================="
echo ""

print_warning "Before continuing, you need Neo4j Aura DB credentials!"
echo ""
echo "If you don't have Aura DB yet:"
echo "  1. Go to: https://neo4j.com/cloud/aura/"
echo "  2. Sign up for free account"
echo "  3. Create a new database (Free or Professional tier)"
echo "  4. Save the credentials (URI, username, password)"
echo ""
echo "Your Aura DB credentials will look like:"
echo "  URI: neo4j+s://xxxxx.databases.neo4j.io"
echo "  Username: neo4j"
echo "  Password: [generated-password]"
echo ""

read -p "Do you have your Aura DB credentials ready? (y/n): " has_aura

if [ "$has_aura" != "y" ] && [ "$has_aura" != "Y" ]; then
    print_warning "Please create your Aura DB instance first, then run this script again."
    echo ""
    echo "Quick guide:"
    echo "  cat AURA_DB_SETUP.md"
    echo ""
    exit 0
fi

print_status "Great! Let's continue with the setup"
echo ""

# Collect Aura DB credentials
echo "Please enter your Aura DB credentials:"
echo ""

read -p "Aura DB URI (e.g., neo4j+s://xxxxx.databases.neo4j.io): " AURA_URI
read -p "Aura DB Username (usually 'neo4j'): " AURA_USER
read -sp "Aura DB Password: " AURA_PASSWORD
echo ""

# Validate inputs
if [ -z "$AURA_URI" ] || [ -z "$AURA_USER" ] || [ -z "$AURA_PASSWORD" ]; then
    print_error "All credentials are required!"
    exit 1
fi

# Check URI format
if [[ ! "$AURA_URI" =~ ^neo4j\+s:// ]]; then
    print_error "Aura DB URI should start with 'neo4j+s://'"
    print_warning "Your URI: $AURA_URI"
    read -p "Continue anyway? (y/n): " continue_anyway
    if [ "$continue_anyway" != "y" ]; then
        exit 1
    fi
fi

print_status "Aura DB credentials collected"
echo ""

# OpenAI API Key
read -sp "OpenAI API Key (sk-...): " OPENAI_KEY
echo ""

if [ -z "$OPENAI_KEY" ]; then
    print_warning "No OpenAI API key provided. You can add it later in .env file"
    OPENAI_KEY="sk-your-openai-api-key-here"
fi

echo ""

# ============================================================================
# STEP 2: Update System
# ============================================================================
echo "========================================="
echo "Step 2: Updating System"
echo "========================================="
echo ""

sudo apt update && sudo apt upgrade -y
print_status "System updated"
echo ""

# ============================================================================
# STEP 3: Install Essential Tools (NO DOCKER!)
# ============================================================================
echo "========================================="
echo "Step 3: Installing Essential Tools"
echo "========================================="
echo ""

sudo apt install -y \
    build-essential \
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools \
    software-properties-common \
    ca-certificates \
    ncdu \
    unzip \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev

print_status "Essential tools installed (NO Docker - using Aura DB!)"
echo ""

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_info "Python $PYTHON_VERSION installed"
echo ""

# ============================================================================
# STEP 4: Setup Project Directory
# ============================================================================
echo "========================================="
echo "Step 4: Setting Up Project"
echo "========================================="
echo ""

PROJECT_DIR="$HOME/Startup-Intelligence-Analysis-App"

# Check if directory already exists
if [ -d "$PROJECT_DIR" ]; then
    print_warning "Project directory already exists: $PROJECT_DIR"
    read -p "Do you want to use existing directory? (y/n): " use_existing

    if [ "$use_existing" == "y" ] || [ "$use_existing" == "Y" ]; then
        cd "$PROJECT_DIR"
        print_status "Using existing project directory"
    else
        print_error "Please remove or rename existing directory first"
        exit 1
    fi
else
    print_warning "Project directory not found."
    echo ""
    echo "Cloning from GitHub..."

    git clone https://github.com/shankerram3/Startup-Intelligence-Analysis-App.git "$PROJECT_DIR" || {
        print_error "Failed to clone repository"
        echo ""
        echo "Please clone manually:"
        echo "  git clone https://github.com/shankerram3/Startup-Intelligence-Analysis-App.git"
        exit 1
    }

    cd "$PROJECT_DIR"
    print_status "Repository cloned"
fi

echo ""

# ============================================================================
# STEP 5: Create .env File with Aura DB Configuration
# ============================================================================
echo "========================================="
echo "Step 5: Creating Configuration"
echo "========================================="
echo ""

cat > "$PROJECT_DIR/.env" << EOF
# OpenAI API (Required for entity extraction and LLM generation)
OPENAI_API_KEY=$OPENAI_KEY

# Neo4j Aura DB Connection (Cloud Database)
NEO4J_URI=$AURA_URI
NEO4J_USER=$AURA_USER
NEO4J_PASSWORD=$AURA_PASSWORD

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Embedding Backend (sentence-transformers recommended for cost savings)
RAG_EMBEDDING_BACKEND=sentence-transformers
SENTENCE_TRANSFORMERS_MODEL=BAAI/bge-small-en-v1.5

# Verbose Logging
RAG_VERBOSE=1
EOF

chmod 600 "$PROJECT_DIR/.env"
print_status ".env file created and secured"
echo ""

# ============================================================================
# STEP 6: Install Python Dependencies
# ============================================================================
echo "========================================="
echo "Step 6: Installing Python Dependencies"
echo "========================================="
echo ""

cd "$PROJECT_DIR"

# Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_info "Virtual environment already exists"
fi

# Activate and install
source venv/bin/activate

pip install --upgrade pip setuptools wheel
print_status "Pip upgraded"

echo ""
echo "Installing requirements (this may take 5-10 minutes)..."
pip install -r requirements.txt

print_status "Python dependencies installed"
echo ""

# ============================================================================
# STEP 7: Test Aura DB Connection
# ============================================================================
echo "========================================="
echo "Step 7: Testing Aura DB Connection"
echo "========================================="
echo ""

python -c "
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv('NEO4J_URI')
user = os.getenv('NEO4J_USER')
password = os.getenv('NEO4J_PASSWORD')

print(f'Testing connection to: {uri}')
print(f'Username: {user}')
print()

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()
    print('✅ Successfully connected to Aura DB!')

    # Get version info
    with driver.session() as session:
        result = session.run('CALL dbms.components() YIELD name, versions')
        for record in result:
            print(f'   Database: {record[\"name\"]} {record[\"versions\"][0]}')

    driver.close()
except Exception as e:
    print(f'❌ Connection failed: {e}')
    print()
    print('Please check:')
    print('  1. Aura DB URI is correct')
    print('  2. Username and password are correct')
    print('  3. Aura DB instance is running (not paused)')
    print('  4. VM has internet connectivity')
    exit(1)
"

if [ $? -eq 0 ]; then
    print_status "Aura DB connection test successful"
else
    print_error "Aura DB connection test failed"
    echo "Please check your credentials and try again"
    exit 1
fi

echo ""

# ============================================================================
# STEP 8: Configure Firewall
# ============================================================================
echo "========================================="
echo "Step 8: Configuring Firewall"
echo "========================================="
echo ""

sudo ufw --force enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8000/tcp  # API

# No Neo4j ports needed with Aura!

print_status "Firewall configured (SSH, API only)"
print_info "No Neo4j ports needed - using Aura DB!"
echo ""

# ============================================================================
# STEP 9: Create Systemd Service
# ============================================================================
echo "========================================="
echo "Step 9: Creating API Service"
echo "========================================="
echo ""

sudo tee /etc/systemd/system/graphrag-api.service > /dev/null << EOF
[Unit]
Description=GraphRAG API Service
After=network.target

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
# STEP 10: Create Helper Scripts
# ============================================================================
echo "========================================="
echo "Step 10: Creating Helper Scripts"
echo "========================================="
echo ""

# Start script (no Docker needed!)
cat > "$HOME/start_graphrag.sh" << EOF
#!/bin/bash
cd $PROJECT_DIR
sudo systemctl start graphrag-api
echo "GraphRAG API started"
sudo systemctl status graphrag-api --no-pager
EOF
chmod +x "$HOME/start_graphrag.sh"

# Stop script
cat > "$HOME/stop_graphrag.sh" << EOF
#!/bin/bash
sudo systemctl stop graphrag-api
echo "GraphRAG API stopped"
EOF
chmod +x "$HOME/stop_graphrag.sh"

# Status script
cat > "$HOME/status_graphrag.sh" << EOF
#!/bin/bash
echo "=== API Status ==="
sudo systemctl status graphrag-api --no-pager

echo ""
echo "=== Aura DB Connection ==="
cd $PROJECT_DIR
source venv/bin/activate
python -c "
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
load_dotenv()
try:
    driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD')))
    driver.verify_connectivity()
    print('✅ Connected to Aura DB')

    with driver.session() as session:
        result = session.run('MATCH (n) RETURN count(n) as count')
        count = result.single()['count']
        print(f'   Total nodes: {count}')

        result = session.run('MATCH ()-[r]->() RETURN count(r) as count')
        rels = result.single()['count']
        print(f'   Total relationships: {rels}')

    driver.close()
except Exception as e:
    print(f'❌ Aura DB error: {e}')
" 2>/dev/null

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
echo "========================================="
echo "Setup Complete! 🎉"
echo "========================================="
echo ""
print_status "What's been configured:"
echo "  ✓ System packages updated"
echo "  ✓ Python 3 and dependencies installed"
echo "  ✓ Neo4j Aura DB connection configured"
echo "  ✓ Firewall configured"
echo "  ✓ Systemd service created"
echo "  ✓ Helper scripts created"
echo ""
print_info "Benefits of using Aura DB:"
echo "  ✓ No Docker needed - saves 1-2GB RAM"
echo "  ✓ Data safe even if VM is evicted"
echo "  ✓ Automatic backups (Professional tier)"
echo "  ✓ No database maintenance required"
echo ""
print_warning "Next steps:"
echo ""
echo "1. Build your knowledge graph:"
echo "   cd $PROJECT_DIR"
echo "   source venv/bin/activate"
echo "   python pipeline.py --scrape-category startups --scrape-max-pages 1 --max-articles 5"
echo ""
echo "2. Generate embeddings:"
echo "   python -c 'from neo4j import GraphDatabase; from utils.embedding_generator import EmbeddingGenerator; import os; from dotenv import load_dotenv; load_dotenv(); driver = GraphDatabase.driver(os.getenv(\"NEO4J_URI\"), auth=(os.getenv(\"NEO4J_USER\"), os.getenv(\"NEO4J_PASSWORD\"))); generator = EmbeddingGenerator(driver, embedding_model=\"sentence_transformers\"); generator.generate_embeddings_for_all_entities(); driver.close()'"
echo ""
echo "3. Start the API:"
echo "   sudo systemctl start graphrag-api"
echo ""
echo "4. Test the API:"
echo "   curl http://localhost:8000/health"
echo "   curl http://$VM_PUBLIC_IP:8000/health"
echo ""
echo "5. Access your services:"
echo "   - API Docs: http://$VM_PUBLIC_IP:8000/docs"
echo "   - API Health: http://$VM_PUBLIC_IP:8000/health"
echo "   - Aura Console: https://console.neo4j.io/"
echo ""
echo "Helper commands:"
echo "   ~/start_graphrag.sh    - Start API"
echo "   ~/stop_graphrag.sh     - Stop API"
echo "   ~/status_graphrag.sh   - Check status"
echo ""
print_info "Azure Network Security Group (NSG):"
echo "  Make sure to open these ports in Azure Portal:"
echo "  - Port 22 (SSH) - Restrict to your IP"
echo "  - Port 8000 (API) - Public or restricted"
echo ""
print_warning "Remember: Your data is in Aura DB cloud"
echo "  Even if this VM is evicted, your data is safe!"
echo ""
echo "========================================="
echo ""
echo "For more information, see:"
echo "  - AURA_DB_SETUP.md (Aura DB guide)"
echo "  - QUICKSTART_AZURE.md (Quick start)"
echo "  - AZURE_README.md (Overview)"
echo ""
