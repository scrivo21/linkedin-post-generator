#!/bin/bash
# LinkedIn Post Generator - Virtual Environment Activation Script

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 LinkedIn Post Generator - Environment Setup${NC}"
echo -e "${BLUE}===============================================${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating it now...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created successfully!${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}🔄 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if requirements are installed
if [ ! -f "venv/lib/python*/site-packages/discord/__init__.py" ]; then
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed successfully!${NC}"
else
    echo -e "${GREEN}✅ Dependencies already installed!${NC}"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚙️  Environment file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}📝 Please edit .env file with your configuration before running the bot${NC}"
else
    echo -e "${GREEN}✅ Environment file found!${NC}"
fi

echo -e "${BLUE}===============================================${NC}"
echo -e "${GREEN}🎉 Setup complete! Virtual environment is now active.${NC}"
echo -e "${BLUE}📋 Available commands:${NC}"
echo -e "   ${YELLOW}python discord_linkedin_bot.py${NC} - Start the Discord bot"
echo -e "   ${YELLOW}psql linkedin_posts < schema.sql${NC} - Setup database schema"
echo -e "   ${YELLOW}deactivate${NC} - Exit virtual environment"
echo -e "${BLUE}===============================================${NC}"

# Export virtual environment indicator
export LINKEDIN_BOT_ENV="active"