@echo off
cd /d "%~dp0"

set PYTHON_BIN=python
if exist "reddit-env\Scripts\python.exe" set PYTHON_BIN=reddit-env\Scripts\python.exe

set SUBREDDIT=%1
if "%SUBREDDIT%"=="" set SUBREDDIT=horrorstories

echo ========================================================
echo   Generando video para r/%SUBREDDIT%...
echo ========================================================

%PYTHON_BIN% scripts\main.py --subreddit "%SUBREDDIT%" --limit 1 --duration 1 --order hot --scenes --subs --words-per-card 3 --dark-mode --yes %*
