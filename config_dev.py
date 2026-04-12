"""
Configuration for debugging the Document Validation System
"""

import sys
import os

# Add backend to path for debugging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Development configuration
DEBUG = True
TESTING = False

# Server Configuration
FLASK_ENV = 'development'
DEBUG_TOOLBAR_ENABLED = True

# Upload Configuration
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
UPLOAD_FOLDER = 'backend/uploads'

# CORS Configuration (for development)
CORS_ORIGINS = ['http://localhost:3000']

# AI Configuration
AI_MODE = 'simulate'  # Options: 'simulate', 'openai', 'mock'

# Logging
LOG_LEVEL = 'DEBUG'

print("""
╔════════════════════════════════════════════════════════╗
║  Document Validation System - Development Config       ║
╚════════════════════════════════════════════════════════╝

Configuration Summary:
- Environment: development
- Debug Mode: ON
- Max Upload: 100MB
- AI Mode: simulation

Directories:
- Backend: ./backend
- Frontend: ./frontend
- Uploads: ./backend/uploads

To start development:
1. Backend:  cd backend && python run.py
2. Frontend: cd frontend && npm start

Quick Links:
- Frontend: http://localhost:3000
- Backend:  http://localhost:5000
- API Docs: ./API_DOCUMENTATION.md
- Quickstart: ./QUICKSTART.md
""")
