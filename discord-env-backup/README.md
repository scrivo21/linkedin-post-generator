# LinkedIn Discord Bot

A Discord bot for creating professional LinkedIn posts with Australian English formatting, Golden Threads integration, and approval workflows.

## Features

- 🇦🇺 **Australian English Focus**: Proper spelling and conversational tone
- 💼 **LinkedIn-Optimized**: 3,000 character limit with hook+rehook structure
- 🧵 **Golden Threads**: Data analysis value & community asset management themes
- ✅ **Approval Workflow**: Team-based post approval system
- 🖼️ **Image Prompts**: Automatic visual content suggestions
- 📊 **Professional Formatting**: No CTAs, hashtags in body, or emojis

## Setup

### 1. Install Dependencies
```bash
npm install
```

### 2. Environment Configuration
Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

Required environment variables:
- `DISCORD_BOT_TOKEN`: Your Discord bot token
- `DISCORD_CHANNEL_ID`: Main channel for bot interactions
- `DISCORD_APPROVAL_CHANNEL_ID`: Channel for post approvals
- `N8N_WEBHOOK_URL`: Webhook for content generation
- `LLM_WEBHOOK_URL`: Alternative LLM webhook endpoint

### 3. Discord Bot Setup
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create new application and bot
3. Copy bot token to `.env`
4. Enable required intents: `GUILDS`, `GUILD_MESSAGES`
5. Set bot permissions: `275414777856`
6. Invite bot to your server

### 4. Register Commands
```bash
npm run register-commands
```

### 5. Start Bot
```bash
# Development mode with auto-restart
npm run dev

# Production mode
npm start
```

## Usage

### Creating LinkedIn Posts
1. Use `/linkedin` slash command or click the "Create LinkedIn Post" button
2. Fill out the comprehensive form with:
   - **Topic/Industry**: Your professional focus area
   - **Target Audience**: Who you're writing for
   - **Situation/Challenge**: Specific scenario to address
   - **Key Insight**: Main point or lesson
   - **Experience**: Your relevant background
   - **Credibility Signpost**: How you'll reference expertise
   - **Personal Anecdote**: Story that illustrates your point
   - **Timeframe**: When this happened
   - **Contextual Info**: Supporting details (optional)
   - **Options**: Golden threads selection and spelling preferences

### Approval Process
1. Submitted posts appear in approval channel
2. Approval team reviews content and formatting
3. Click ✅ Approve, ❌ Reject, or ✏️ Edit buttons
4. Approved posts are automatically published to LinkedIn

### Golden Threads
Choose from predefined themes to weave into content:
- **Data Analysis Value**: "Data needs analysis to become an asset"
- **Community Asset Management**: "Community is critical to asset management"

## Content Rules

Generated LinkedIn posts follow strict formatting:
- **Hook + Rehook**: First 3 lines form one paragraph (max 200 characters)
- **Australian English**: Proper spelling (realise, colour, organisation)
- **Conversational Tone**: Professional but approachable mate-to-mate style
- **Minor Error**: One deliberate spelling mistake for authenticity
- **No Marketing**: No CTAs, hashtags in post body, or emojis
- **Professional Credibility**: Through storytelling, not explicit claims

## Project Structure

```
discord-env/
├── bot.js                    # Main Discord bot application
├── package.json             # Dependencies and scripts
├── .env.example             # Environment variable template
├── claude.md                # Claude Code documentation
├── scripts/
│   ├── register-commands.js # Slash command registration
│   └── quickstart.sh        # One-command setup script
├── test/
│   └── bot-test.js          # Test suite for bot functionality
└── docs/
    ├── DEPLOYMENT.md        # Complete deployment guide
    └── FIELD_MAPPING.md     # HTML to Discord field mapping
```

## Development Scripts

- `npm start`: Start bot in production mode
- `npm run dev`: Start bot with nodemon for development
- `npm run register-commands`: Register Discord slash commands
- `npm run quickstart`: Complete setup and start (recommended for first time)
- `npm test`: Run bot tests and webhook connectivity

## N8N Integration

The bot integrates with N8N workflows for:
- Content generation via LLM webhooks
- Post processing and validation
- LinkedIn API publishing
- Analytics and tracking

See `claude.md` for detailed N8N workflow configuration.

## Troubleshooting

### Bot Not Responding
- Check `DISCORD_BOT_TOKEN` is valid
- Verify bot has required permissions in server
- Ensure bot is online and connected

### Webhook Errors
- Verify `N8N_WEBHOOK_URL` is accessible
- Check authentication tokens if required
- Validate JSON payload format

### Command Registration Issues
- Run `npm run register-commands` after code changes
- Check `DISCORD_GUILD_ID` for guild-specific commands
- Wait up to 1 hour for global command updates

## Migration from HTML Version

This Discord bot preserves all functionality from the original HTML LinkedIn post generator:
- Same comprehensive form fields
- Identical Australian English formatting rules
- Golden Threads system maintained
- Professional content structure preserved
- Image prompt generation included