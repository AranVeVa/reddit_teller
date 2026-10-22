@echo off
cd /d "%~dp0"
echo ========================================================
echo   Iniciando reddit_teller en Windows (Backend + Frontend)
echo ========================================================

set PYTHON_BIN=python
if exist "reddit-env\Scripts\python.exe" set PYTHON_BIN=reddit-env\Scripts\python.exe

start "reddit_teller - Backend API" cmd /k "%PYTHON_BIN% -m uvicorn server.app:app --host 127.0.0.1 --port 8000 --reload"
start "reddit_teller - Frontend Vite" cmd /k "cd frontend && npm run dev"

echo.
echo Servidores iniciados en ventanas separadas:
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://localhost:5173
echo.
