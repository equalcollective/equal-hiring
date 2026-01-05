@echo off
REM X-Ray Backend Startup Script for Windows
REM This script activates the virtual environment and starts the FastAPI server

echo ========================================
echo X-Ray Backend Startup Script
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo.
    echo Please create it first by running:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if uvicorn is installed
python -c "import uvicorn" 2>nul
if errorlevel 1 (
    echo ERROR: uvicorn is not installed!
    echo.
    echo Please install dependencies by running:
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo.
echo Starting X-Ray Backend API server...
echo Server will be available at: http://localhost:8000
echo API Docs will be available at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
