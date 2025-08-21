# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive LinkedIn Post Generator system consisting of:

1. **HTML Application**: A standalone web application (`linkedin-post-generator.html`) that creates compelling LinkedIn content in Australian English
2. **Discord Approval Bot**: A Python-based Discord bot system that monitors a PostgreSQL database for pending posts, sends them for team approval, and automatically publishes approved content to LinkedIn
3. **Database Integration**: PostgreSQL database that stores posts, tracks approval status, and manages the complete workflow from creation to publication

## Architecture

### HTML Application Architecture

**Single-File Application**: The entire web application is contained within `linkedin-post-generator.html` - a self-contained web application with embedded CSS and JavaScript.

**Core Components**:
- **Form Interface**: Collects user inputs for post generation (industry, audience, personal anecdotes, etc.)
- **LLM Webhook Integration**: Configurable endpoint that sends structured prompts to external LLM services
- **Golden Threads System**: Predefined themes that can be woven into content:
  - Data Analysis Value: "Data needs analysis to become an asset"
  - Community Asset Management: "Community is critical to asset management"
- **Local Storage**: Automatically saves form data and webhook configuration for user convenience

### Discord Bot System Architecture

**Core Python Modules**:
- **`discord_linkedin_bot.py`**: Main Discord bot with approval workflow and LinkedIn mockup generation
- **`db_monitor.py`**: Database monitoring service that polls for new pending posts
- **`linkedin_publisher.py`**: LinkedIn API integration for publishing approved posts
- **`models.py`**: SQLAlchemy database models and data access layer
- **`config.py`**: Environment variable management and configuration validation

**Database Schema** (`schema.sql`):
- **`linkedin_posts` table**: Stores post content, status, approval tracking, and LinkedIn metadata
- **Status tracking**: pending → approved/rejected → published/failed
- **Discord integration**: Message IDs for approval workflow
- **Audit trail**: Timestamps and approval history

### Complete Workflow

1. **Content Creation**: User creates post via HTML application OR posts inserted directly into database
2. **Database Monitoring**: Python service detects new pending posts
3. **Discord Notification**: Bot sends LinkedIn-styled preview to approval channel with reaction buttons
4. **Team Approval**: Team members react with ✅ (approve) or ❌ (reject)
5. **Automatic Publishing**: Approved posts are automatically published to LinkedIn via API
6. **Webhook Integration**: Optional n8n webhook notifications for external integrations
7. **Status Tracking**: Complete audit trail maintained in database

## Key Features

### HTML Application Features
- **Australian English Focus**: Uses Australian spelling and conversational tone
- **Professional Web App**: Mobile-responsive design optimized for iPhone/Safari
- **Webhook Architecture**: Designed to work with Tailscale network LLM services
- **Auto-save**: Form data persists in browser localStorage
- **Structured Content**: Enforces specific LinkedIn post structure (hook + rehook under 200 characters, no CTAs, no hashtags/emojis)
- **Image Prompt Generation**: Creates accompanying visual prompts for generated posts
- **Progress Tracking**: Real-time form completion indicator (0-100%)
- **Field Validation**: Real-time validation with error messages and visual feedback
- **Character Counting**: Live character counters with warning/danger indicators
- **Data Export/Import**: JSON-based form data backup and restore

### Discord Bot System Features
- **Database Monitoring**: Automatic polling for new pending posts every 30 seconds
- **LinkedIn Mockups**: Generates visual previews of how posts will appear on LinkedIn
- **Reaction-Based Approval**: Simple ✅/❌ reactions for post approval/rejection
- **Rich Discord Embeds**: Professional post previews with metadata and analytics
- **Automatic Publishing**: Seamless LinkedIn API integration for approved posts
- **Status Tracking**: Complete audit trail from creation to publication
- **Error Handling**: Retry logic and failure notifications
- **Admin Commands**: Bot status checking and test post creation
- **Webhook Integration**: Optional n8n notifications for external workflows

### Database Features
- **PostgreSQL Integration**: Robust database with full ACID compliance
- **Status Management**: Comprehensive workflow state tracking
- **Audit Trail**: Complete history of approvals, rejections, and publications
- **Performance Optimization**: Indexed queries for fast monitoring
- **Data Integrity**: Foreign key constraints and validation triggers
- **Backup Functions**: Built-in data export and cleanup utilities

## Development Notes

### HTML Application Development
- **No Build Process**: Direct HTML file - open in browser to run
- **No Dependencies**: Pure HTML/CSS/JavaScript with no external libraries
- **Testing**: Manual testing via browser - check form validation, webhook integration, and responsive design
- **Styling**: Embedded CSS with LinkedIn-blue color scheme (#003f7f)

### Discord Bot Development
- **Python Dependencies**: See `requirements.txt` for complete dependency list
- **Environment Setup**: Copy `.env.example` to `.env` and configure all required variables
- **Database Setup**: Run `schema.sql` to create PostgreSQL tables and functions
- **Testing**: Use `!test_post` command to create sample posts for approval workflow testing
- **Deployment**: Can run as standalone service or in Docker container

### Configuration Requirements
- **Discord Bot Token**: Create Discord application and bot at https://discord.com/developers/applications
- **LinkedIn API**: Register LinkedIn application for API access and OAuth tokens
- **PostgreSQL Database**: Local or hosted PostgreSQL instance
- **Channel IDs**: Discord channel IDs for approval and notification channels

## Integration & API Configuration

### HTML Application Webhook Configuration
The HTML application sends POST/PUT requests to LLM services with this JSON payload:
```json
{
  "prompt": "...",
  "temperature": 0.7,
  "max_tokens": 1500,
  "timestamp": "2023-...",
  "source": "linkedin-post-generator"
}
```

### LinkedIn API Configuration
The Discord bot integrates with LinkedIn's API v2 for post publishing:
```json
{
  "author": "urn:li:person:{person_id}",
  "lifecycleState": "PUBLISHED",
  "specificContent": {
    "com.linkedin.ugc.ShareContent": {
      "shareCommentary": {"text": "post_content"},
      "shareMediaCategory": "NONE|IMAGE"
    }
  },
  "visibility": {
    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
  }
}
```

### n8n Webhook Integration (Optional)
When posts are published, the system can send notifications to n8n workflows:
```json
{
  "event": "linkedin_post_published",
  "post_id": 123,
  "linkedin_post_id": "urn:li:share:123456789",
  "linkedin_url": "https://www.linkedin.com/posts/activity-123456789",
  "content": "post_content",
  "published_at": "2023-12-01T10:00:00Z",
  "industry": "Technology",
  "audience": "Tech professionals"
}
```

## Content Rules

Generated LinkedIn posts must follow strict formatting:
- First 3 lines form one paragraph (max 200 characters total)
- Australian English spelling and grammar
- Include one natural spelling error
- No call-to-action, hashtags, or emojis
- Conversational mate-to-mate tone
- Professional credibility through storytelling, not explicit claims

## Usage Instructions

### Setting Up the Discord Bot System

1. **Database Setup**:
   ```bash
   # Create PostgreSQL database
   createdb linkedin_posts
   
   # Run schema setup
   psql linkedin_posts < schema.sql
   ```

2. **Environment Configuration**:
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your actual configuration values
   nano .env
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Discord Bot**:
   ```bash
   python discord_linkedin_bot.py
   ```

### Creating Posts for Approval

**Option 1: Direct Database Insert**
```sql
INSERT INTO linkedin_posts (content, industry, audience, golden_threads)
VALUES (
    'Your LinkedIn post content here...',
    'Technology',
    'Software developers',
    'Data Analysis Value'
);
```

**Option 2: Using the HTML Application**
1. Open `linkedin-post-generator.html` in your browser
2. Fill out the form with post details
3. Configure webhook to insert into database instead of generating content

**Option 3: Bot Command (for testing)**
```
!test_post This is a test post for the approval workflow
```

### Bot Commands

- `!status` - Check bot and system status
- `!test_post [content]` - Create a test post (admin only)

The system will automatically:
1. Detect new pending posts in the database
2. Send mockups to Discord for approval
3. Publish approved posts to LinkedIn
4. Track all status changes and maintain audit trail