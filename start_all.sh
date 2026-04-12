#!/bin/bash

# Document Validation System - Start All Services (macOS/Linux)

set -e

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  Document Validation System - Starting All Services    ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check and setup backend
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}[!] Virtual environment not found. Creating...${NC}"
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Check and setup frontend
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}[!] Node modules not found. Installing...${NC}"
    cd frontend
    npm install
    cd ..
fi

echo ""
echo -e "${BLUE}Starting services...${NC}"
echo ""

# Start Backend
echo -e "${GREEN}[1/2] Starting Backend (Flask) on port 5000...${NC}"
cd backend
source venv/bin/activate
python run.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 2

# Start Frontend
echo -e "${GREEN}[2/2] Starting Frontend (React) on port 3000...${NC}"
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  Services Started!                                      ║"
echo "╠════════════════════════════════════════════════════════╣"
echo "║  Backend:  http://localhost:5000                       ║"
echo "║  Frontend: http://localhost:3000                       ║"
echo "║  API Docs: ./API_DOCUMENTATION.md                      ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Process IDs:"
echo "  Backend:  $BACKEND_PID"
echo "  Frontend: $FRONTEND_PID"
echo ""
echo "To stop services:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo "  Or press Ctrl+C"
echo ""

# Wait for both processes
wait
