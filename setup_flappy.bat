@echo off
echo ==========================================
echo   Flappy Bird - Environment Setup Script
echo ==========================================
echo.

REM Step 1: Ensure Python is available
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Python not found. Please install Python 3.9+ first.
    pause
    exit /b 1
)

REM Step 2: Create a virtual environment
echo Creating virtual environment...
python -m venv venv
IF ERRORLEVEL 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

REM Step 3: Activate it
call venv\Scripts\activate

REM Step 4: Upgrade pip
python -m pip install --upgrade pip

REM Step 5: Install required packages
echo Installing dependencies...
pip install pygame neat-python mysql-connector-python python-dotenv

REM Step 6: Verify installation
echo.
echo Checking installed packages...
pip list

REM Step 7: Start the game
echo.
echo Launching Flappy Bird game...
python game.py

echo.
echo Done! Press any key to exit.
pause
