@echo off
setlocal EnableDelayedExpansion
echo ==============================================
echo MedSight AI - Backend Environment Setup
echo ==============================================

echo Select which Python version you want to use for this project:
echo.
echo [1] Python 3.14
echo [2] Python 3.13
echo [3] Python 3.12
echo [4] Python 3.10 (RECOMMENDED for PyTorch/Machine Learning)
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" set PY_CMD=py -3.14
if "%choice%"=="2" set PY_CMD=py -3.13
if "%choice%"=="3" set PY_CMD=py -3.12
if "%choice%"=="4" set PY_CMD=py -3.10

if not defined PY_CMD (
    echo Invalid choice. Please run the script again and enter a number between 1 and 4.
    pause
    exit /b
)

echo.
echo Checking if the selected Python version is installed...
%PY_CMD% --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ==============================================
    echo [ERROR] The selected Python version is not installed or not recognized!
    echo ==============================================
    pause
    exit /b
)

echo [1/3] Creating Virtual Environment using %PY_CMD%...
%PY_CMD% -m venv venv

echo [2/3] Activating Virtual Environment and Installing Dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
:: Force install older setuptools
python -m pip install setuptools==69.5.1 wheel
:: Bypass Pip's isolated build environment to prevent Whisper from downloading broken setuptools versions
pip install openai-whisper==20231117 --no-build-isolation
pip install -r backend/requirements.txt

echo [3/3] Initializing Database...
python init_db_script.py

echo ==============================================
echo SETUP COMPLETE!
echo ==============================================
echo IMPORTANT NEXT STEPS:
echo 1. Download and install Node.js (Version 20 LTS) from https://nodejs.org 
echo    Note: Do NOT check the box to automatically install Python/Visual Studio tools.
echo.
echo 2. To start the backend: type "call venv\Scripts\activate.bat" and then run "uvicorn backend.main:app --reload --port 8000"
echo.
echo 3. To start the frontend: open a new terminal, cd into the "frontend" folder, run "npm install" and then "npm run dev"
echo ==============================================
pause
exit /b
