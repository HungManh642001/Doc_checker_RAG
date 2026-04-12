@echo off
REM Colors and setup for Windows

echo.
echo ===============================================
echo.  Hệ thống Thẩm định Tài liệu - Setup
echo ===============================================
echo.

REM Setup Backend
echo [1/2] Setting up Backend...
cd backend

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo Installing Python packages...
pip install -r requirements.txt

cd ..

echo [2/2] Setting up Frontend...
cd frontend

if not exist "node_modules" (
    echo Installing Node packages...
    call npm install
)

cd ..

echo.
echo ===============================================
echo.  Setup Complete!
echo ===============================================
echo.
echo To start the application:
echo.
echo Terminal 1 - Backend:
echo   cd backend
echo   .\venv\Scripts\activate.bat
echo   python run.py
echo.
echo Terminal 2 - Frontend:
echo   cd frontend
echo   npm start
echo.
pause
