#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Hệ thống Thẩm định Tài liệu - Setup ===${NC}\n"

# Setup Backend
echo -e "${BLUE}1. Setting up Backend...${NC}"
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing Python packages..."
pip install -r requirements.txt

cd ..

echo -e "${GREEN}✓ Backend setup complete${NC}\n"

# Setup Frontend
echo -e "${BLUE}2. Setting up Frontend...${NC}"
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node packages..."
    npm install
fi

cd ..

echo -e "${GREEN}✓ Frontend setup complete${NC}\n"

echo -e "${BLUE}=== Setup Complete ===${NC}"
echo -e "\n${GREEN}To start the application:${NC}"
echo -e "1. Backend: cd backend && source venv/bin/activate && python run.py"
echo -e "2. Frontend: cd frontend && npm start"
