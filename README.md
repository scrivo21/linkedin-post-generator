# LinkedIn Post Generator & Approval System

```ascii
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    ██╗     ██╗███╗   ██╗██╗  ██╗███████╗██████╗ ██╗███╗   ██╗               ║
║    ██║     ██║████╗  ██║██║ ██╔╝██╔════╝██╔══██╗██║████╗  ██║               ║
║    ██║     ██║██╔██╗ ██║█████╔╝ █████╗  ██║  ██║██║██╔██╗ ██║               ║
║    ██║     ██║██║╚██╗██║██╔═██╗ ██╔══╝  ██║  ██║██║██║╚██╗██║               ║
║    ███████╗██║██║ ╚████║██║  ██╗███████╗██████╔╝██║██║ ╚████║               ║
║    ╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═══╝               ║
║                                                                              ║
║    ██████╗  ██████╗ ███████╗████████╗     ███╗   ███╗ ██████╗ ██████╗        ║
║    ██╔══██╗██╔═══██╗██╔════╝╚══██╔══╝     ████╗ ████║██╔════╝ ██╔══██╗       ║
║    ██████╔╝██║   ██║███████╗   ██║        ██╔████╔██║██║  ███╗██████╔╝       ║
║    ██╔═══╝ ██║   ██║╚════██║   ██║        ██║╚██╔╝██║██║   ██║██╔══██╗       ║
║    ██║     ╚██████╔╝███████║   ██║        ██║ ╚═╝ ██║╚██████╔╝██║  ██║       ║
║    ╚═╝      ╚═════╝ ╚══════╝   ╚═╝        ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝       ║
║                                                                              ║
║                    🤖 Automated LinkedIn Content Management 📱               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Discord.py-2.3.2-blue.svg" alt="Discord.py">
  <img src="https://img.shields.io/badge/PostgreSQL-14+-blue.svg" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Status-Production-brightgreen.svg" alt="Status">
</p>

---

## 🌟 Overview

The **LinkedIn Post Generator & Approval System** is a comprehensive solution for creating, managing, and publishing professional LinkedIn content through an automated workflow. The system combines a web-based post generator with a Discord bot approval system and seamless LinkedIn API integration.

## 🚀 Quick Start

### For macOS/Linux:
```bash
# Clone or navigate to project directory
cd LinkedIn-Post-Generator

# Run the setup script (creates venv, installs dependencies)
source activate.sh

# Setup database (requires PostgreSQL)
createdb linkedin_posts
psql linkedin_posts < schema.sql

# Configure environment variables
cp .env.example .env
# Edit .env with your Discord, LinkedIn, and database credentials

# Start the Discord bot
python discord_linkedin_bot.py
```

### For Windows:
```cmd
# Navigate to project directory
cd LinkedIn-Post-Generator

# Run the setup script
activate.bat

# Setup database (requires PostgreSQL)
createdb linkedin_posts
psql linkedin_posts < schema.sql

# Configure environment variables
copy .env.example .env
# Edit .env with your credentials

# Start the Discord bot
python discord_linkedin_bot.py
```

## 📋 System Requirements

- Python 3.10+
- PostgreSQL 12+
- Discord Bot Token
- LinkedIn API Access (optional, for publishing)

## 🏗️ Architecture

This system consists of three main components:

1. **HTML Application** (`linkedin-post-generator.html`) - Content creation interface
2. **Discord Bot** (`discord_linkedin_bot.py`) - Approval workflow management
3. **PostgreSQL Database** - Content storage and status tracking

## 🔧 Configuration

### Required Environment Variables (.env):

```env
# Discord Configuration
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_APPROVAL_CHANNEL_ID=your_approval_channel_id

# Database Configuration  
DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# LinkedIn API (optional)
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token
LINKEDIN_PERSON_ID=your_linkedin_person_id

# Optional: n8n Webhook Integration
N8N_WEBHOOK_URL=your_n8n_webhook_url
```

## 📈 Workflow

1. **Content Creation**: Posts created via HTML app or direct database insert
2. **Auto-Detection**: Bot monitors database for new pending posts
3. **Discord Approval**: Team approves/rejects via Discord reactions (✅/❌)
4. **Auto-Publishing**: Approved posts published to LinkedIn automatically
5. **Audit Trail**: Complete tracking of all status changes

## 🤖 Bot Commands

- `!status` - Check system status and statistics
- `!test_post [content]` - Create test post for approval (admin only)

## 📁 Project Structure

```
├── linkedin-post-generator.html    # Web application for content creation
├── discord_linkedin_bot.py         # Main Discord bot
├── db_monitor.py                   # Database monitoring service
├── linkedin_publisher.py           # LinkedIn API integration
├── models.py                       # Database models
├── config.py                       # Configuration management
├── schema.sql                      # Database schema
├── requirements.txt                # Python dependencies
├── activate.sh                     # Setup script (macOS/Linux)
├── activate.bat                    # Setup script (Windows)
├── .env.example                    # Environment template
└── CLAUDE.md                       # Detailed technical documentation
```

## 🎯 Features

### Discord Bot Features
- LinkedIn-style post previews in Discord
- Reaction-based approval workflow
- Automatic post publishing
- Rich embed notifications
- Error handling and retry logic
- Admin commands and status monitoring

### HTML Application Features
- Australian English content generation
- Form validation and progress tracking
- Auto-save functionality
- Data export/import capabilities
- Mobile-responsive design
- Golden Threads content consistency system

### Database Features
- PostgreSQL with full audit trail
- Status workflow management
- Performance optimized queries
- Data integrity constraints
- Backup and cleanup functions

## 🔗 Integration Options

- **n8n Webhooks**: Optional workflow automation
- **LinkedIn API**: Direct publishing integration
- **Custom Webhooks**: Extensible notification system

## 📖 Documentation

See `CLAUDE.md` for comprehensive technical documentation including:
- Detailed architecture overview
- API configurations
- Database schema details
- Setup instructions
- Integration guides

## 🛠️ Development

The project uses a virtual environment for dependency management. Use the provided activation scripts for easy setup:

```bash
# Activate environment
source activate.sh

# Deactivate when done
deactivate
```

## 📝 License

This project is configured for internal use. Modify as needed for your organization's requirements.