#!/bin/bash
# Startup script for GraphRAG API and Frontend
# Starts both services in a tmux session for easy management

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting GraphRAG Services...${NC}\n"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if frontend node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Frontend dependencies not installed. Installing...${NC}"
    cd frontend
    npm install
    cd ..
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found!${NC}"
    echo "Please create .env with your configuration (see README.md)"
fi

# Kill existing tmux session if it exists
tmux kill-session -t graphrag-services 2>/dev/null || true

# Create new tmux session with two panes
tmux new-session -d -s graphrag-services -n services

# Split window horizontally
tmux split-window -h -t graphrag-services:services

# Start API in left pane
tmux send-keys -t graphrag-services:services.0 \
    "cd '$SCRIPT_DIR' && source venv/bin/activate && \
     echo -e '${GREEN}🚀 Starting GraphRAG API...${NC}' && \
     python api.py" C-m

# Start Frontend in right pane
tmux send-keys -t graphrag-services:services.1 \
    "cd '$SCRIPT_DIR/frontend' && \
     echo -e '${GREEN}🌐 Starting Frontend...${NC}' && \
     npm run dev" C-m

# Wait a moment for services to start
sleep 2

# Check if services are running
API_RUNNING=$(ps aux | grep -E "uvicorn api:app|python.*api.py" | grep -v grep | wc -l)
FRONTEND_RUNNING=$(ps aux | grep -E "vite|npm.*dev" | grep -v grep | wc -l)

echo ""
echo -e "${GREEN}✅ Services started in tmux session 'graphrag-services'${NC}\n"
echo -e "📋 Useful Commands:"
echo -e "   ${YELLOW}Attach to session:${NC}    tmux attach -t graphrag-services"
echo -e "   ${YELLOW}Detach from session:${NC}   Press Ctrl+B, then D"
echo -e "   ${YELLOW}Stop all services:${NC}    tmux kill-session -t graphrag-services"
echo -e "   ${YELLOW}View logs:${NC}            tmux attach -t graphrag-services\n"

if [ "$API_RUNNING" -gt 0 ] && [ "$FRONTEND_RUNNING" -gt 0 ]; then
    echo -e "${GREEN}✅ API: Running on http://0.0.0.0:8000${NC}"
    echo -e "${GREEN}✅ Frontend: Running on http://localhost:5173${NC}"
    echo ""
    echo -e "📚 API Documentation: http://localhost:8000/docs"
    echo -e "🌐 Frontend: http://localhost:5173"
    echo ""
    echo -e "${YELLOW}💡 Tip: Access from your local machine:${NC}"
    echo -e "   Frontend: http://\$(hostname -I | awk '{print \$1}'):5173"
    echo -e "   API: http://\$(hostname -I | awk '{print \$1}'):8000"
else
    echo -e "${YELLOW}⚠️  Services may still be starting...${NC}"
    echo -e "   Check status: tmux attach -t graphrag-services"
fi

echo ""
