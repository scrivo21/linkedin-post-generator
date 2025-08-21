#!/bin/bash

# LinkedIn Discord Bot Quick Start Script
echo "🚀 LinkedIn Discord Bot Quick Start"
echo "================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

echo "✅ Node.js version: $(node --version)"

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

echo "✅ Dependencies installed"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your Discord bot token and webhook URLs"
    echo ""
    echo "Required environment variables:"
    echo "- DISCORD_BOT_TOKEN=your_discord_bot_token"
    echo "- DISCORD_CHANNEL_ID=your_main_channel_id"
    echo "- DISCORD_APPROVAL_CHANNEL_ID=your_approval_channel_id"
    echo "- LLM_WEBHOOK_URL=your_llm_webhook_url"
    echo ""
    echo "Run this script again after configuring .env"
    exit 0
fi

# Source environment variables
source .env

# Check if required environment variables are set
if [ -z "$DISCORD_BOT_TOKEN" ] || [ "$DISCORD_BOT_TOKEN" = "your_discord_bot_token_here" ]; then
    echo "❌ DISCORD_BOT_TOKEN not configured in .env file"
    echo "Please edit .env and set your Discord bot token"
    exit 1
fi

if [ -z "$LLM_WEBHOOK_URL" ] || [ "$LLM_WEBHOOK_URL" = "http://localhost:5678/webhook-test/d5e5b3c7-89c0-4397-ab90-f609a99bd430" ]; then
    echo "⚠️  LLM_WEBHOOK_URL not configured - content generation will fail"
    echo "Please set your LLM webhook URL in .env file"
fi

echo "✅ Environment variables configured"

# Run tests
echo "🧪 Running tests..."
npm test
if [ $? -ne 0 ]; then
    echo "❌ Tests failed"
    exit 1
fi

echo "✅ Tests passed"

# Register commands
echo "📝 Registering Discord slash commands..."
npm run register-commands
if [ $? -ne 0 ]; then
    echo "❌ Failed to register commands"
    echo "Check your DISCORD_BOT_TOKEN and bot permissions"
    exit 1
fi

echo "✅ Commands registered"

# Start bot
echo ""
echo "🎉 Setup complete! Starting LinkedIn Discord Bot..."
echo ""
echo "Bot features:"
echo "- /linkedin command for post creation"
echo "- Two-page modal form with all LinkedIn fields"
echo "- Australian English content generation"
echo "- Golden Threads integration"
echo "- Approval workflow system"
echo ""
echo "Press Ctrl+C to stop the bot"
echo ""

npm run dev