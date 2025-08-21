# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Discord-based Social Media Post Generator that has migrated from a standalone HTML application to a comprehensive Discord bot + N8N automation workflow. The system creates compelling LinkedIn content (and other social media platforms) in Australian English through Discord modal forms, with approval workflows and automated publishing.

## Architecture

**Discord Bot + N8N Automation**: The system uses Discord as the user interface and N8N as the automation engine for post processing, approval workflows, and social media API integration.

**Core Components**:
- **Discord Bot**: Handles user interactions via slash commands, modal forms, and button interactions
- **N8N Workflows**: Processes posts, manages approval flows, and publishes to social media APIs
- **Database Integration**: Stores posts, tracks approval status, and maintains audit trails
- **Social Media APIs**: Direct integration with Instagram, Twitter/X, Facebook, LinkedIn, and TikTok

**Migration Context**: This project evolved from a single-file HTML application (`linkedin-post-generator.html`) to a scalable Discord-based system supporting multiple platforms and team collaboration.

## Development Commands

### Bot Development
```bash
# Install dependencies
npm install

# Start bot in development mode
npm run dev

# Start bot in production
npm start

# Register slash commands (run once after code changes)
node register-commands.js
```

### Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
# Required: DISCORD_BOT_TOKEN, N8N_WEBHOOK_URL, social media API tokens
```

### Testing
```bash
# Test Discord bot locally
npm run test:bot

# Test N8N webhooks
curl -X POST ${N8N_WEBHOOK_URL}/test -H "Content-Type: application/json" -d '{"test": true}'

# Validate slash commands
npm run validate:commands
```

## Key Architecture Patterns

### Discord Interaction Flow
1. **Slash Commands** (`/createpost`) → Platform Selection
2. **Modal Forms** → Platform-specific field collection
3. **Webhook Submission** → N8N processing pipeline
4. **Approval Interface** → Discord embed with action buttons
5. **Publication** → Automated posting to social media APIs

### Data Flow Architecture
```
Discord User Input → Modal Form → N8N Webhook → Processing → Database Storage → Approval Request → Publication
```

### Platform-Specific Handling
- **Instagram**: Requires media URL, supports alt text
- **Twitter/X**: 280 char limit, thread continuation support
- **LinkedIn**: Professional formatting, article link integration
- **Facebook**: Location check-ins, multiple media support
- **TikTok**: Video requirements, hashtag optimization

## Core Files Structure

### Main Bot Files
- `bot.js` - Main Discord bot application with all interaction handlers
- `package.json` - Dependencies and scripts configuration
- `.env` - Environment variables (Discord tokens, N8N endpoints, API keys)

### N8N Integration
- N8N workflows handle post processing, approval flows, and API publishing
- Webhook endpoints for post creation and approval responses
- Database integration for post tracking and audit trails

### Legacy Files
- `../linkedin-post-generator.html` - Original single-file HTML application (being phased out)
- `../CLAUDE.md` - Original project documentation for HTML version

## Content Generation Rules

The system maintains the original LinkedIn post formatting requirements:
- **Australian English**: Uses Australian spelling and conversational tone
- **Structure**: Hook + rehook (first 3 lines, max 200 characters total)
- **Style**: Conversational mate-to-mate tone with deliberate minor spelling errors
- **Restrictions**: No CTAs, hashtags in post body, or emojis
- **Golden Threads**: Predefined themes that can be woven into content

## Development Guidelines

### Discord Bot Patterns
- Use interaction deferral for long-running operations
- Implement proper error handling with user-friendly messages
- Follow Discord's rate limiting guidelines
- Use ephemeral responses for private interactions

### N8N Integration
- Validate all incoming webhook data
- Implement proper error responses
- Use secure authentication tokens
- Handle timeout scenarios gracefully

### Security Requirements
- Never expose API tokens in code or logs
- Validate all user inputs before processing
- Use environment variables for sensitive configuration
- Implement proper permission checks for approval actions

## Platform-Specific Implementation Notes

### Character Limits
- Twitter: 280 characters per tweet
- Instagram: 2,200 characters
- LinkedIn: 3,000 characters
- Facebook: 63,206 characters
- TikTok: 4,000 characters

### Required Fields by Platform
- **Instagram**: Media URL (images/videos)
- **Twitter**: None (content auto-truncated)
- **LinkedIn**: None (professional formatting applied)
- **Facebook**: None (location optional)
- **TikTok**: Video URL recommended

### API Integration Points
Each platform requires specific API endpoints and authentication:
- Instagram Business API
- Twitter API v2
- LinkedIn API v2
- Facebook Graph API
- TikTok for Business API

## Approval Workflow

### Approval Process
1. Post submitted via Discord modal
2. N8N processes and validates content
3. Approval request sent to designated Discord channel
4. Reviewers use button interactions (Approve/Reject/Edit)
5. Approved posts automatically published
6. Audit trail maintained in database

### Approval Channel Configuration
- Separate channel for approval requests
- Role-based permissions for approvers
- 24-hour approval expiry (configurable)
- Automatic notifications for pending approvals

## Migration Notes

### From HTML to Discord
- **UI Migration**: Modal forms replace HTML form interface
- **Webhook Integration**: N8N replaces direct LLM webhook calls
- **Multi-platform**: Expanded from LinkedIn-only to all major platforms
- **Team Collaboration**: Added approval workflows and user attribution
- **Persistence**: Database storage replaces localStorage

### Legacy Compatibility
- Original prompt structure maintained for LinkedIn posts
- Australian English requirements preserved
- Golden Threads system carried forward
- Content rules and formatting guidelines unchanged

## Common Development Tasks

### Adding New Social Platforms
1. Add platform choice to slash command options
2. Create platform-specific input fields in modal
3. Implement mockup design for post preview
4. Add API integration in N8N workflow
5. Update character limits and validation rules

### Modifying Approval Workflow
1. Update button components in approval embed
2. Modify approval response webhook handler
3. Adjust database schema for new approval states
4. Update audit trail logging

### Debugging Discord Interactions
- Check bot permissions in Discord Developer Portal
- Verify webhook URLs are accessible from Discord
- Use Discord's interaction timeout handling
- Monitor N8N execution logs for processing errors

## Environment Configuration

### Required Environment Variables
```env
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_CHANNEL_ID=main_channel_for_bot
DISCORD_APPROVAL_CHANNEL_ID=approval_requests_channel
N8N_WEBHOOK_URL=n8n_post_creation_endpoint
N8N_APPROVAL_WEBHOOK=n8n_approval_response_endpoint
```

### Social Media API Configuration
Each platform requires specific API credentials and configuration in both the Discord bot environment and N8N workflow settings.

## Prerequisites & Setup

### Required Dependencies
- Node.js 18+
- Discord.js v14+
- Axios for HTTP requests
- N8N instance (self-hosted or cloud)
- Social Media Platform API access

### Discord Bot Setup
1. Create Discord application at [Developer Portal](https://discord.com/developers/applications)
2. Generate bot token and enable required intents (`GUILDS`, `GUILD_MESSAGES`)
3. Set bot permissions: `275414777856` (Send Messages, Slash Commands, Embed Links, etc.)
4. Invite bot to server with application commands scope

### N8N Workflow Configuration
- Import provided N8N workflow JSON
- Configure webhook endpoints for post creation and approval
- Set up database integration (Notion, Airtable, or PostgreSQL)
- Configure social media API credentials

## Implementation Notes

### Main Bot Structure
- `bot.js` - Main application file with Discord.js v14+ implementation
- Slash command registration with platform-specific options
- Modal form builders for different social media platforms
- Interaction handlers for buttons and form submissions
- N8N webhook integration for post processing

### Key Function Structure
- `showPostCreationModal()` - Creates platform-specific modal forms
- `handlePostSubmission()` - Processes form data and sends to N8N
- `createPlatformMockup()` - Generates Discord embed previews
- `handleApprovalAction()` - Manages approval workflow responses

## N8N Workflow Integration

### Core Workflow Nodes
- **Post Webhook** - Receives Discord form submissions
- **Data Processing** - Validates and processes post data
- **Approval Request** - Sends approval embed to Discord channel
- **Approval Response** - Handles approval/rejection actions
- **Publishing** - Publishes approved posts to social media APIs
- **Database Storage** - Tracks posts and audit trail

### Webhook Endpoints
- `/webhook/create-post` - Main post creation endpoint
- `/webhook/approval-response` - Handles approval decisions

## User Workflow

### Basic Usage
1. `/createpost` slash command → Platform selection → Modal form → Submit
2. N8N processes data → Approval request sent to designated channel
3. Approval team reviews → Approve/Reject/Edit buttons
4. Approved posts automatically published to social media APIs

### Platform Features
- **Instagram**: Media URL required, alt text optional
- **Twitter/X**: Thread support with `---` separator, 280 char limit
- **LinkedIn**: Article links, professional formatting, 3000 char limit
- **Facebook**: Location check-ins, 63k char limit
- **TikTok**: Video URLs recommended, 4000 char limit

## Troubleshooting

### Common Issues
- **Bot not responding**: Check token validity, permissions, and intents
- **Webhook errors**: Verify N8N URLs and authentication tokens
- **Form failures**: Validate required fields and character limits
- **Approval issues**: Check channel permissions and webhook configuration

### Debug Configuration
```env
DEBUG=true
LOG_LEVEL=debug
```

## Extension Points

### Adding New Platforms
1. Update slash command choices in `bot.js`
2. Add platform-specific input fields to modal builder
3. Create platform mockup design
4. Configure API integration in N8N workflow
5. Update character limits and validation

### Enhanced Features
- Scheduled recurring posts with cron scheduling
- Post templates for frequently used formats
- Multi-user approval workflows with role permissions
- Analytics dashboard for post performance tracking
- Centralised media library integration