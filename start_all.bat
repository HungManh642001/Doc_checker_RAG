@echo off
REM Document Validation System - Start All Services (Windows)

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  Document Validation System - Starting All Services     ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Check if node_modules exists in frontend
if not exist "frontend\node_modules" (
    echo [!] Node modules not found. Installing...
    cd frontend
    call npm install
    cd ..
)

REM Check if venv exists
if not exist "backend\venv" (
    echo [!] Virtual environment not found. Creating...
    cd backend
    python -m venv venv
    call .\venv\Scripts\activate.bat
    pip install -r requirements.txt
    cd ..
)

echo.
echo Starting services...
echo.

REM Start Backend in a new window
echo [1/2] Starting Backend (Flask) on port 5000...
start "Docker Validation System - Backend" cmd /k "cd backend && .\venv\Scripts\activate.bat && python run.py"

REM Wait a bit for backend to start
timeout /t 2 /nobreak

REM Start Frontend in a new window
echo [2/2] Starting Frontend (React) on port 3000...
start "Document Validation System - Frontend" cmd /k "cd frontend && npm start"

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  Services Started!                                      ║
echo ╠════════════════════════════════════════════════════════╣
echo ║  Backend:  http://localhost:5000                       ║
echo ║  Frontend: http://localhost:3000                       ║
echo ║  API Docs: http://localhost:5000/api                   ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo Click on the frontend window to interact with the app.
echo.
echo To stop services:
echo   - Close the backend window
echo   - Close the frontend window
echo.
pause
