@echo off
title CodeFlamingo AI Blog Agent
color 0B

echo ==========================================
echo    Waking up the CodeFlamingo AI Agent...
echo ==========================================
echo.

:: 1. Navigate to the folder where this .bat file lives
set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

:: 2. Activate the Python virtual environment
call ai-worker-blog\Scripts\activate.bat

:: 3. Go to the scripts folder and run the agent
cd automation
python blog_agent.py

:: 4. Keep the window open when finished
echo.
pause