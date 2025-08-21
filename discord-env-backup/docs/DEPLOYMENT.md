# LinkedIn Discord Bot Deployment Guide

## Quick Setup

### 1. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your actual credentials
```

Required environment variables:
```env
# Discord Bot (Required)
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_server_id_for_fast_commands
DISCORD_CHANNEL_ID=main_channel_id
DISCORD_APPROVAL_CHANNEL_ID=approval_channel_id

# LLM Webhook (Required for content generation)
LLM_WEBHOOK_URL=http://localhost:5678/webhook-test/d5e5b3c7-89c0-4397-ab90-f609a99bd430
LLM_WEBHOOK_METHOD=POST

# Optional
N8N_WEBHOOK_TOKEN=optional_security_token
```

### 2. Discord Bot Setup

#### Create Discord Application
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" → Name: "LinkedIn Post Generator"
3. Go to "Bot" section → Click "Add Bot"
4. Copy the bot token to your `.env` file
5. Under "Privileged Gateway Intents", enable:
   - ✅ MESSAGE CONTENT INTENT
   - ✅ SERVER MEMBERS INTENT

#### Get Discord IDs
```bash
# Enable Developer Mode in Discord:
# Settings → Advanced → Developer Mode

# Right-click and copy IDs:
DISCORD_GUILD_ID=your_server_id
DISCORD_CHANNEL_ID=main_channel_id
DISCORD_APPROVAL_CHANNEL_ID=approval_channel_id
```

#### Bot Permissions
Required permissions: `275414777856`
- Send Messages
- Use Slash Commands  
- Embed Links
- Attach Files
- Read Message History

#### Invite Bot to Server
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=275414777856&scope=bot%20applications.commands
```

### 3. Installation & Testing
```bash
# Install dependencies
npm install

# Test prompt generation and webhook connectivity
npm test

# Register Discord slash commands
npm run register-commands

# Start bot in development mode
npm run dev
```

### 4. Verify Setup

#### Test LinkedIn Command
1. In Discord, type `/linkedin`
2. Fill out the comprehensive form (2 pages)
3. Check that content is generated and sent for approval
4. Verify approval message appears in approval channel

#### Test Approval Workflow
1. Click ✅ Approve, ❌ Reject, or ✏️ Edit buttons
2. Verify status updates correctly
3. Check console logs for webhook calls

## LLM Webhook Integration

### Supported Webhook Formats

#### Option 1: Direct LLM Webhook
```bash
LLM_WEBHOOK_URL=http://localhost:5678/webhook-test/your-webhook-id
LLM_WEBHOOK_METHOD=POST
```

Expected payload:
```json
{
  "prompt": "# LinkedIn Post Prompt...",
  "temperature": 0.7,
  "max_tokens": 1500,
  "timestamp": "2024-08-19T...",
  "source": "linkedin-discord-bot",
  "platform": "linkedin",
  "formData": { ... }
}
```

#### Option 2: N8N Workflow
```bash
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/linkedin-post
N8N_APPROVAL_WEBHOOK=https://your-n8n-instance.com/webhook/linkedin-approval
N8N_WEBHOOK_TOKEN=optional_bearer_token
```

## Content Generation Features

### LinkedIn-Specific Requirements
- ✅ Australian English spelling and grammar
- ✅ Hook + rehook structure (200 char limit for first 3 lines)
- ✅ Conversational mate-to-mate tone
- ✅ One deliberate minor spelling error
- ✅ No CTAs, hashtags in body, or emojis
- ✅ Professional credibility through storytelling

### Golden Threads Integration
- **Data Analysis Value**: "Data needs analysis to become an asset"
- **Community Asset Management**: "Community is critical to asset management"

### Form Fields (Preserves HTML Version)
**Page 1:**
- Topic/Industry
- Target Audience
- Specific Situation/Challenge
- Key Insight/Lesson
- Your Experience/Background (first 200 chars)

**Page 2:**
- Credibility Signpost
- Personal Anecdote
- Timeframe/Context
- Contextual Information (optional)
- Golden Threads & Spelling Error options

## Production Deployment

### Environment Setup
```bash
NODE_ENV=production
LOG_LEVEL=info
DEBUG=false
```

### Process Management
```bash
# Using PM2
npm install -g pm2
pm2 start bot.js --name linkedin-bot

# Or using systemd
sudo cp linkedin-bot.service /etc/systemd/system/
sudo systemctl enable linkedin-bot
sudo systemctl start linkedin-bot
```

### Monitoring
```bash
# Check bot status
pm2 status linkedin-bot

# View logs
pm2 logs linkedin-bot

# Monitor performance
pm2 monit
```

## Troubleshooting

### Common Issues

#### Bot Not Responding
```bash
# Check token validity
echo $DISCORD_BOT_TOKEN | wc -c  # Should be ~60 characters

# Verify bot permissions
# Bot needs "Use Slash Commands" permission in Discord server

# Check bot is online
npm run dev  # Should show "✅ LinkedIn Discord Bot logged in"
```

#### Webhook Errors
```bash
# Test webhook connectivity
npm test

# Check webhook URL accessibility
curl -X POST $LLM_WEBHOOK_URL -H "Content-Type: application/json" -d '{"test": true}'

# Verify network connectivity (Tailscale, etc.)
ping your-webhook-host
```

#### Command Registration Issues
```bash
# Re-register commands
npm run register-commands

# For guild-specific commands (faster updates)
DISCORD_GUILD_ID=your_server_id npm run register-commands

# Global commands take up to 1 hour to update
```

#### Modal Form Issues
```bash
# Check character limits
# Discord modals have max 5 components per modal
# Text inputs have max length limits (see code)

# Verify form data storage
# Check global.linkedinFormData in bot console
```

### Debug Mode
```bash
DEBUG=true npm run dev
```

### Error Codes
- **50013**: Missing permissions (check bot permissions)
- **10062**: Unknown interaction (command registration issue)  
- **40060**: Interaction has already been acknowledged (timing issue)

## Development

### File Structure
```
discord-env/
├── bot.js              # Main Discord bot application
├── register-commands.js # Slash command registration
├── test/bot-test.js     # Test suite for prompt generation
├── package.json        # Dependencies and scripts
├── .env.example        # Environment variable template
└── README.md          # Basic usage documentation
```

### Adding Features
1. **New Platform Support**: Extend modal forms and content generation
2. **Enhanced Approval**: Add role-based permissions
3. **Analytics**: Track post performance and engagement
4. **Templates**: Save frequently used post formats

### Code Quality
```bash
# Run tests before deployment
npm test

# Check for syntax errors
node -c bot.js

# Monitor memory usage
process.memoryUsage()
```

## Security Considerations

### Token Management
- ✅ Never commit `.env` files to git
- ✅ Use environment variables for all secrets
- ✅ Rotate Discord bot token regularly
- ✅ Secure webhook endpoints with authentication

### Input Validation
- ✅ Character limits enforced on all inputs
- ✅ Required field validation
- ✅ Sanitization of user content before webhook submission

### Access Control
- ✅ Ephemeral responses for private information
- ✅ Role-based approval permissions (future enhancement)
- ✅ Channel-specific bot access

## Maintenance

### Regular Tasks
- Monitor bot uptime and response times
- Review error logs for patterns
- Update dependencies monthly
- Test approval workflow functionality
- Backup configuration and data

### Updates
```bash
# Update dependencies
npm update

# Re-register commands after Discord.js updates
npm run register-commands

# Test after updates
npm test
```