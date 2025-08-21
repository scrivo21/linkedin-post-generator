@echo off
REM LinkedIn Post Generator - Virtual Environment Activation Script (Windows)

echo 🚀 LinkedIn Post Generator - Environment Setup
echo ===============================================

REM Check if virtual environment exists
if not exist "venv" (
    echo ⚠️  Virtual environment not found. Creating it now...
    python -m venv venv
    echo ✅ Virtual environment created successfully!
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if requirements are installed
if not exist "venv\Lib\site-packages\discord" (
    echo 📦 Installing dependencies...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    echo ✅ Dependencies installed successfully!
) else (
    echo ✅ Dependencies already installed!
)

REM Check if .env file exists
if not exist ".env" (
    echo ⚙️  Environment file not found. Creating from template...
    copy .env.example .env
    echo 📝 Please edit .env file with your configuration before running the bot
) else (
    echo ✅ Environment file found!
)

echo ===============================================
echo 🎉 Setup complete! Virtual environment is now active.
echo 📋 Available commands:
echo    python discord_linkedin_bot.py - Start the Discord bot
echo    psql linkedin_posts ^< schema.sql - Setup database schema
echo    deactivate - Exit virtual environment
echo ===============================================

REM Set environment indicator
set LINKEDIN_BOT_ENV=active