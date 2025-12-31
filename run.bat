@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   PERSON DETECTION GATE SYSTEM
echo ========================================
echo.

:: 1. Check if .venv exists and activate
if exist .venv\Scripts\activate.bat (
    echo [1/4] Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [1/4] No virtual environment found, using system Python...
)

:: 2. Check Python
echo [2/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

:: 3. Install dependencies if needed
echo [3/4] Checking dependencies...
pip show ultralytics >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

:: 4. Start the detection system
echo [4/4] Starting Person Detection System...
echo.
echo ========================================
echo   SYSTEM STARTING...
echo ========================================
echo.
echo   Python Detection: http://localhost:8000
echo   Node.js Dashboard: http://localhost:3000
echo.
echo   Press Ctrl+C to stop the system
echo ========================================
echo.

:: Start Node.js server in background (if node is available)
where node >nul 2>&1
if not errorlevel 1 (
    start "SMAC Backend" /min cmd /c "cd backend && node server.js"
    echo [OK] Node.js backend started (port 3000)
    timeout /t 2 /nobreak >nul
) else (
    echo [WARN] Node.js not found - dashboard will not start
)

:: Start Python detection system (foreground)
echo [OK] Starting Python detection system...
cd src
python detection_system.py

:: Cleanup when Python stops
cd ..
echo.
echo Stopping system...
taskkill /FI "WINDOWTITLE eq SMAC Backend" >nul 2>&1

echo.
echo System stopped.
pause
