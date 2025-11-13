@echo off
REM ===========================================================
REM Flappy Bird AI - Windows Environment Setup Script
REM Author: Shivanshu Shukla
REM ===========================================================

echo Setting up Flappy Bird environment...
echo.

REM --- Check for Python installation ---
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not added to PATH.
    echo Please install Python 3.10+ and rerun this script.
    pause
    exit /b
)

REM --- Create virtual environment ---
echo Creating virtual environment...
python -m venv venv

REM --- Activate environment ---
echo Activating virtual environment...
call venv\Scripts\activate

REM --- Upgrade pip ---
echo Upgrading pip...
python -m pip install --upgrade pip

REM --- Install required packages ---
echo Installing required dependencies...
pip install mysql-connector-python==9.5.0
pip install neat-python==0.92
pip install pygame==2.6.1
pip install python-dotenv==1.2.1

REM --- Done ---
echo.
echo ===========================================================
echo ✅ Setup complete!
echo To start the game, run:
echo.
echo     venv\Scripts\activate
echo     python game.py
echo.
echo ===========================================================
pause
