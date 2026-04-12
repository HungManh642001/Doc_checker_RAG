@echo off
REM Create sample DOCX files for testing

setlocal

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  Creating Sample DOCX Documents for Testing             ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to PATH
    pause
    exit /b 1
)

REM Check if python-docx is installed
python -c "import docx" >nul 2>&1
if errorlevel 1 (
    echo [!] python-docx not found. Installing...
    pip install python-docx
)

echo Running sample creation script...
python create_samples.py

if errorlevel 0 (
    echo.
    echo ╔════════════════════════════════════════════════════════╗
    echo ║  ✓ Sample documents created successfully!              ║
    echo ╚════════════════════════════════════════════════════════╝
    echo.
    echo Location: samples/
    echo Files:
    echo   - sample_main.docx (Document to analyze)
    echo   - sample_regulation.docx (Regulation)
    echo   - sample_reference.docx (Reference document)
    echo.
    echo You can now upload these files to test the application.
    echo.
) else (
    echo [ERROR] Failed to create sample documents
)

pause
