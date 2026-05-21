@echo off
title RetailMind Launcher
echo ===================================================
echo             STARTING RETAILMIND PLATFORM
echo ===================================================
echo.

:: Get the directory of this batch file
set "BASE_DIR=%~dp0"
cd /d "%BASE_DIR%"

:: 1. Start FastAPI Backend in a new window
echo [1/3] Launching FastAPI Backend...
start "RetailMind Backend" cmd /c "cd /d "%BASE_DIR%backend" && if exist .venv (call .venv\Scripts\activate) && pip install -r requirements.txt && uvicorn app.main:app --port 8000 --reload"

:: 2. Start Vite Frontend in a new window
echo [2/3] Launching React Frontend...
start "RetailMind Frontend" cmd /c "cd /d "%BASE_DIR%frontend" && npm install && npm run dev"

:: 3. Open browser
echo [3/3] Opening Web Interface...
timeout /t 5 >nul
start http://localhost:5173

echo.
echo ===================================================
echo RetailMind is starting!
echo  - Backend running at: http://localhost:8000
echo  - Frontend running at: http://localhost:5173
echo.
echo Keep the command windows open while using the app.
echo To stop, simply close the backend and frontend windows.
echo ===================================================
pause
