# LinkedIn Analytics Implementation Plan

## Executive Summary

This document outlines a comprehensive plan to implement LinkedIn post performance tracking for our LinkedIn Post Generator system. The architecture is designed to work seamlessly with the current Discord bot system while providing a clear migration path to future iOS/macOS native applications with a Python backend.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [LinkedIn API Integration](#linkedin-api-integration)
3. [Database Schema Evolution](#database-schema-evolution)
4. [Core Analytics Service](#core-analytics-service)
5. [Current Discord Bot Integration](#current-discord-bot-integration)
6. [Future Native App Support](#future-native-app-support)
7. [Implementation Phases](#implementation-phases)
8. [Testing Strategy](#testing-strategy)
9. [Migration Path](#migration-path)
10. [Configuration & Deployment](#configuration--deployment)

## Architecture Overview

### Core Design Principles

- **API-First Architecture**: All functionality exposed via REST API endpoints
- **Database-Centric**: PostgreSQL as single source of truth for all platforms
- **Platform Agnostic**: Business logic separated from presentation layer
- **Modular Services**: Loosely coupled components for easy migration
- **Backwards Compatible**: Current Discord bot functionality remains unchanged

### System Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌──────────────┐
│   Discord Bot   │────▶│              │◀────│  iOS/macOS   │
│   (Current)     │     │   Python     │     │   App        │
└─────────────────┘     │   Backend    │     │  (Future)    │
                        │              │     └──────────────┘
┌─────────────────┐     │  - FastAPI   │     ┌──────────────┐
│  HTML Web App   │────▶│  - Analytics │◀────│   n8n/Make   │
│   (Current)     │     │  - Database  │     │  Webhooks    │
└─────────────────┘     │  - Monitor   │     └──────────────┘
                        └──────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  PostgreSQL  │
                        │  (Enhanced)  │
                        └──────────────┘
```

## LinkedIn API Integration

### Available APIs (2025)

1. **Member Post Analytics API** (Released July 2025)
   - First-party access to personal post metrics
   - Includes impressions, engagement, profile views, follower growth
   - Requires application approval from LinkedIn

2. **Share Statistics API** (v2)
   - Legacy API for organizational posts
   - Provides engagement metrics for company pages
   - Still available for approved developers

### API Access Strategy

#### Primary: Direct LinkedIn API Access

1. **Application Process**:
   - Visit https://developer.linkedin.com
   - Create new application
   - Select "Marketing Developer Platform" under Products
   - Complete detailed access request form
   - Wait for LinkedIn approval (typically 2-3 weeks)

2. **Required Information for Application**:
   - Business use case description
   - Data usage and storage policies
   - Compliance with LinkedIn's API terms
   - Expected volume and frequency of API calls

#### Fallback: Third-Party Integration

If direct API access is denied, integrate via approved platforms:
- **Hootsuite**: Has Member Post Analytics API access
- **Buffer**: Analytics API with LinkedIn metrics
- **Sprinklr**: Enterprise analytics platform

### API Implementation

```python
class LinkedInAPIClient:
    def __init__(self, access_token: str, person_id: str):
        self.access_token = access_token
        self.person_id = person_id
        self.base_url = "https://api.linkedin.com/rest"
    
    async def get_post_metrics(self, post_urn: str) -> dict:
        """Fetch metrics using Member Post Analytics API"""
        # Implementation details...
    
    async def get_share_statistics(self, share_urn: str) -> dict:
        """Fallback to Share Statistics API"""
        # Implementation details...
```

### URN Handling

LinkedIn posts use URN (Uniform Resource Name) identifiers:

- **Share URN**: `urn:li:share:123456789`
- **Activity URL**: `https://www.linkedin.com/feed/update/urn:li:activity:123456789`
- **UGC Post**: `urn:li:ugcPost:123456789`

```python
class URNHandler:
    @staticmethod
    def extract_urn_from_url(url: str) -> str:
        """Extract URN from LinkedIn post URL"""
        if 'linkedin.com/posts/activity-' in url:
            activity_id = url.split('activity-')[1].split('/')[0]
            return f"urn:li:share:{activity_id}"
        return None
    
    @staticmethod
    def urn_to_url(urn: str) -> str:
        """Convert URN to viewable LinkedIn URL"""
        if urn.startswith('urn:li:share:'):
            share_id = urn.split(':')[-1]
            return f"https://www.linkedin.com/feed/update/urn:li:activity:{share_id}"
        return None
```

## Database Schema Evolution

### Backwards-Compatible Schema Updates

Extend the existing `linkedin_posts` table without breaking current functionality:

```sql
-- Add new columns for analytics (all nullable for backwards compatibility)
ALTER TABLE linkedin_posts ADD COLUMN IF NOT EXISTS linkedin_urn VARCHAR(100);
ALTER TABLE linkedin_posts ADD COLUMN IF NOT EXISTS metrics JSONB DEFAULT '{}';
ALTER TABLE linkedin_posts ADD COLUMN IF NOT EXISTS metrics_summary JSONB DEFAULT '{}';
ALTER TABLE linkedin_posts ADD COLUMN IF NOT EXISTS metrics_last_updated TIMESTAMP WITH TIME ZONE;
ALTER TABLE linkedin_posts ADD COLUMN IF NOT EXISTS performance_tier VARCHAR(20);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_linkedin_posts_urn ON linkedin_posts(linkedin_urn);
CREATE INDEX IF NOT EXISTS idx_linkedin_posts_metrics_updated ON linkedin_posts(metrics_last_updated);
CREATE INDEX IF NOT EXISTS idx_linkedin_posts_performance ON linkedin_posts(performance_tier);
```

### New Tables for Historical Data

```sql
-- Store historical metrics snapshots
CREATE TABLE linkedin_metrics_snapshots (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES linkedin_posts(id),
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metrics_data JSONB NOT NULL,
    source VARCHAR(50) DEFAULT 'api', -- 'api', 'manual', 'third_party'
    
    -- Commonly queried metrics for performance
    impressions INTEGER,
    engagement_rate DECIMAL(5,4),
    likes INTEGER,
    comments INTEGER,
    shares INTEGER
);

-- Indexes for efficient querying
CREATE INDEX idx_metrics_snapshots_post_id ON linkedin_metrics_snapshots(post_id);
CREATE INDEX idx_metrics_snapshots_captured ON linkedin_metrics_snapshots(captured_at);
CREATE INDEX idx_metrics_snapshots_engagement ON linkedin_metrics_snapshots(engagement_rate DESC);
```

### Standardized Metrics Format

All metrics are stored in JSONB format for flexibility:

```json
{
    "impressions": 5000,
    "unique_impressions": 3500,
    "likes": 125,
    "comments": 23,
    "shares": 12,
    "clicks": 89,
    "engagement_rate": 0.032,
    "profile_views": 45,
    "new_followers": 8,
    "demographics": {
        "industries": ["Technology", "Marketing"],
        "seniorities": ["Manager", "Director"],
        "locations": ["Australia", "United States"]
    },
    "source": "member_post_analytics_api",
    "captured_at": "2025-01-20T10:00:00Z"
}
```

## Core Analytics Service

### LinkedInAnalyticsService Class

Platform-agnostic service that handles all analytics operations:

```python
# linkedin_analytics_service.py
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncpg
from dataclasses import dataclass

@dataclass
class PostMetrics:
    post_id: int
    urn: str
    impressions: int
    unique_impressions: int
    likes: int
    comments: int
    shares: int
    clicks: int
    engagement_rate: float
    profile_views: int
    new_followers: int
    captured_at: datetime

class LinkedInAnalyticsService:
    def __init__(self, db_connection, linkedin_api_client, config):
        self.db = db_connection
        self.linkedin_api = linkedin_api_client
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def fetch_metrics_for_post(self, post_id: int) -> Optional[PostMetrics]:
        """Fetch latest metrics from LinkedIn API for a specific post"""
        try:
            # Get post details from database
            post = await self.db.get_post_by_id(post_id)
            if not post or not post.linkedin_urn:
                self.logger.warning(f"Post {post_id} has no LinkedIn URN")
                return None
            
            # Fetch from LinkedIn API
            raw_metrics = await self.linkedin_api.get_post_metrics(post.linkedin_urn)
            
            # Convert to standard format
            metrics = self._process_raw_metrics(raw_metrics, post_id, post.linkedin_urn)
            
            # Store in database
            await self._store_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error fetching metrics for post {post_id}: {e}")
            return None
    
    async def bulk_update_metrics(self, post_ids: List[int] = None) -> Dict[str, int]:
        """Update metrics for multiple posts"""
        if post_ids is None:
            # Get all posts that need updates
            post_ids = await self._get_posts_needing_updates()
        
        results = {"success": 0, "failed": 0, "skipped": 0}
        
        # Process in batches to respect API rate limits
        batch_size = 10
        for i in range(0, len(post_ids), batch_size):
            batch = post_ids[i:i + batch_size]
            
            tasks = [self.fetch_metrics_for_post(post_id) for post_id in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    results["failed"] += 1
                elif result is None:
                    results["skipped"] += 1
                else:
                    results["success"] += 1
            
            # Rate limiting delay
            await asyncio.sleep(1)
        
        return results
    
    async def get_analytics_summary(self, days: int = 30) -> Dict:
        """Get analytics summary for dashboard"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = """
        SELECT 
            COUNT(*) as total_posts,
            AVG(CAST(metrics->>'engagement_rate' AS FLOAT)) as avg_engagement_rate,
            SUM(CAST(metrics->>'impressions' AS INTEGER)) as total_impressions,
            SUM(CAST(metrics->>'likes' AS INTEGER)) as total_likes,
            MAX(CAST(metrics->>'engagement_rate' AS FLOAT)) as best_engagement_rate
        FROM linkedin_posts 
        WHERE published_at >= $1 AND metrics IS NOT NULL
        """
        
        result = await self.db.fetchrow(query, cutoff_date)
        
        # Get top performing posts
        top_posts_query = """
        SELECT id, content, metrics->>'engagement_rate' as engagement_rate,
               metrics->>'impressions' as impressions
        FROM linkedin_posts 
        WHERE published_at >= $1 AND metrics IS NOT NULL
        ORDER BY CAST(metrics->>'engagement_rate' AS FLOAT) DESC
        LIMIT 5
        """
        
        top_posts = await self.db.fetch(top_posts_query, cutoff_date)
        
        return {
            "summary": dict(result) if result else {},
            "top_posts": [dict(post) for post in top_posts],
            "period": f"Last {days} days"
        }
    
    def _process_raw_metrics(self, raw_metrics: dict, post_id: int, urn: str) -> PostMetrics:
        """Convert LinkedIn API response to standard metrics format"""
        return PostMetrics(
            post_id=post_id,
            urn=urn,
            impressions=raw_metrics.get('impressions', 0),
            unique_impressions=raw_metrics.get('unique_impressions', 0),
            likes=raw_metrics.get('likes', 0),
            comments=raw_metrics.get('comments', 0),
            shares=raw_metrics.get('shares', 0),
            clicks=raw_metrics.get('clicks', 0),
            engagement_rate=self._calculate_engagement_rate(raw_metrics),
            profile_views=raw_metrics.get('profile_views', 0),
            new_followers=raw_metrics.get('new_followers', 0),
            captured_at=datetime.now()
        )
    
    def _calculate_engagement_rate(self, metrics: dict) -> float:
        """Calculate engagement rate from raw metrics"""
        impressions = metrics.get('impressions', 0)
        if impressions == 0:
            return 0.0
        
        total_engagements = (
            metrics.get('likes', 0) + 
            metrics.get('comments', 0) + 
            metrics.get('shares', 0)
        )
        
        return total_engagements / impressions
    
    async def _store_metrics(self, metrics: PostMetrics) -> None:
        """Store metrics in database"""
        # Update main post record
        update_query = """
        UPDATE linkedin_posts 
        SET 
            metrics = $1,
            metrics_summary = $2,
            metrics_last_updated = $3,
            performance_tier = $4
        WHERE id = $5
        """
        
        metrics_json = {
            "impressions": metrics.impressions,
            "unique_impressions": metrics.unique_impressions,
            "likes": metrics.likes,
            "comments": metrics.comments,
            "shares": metrics.shares,
            "clicks": metrics.clicks,
            "engagement_rate": metrics.engagement_rate,
            "profile_views": metrics.profile_views,
            "new_followers": metrics.new_followers,
            "captured_at": metrics.captured_at.isoformat()
        }
        
        summary = {
            "total_engagement": metrics.likes + metrics.comments + metrics.shares,
            "engagement_rate": metrics.engagement_rate,
            "reach": metrics.impressions
        }
        
        performance_tier = self._determine_performance_tier(metrics.engagement_rate)
        
        await self.db.execute(
            update_query, 
            metrics_json, 
            summary, 
            metrics.captured_at, 
            performance_tier, 
            metrics.post_id
        )
        
        # Store historical snapshot
        snapshot_query = """
        INSERT INTO linkedin_metrics_snapshots 
        (post_id, metrics_data, impressions, engagement_rate, likes, comments, shares)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """
        
        await self.db.execute(
            snapshot_query,
            metrics.post_id,
            metrics_json,
            metrics.impressions,
            metrics.engagement_rate,
            metrics.likes,
            metrics.comments,
            metrics.shares
        )
    
    def _determine_performance_tier(self, engagement_rate: float) -> str:
        """Categorize post performance"""
        if engagement_rate >= 0.05:  # 5%+
            return "viral"
        elif engagement_rate >= 0.03:  # 3-5%
            return "high"
        elif engagement_rate >= 0.015:  # 1.5-3%
            return "medium"
        elif engagement_rate >= 0.005:  # 0.5-1.5%
            return "low"
        else:
            return "minimal"
    
    async def _get_posts_needing_updates(self) -> List[int]:
        """Get list of post IDs that need metrics updates"""
        query = """
        SELECT id FROM linkedin_posts 
        WHERE status = 'published' 
        AND linkedin_urn IS NOT NULL
        AND (
            metrics_last_updated IS NULL 
            OR metrics_last_updated < NOW() - INTERVAL '1 hour'
        )
        ORDER BY published_at DESC
        """
        
        result = await self.db.fetch(query)
        return [row['id'] for row in result]
```

### Metrics Monitoring Scheduler

Standalone service for automated metrics updates:

```python
# metrics_scheduler.py
import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from linkedin_analytics_service import LinkedInAnalyticsService

class MetricsScheduler:
    def __init__(self, analytics_service: LinkedInAnalyticsService):
        self.analytics_service = analytics_service
        self.scheduler = AsyncIOScheduler()
        self.logger = logging.getLogger(__name__)
    
    def start(self):
        """Start the monitoring scheduler"""
        # Schedule different update frequencies based on post age
        self.scheduler.add_job(
            self.update_recent_posts,
            'interval',
            hours=1,
            id='recent_posts_hourly'
        )
        
        self.scheduler.add_job(
            self.update_medium_age_posts,
            'interval',
            hours=6,
            id='medium_posts_6hourly'
        )
        
        self.scheduler.add_job(
            self.update_older_posts,
            'interval',
            hours=24,
            id='older_posts_daily'
        )
        
        self.scheduler.start()
        self.logger.info("Metrics scheduler started")
    
    async def update_recent_posts(self):
        """Update metrics for posts less than 24 hours old"""
        post_ids = await self._get_posts_by_age(hours=24)
        await self.analytics_service.bulk_update_metrics(post_ids)
        self.logger.info(f"Updated {len(post_ids)} recent posts")
    
    async def update_medium_age_posts(self):
        """Update metrics for posts 1-7 days old"""
        post_ids = await self._get_posts_by_age(days_min=1, days_max=7)
        await self.analytics_service.bulk_update_metrics(post_ids)
        self.logger.info(f"Updated {len(post_ids)} medium-age posts")
    
    async def update_older_posts(self):
        """Update metrics for posts 7-30 days old"""
        post_ids = await self._get_posts_by_age(days_min=7, days_max=30)
        await self.analytics_service.bulk_update_metrics(post_ids)
        self.logger.info(f"Updated {len(post_ids)} older posts")
    
    async def _get_posts_by_age(self, hours=None, days_min=None, days_max=None):
        """Get posts within specific age range"""
        # Implementation to query database for posts in age range
        pass
```

## Current Discord Bot Integration

### Minimal Changes to Existing Bot

Update `discord_linkedin_bot.py` to add analytics commands:

```python
# Add imports
from linkedin_analytics_service import LinkedInAnalyticsService
from linkedin_api_client import LinkedInAPIClient

class LinkedInDiscordBot:
    def __init__(self):
        # Existing initialization code...
        
        # Add analytics service
        self.linkedin_api = LinkedInAPIClient(
            Config.LINKEDIN_ACCESS_TOKEN,
            Config.LINKEDIN_PERSON_ID
        )
        self.analytics_service = LinkedInAnalyticsService(
            self.db, 
            self.linkedin_api, 
            Config
        )
    
    # New analytics commands
    @commands.command(name='analytics', aliases=['stats'])
    async def show_post_analytics(self, ctx, post_id: int = None):
        """Show analytics for a specific post or recent posts summary"""
        try:
            if post_id:
                # Show specific post analytics
                metrics = await self.analytics_service.fetch_metrics_for_post(post_id)
                if metrics:
                    embed = self._create_post_metrics_embed(metrics)
                    await ctx.send(embed=embed)
                else:
                    await ctx.send(f"❌ No metrics available for post {post_id}")
            else:
                # Show recent posts summary
                summary = await self.analytics_service.get_analytics_summary(days=7)
                embed = self._create_summary_embed(summary)
                await ctx.send(embed=embed)
                
        except Exception as e:
            await ctx.send(f"❌ Error fetching analytics: {str(e)}")
    
    @commands.command(name='refresh_metrics')
    async def refresh_post_metrics(self, ctx, post_id: int):
        """Manually refresh metrics for a specific post"""
        try:
            metrics = await self.analytics_service.fetch_metrics_for_post(post_id)
            if metrics:
                await ctx.send(f"✅ Updated metrics for post {post_id}")
            else:
                await ctx.send(f"❌ Could not update metrics for post {post_id}")
        except Exception as e:
            await ctx.send(f"❌ Error updating metrics: {str(e)}")
    
    @commands.command(name='top_posts')
    async def show_top_posts(self, ctx, days: int = 7):
        """Show top performing posts in the last N days"""
        try:
            summary = await self.analytics_service.get_analytics_summary(days=days)
            embed = self._create_top_posts_embed(summary['top_posts'], days)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Error fetching top posts: {str(e)}")
    
    @commands.command(name='metrics_report')
    @commands.has_permissions(administrator=True)
    async def generate_metrics_report(self, ctx, days: int = 30):
        """Generate comprehensive metrics report (admin only)"""
        try:
            # Generate detailed report
            report_data = await self.analytics_service.get_detailed_report(days)
            
            # Create and send CSV file
            csv_content = self._generate_csv_report(report_data)
            file = discord.File(io.StringIO(csv_content), filename=f'linkedin_metrics_{days}d.csv')
            
            await ctx.send(f"📊 LinkedIn metrics report for last {days} days:", file=file)
        except Exception as e:
            await ctx.send(f"❌ Error generating report: {str(e)}")
    
    def _create_post_metrics_embed(self, metrics: PostMetrics) -> discord.Embed:
        """Create Discord embed for post metrics"""
        embed = discord.Embed(
            title=f"📊 Post Analytics - ID {metrics.post_id}",
            color=0x0077B5  # LinkedIn blue
        )
        
        # Performance indicator
        performance_emoji = {
            "viral": "🔥",
            "high": "🚀",
            "medium": "📈",
            "low": "📊",
            "minimal": "📉"
        }
        tier = self.analytics_service._determine_performance_tier(metrics.engagement_rate)
        
        embed.add_field(
            name=f"{performance_emoji.get(tier, '📊')} Performance",
            value=f"**{tier.title()}** ({metrics.engagement_rate:.2%} engagement)",
            inline=False
        )
        
        # Metrics
        embed.add_field(name="👁️ Impressions", value=f"{metrics.impressions:,}", inline=True)
        embed.add_field(name="👤 Unique Views", value=f"{metrics.unique_impressions:,}", inline=True)
        embed.add_field(name="💙 Likes", value=f"{metrics.likes:,}", inline=True)
        embed.add_field(name="💬 Comments", value=f"{metrics.comments:,}", inline=True)
        embed.add_field(name="🔄 Shares", value=f"{metrics.shares:,}", inline=True)
        embed.add_field(name="🖱️ Clicks", value=f"{metrics.clicks:,}", inline=True)
        
        # Profile impact
        if metrics.profile_views > 0:
            embed.add_field(name="👁️ Profile Views", value=f"{metrics.profile_views:,}", inline=True)
        if metrics.new_followers > 0:
            embed.add_field(name="➕ New Followers", value=f"{metrics.new_followers:,}", inline=True)
        
        embed.timestamp = metrics.captured_at
        embed.set_footer(text="Last updated")
        
        return embed
    
    def _create_summary_embed(self, summary: dict) -> discord.Embed:
        """Create summary embed for multiple posts"""
        data = summary['summary']
        embed = discord.Embed(
            title=f"📊 LinkedIn Analytics Summary - {summary['period']}",
            color=0x0077B5
        )
        
        if data:
            embed.add_field(
                name="📝 Total Posts", 
                value=f"{data.get('total_posts', 0):,}", 
                inline=True
            )
            embed.add_field(
                name="👁️ Total Impressions", 
                value=f"{data.get('total_impressions', 0):,}", 
                inline=True
            )
            embed.add_field(
                name="💙 Total Likes", 
                value=f"{data.get('total_likes', 0):,}", 
                inline=True
            )
            embed.add_field(
                name="📊 Avg Engagement Rate", 
                value=f"{data.get('avg_engagement_rate', 0):.2%}", 
                inline=True
            )
            embed.add_field(
                name="🔥 Best Performance", 
                value=f"{data.get('best_engagement_rate', 0):.2%}", 
                inline=True
            )
        else:
            embed.description = "No analytics data available for this period."
        
        return embed
```

### Enhanced Webhook Notifications

Update the existing webhook system to include analytics milestones:

```python
class AnalyticsWebhooks:
    @staticmethod
    async def send_milestone_notification(post_id: int, milestone: str, metrics: PostMetrics):
        """Send notification when post hits performance milestone"""
        webhook_data = {
            "event": "linkedin_post_milestone",
            "milestone": milestone,  # "1k_impressions", "viral", "top_performer"
            "post_id": post_id,
            "metrics": {
                "impressions": metrics.impressions,
                "engagement_rate": metrics.engagement_rate,
                "total_engagement": metrics.likes + metrics.comments + metrics.shares
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to configured webhooks (n8n, Discord, etc.)
        # Implementation...
```

## Future Native App Support

### REST API Endpoints

Create a comprehensive REST API for future iOS/macOS applications:

```python
# app_api.py
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
import json

app = FastAPI(title="LinkedIn Analytics API", version="1.0.0")
security = HTTPBearer()

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Implement JWT token validation
    # Return user object or raise HTTPException
    pass

@app.get("/api/posts", response_model=List[dict])
async def get_posts(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    user=Depends(get_current_user)
):
    """Get list of posts with basic metrics"""
    # Implementation...
    pass

@app.get("/api/posts/{post_id}/metrics")
async def get_post_metrics(post_id: int, user=Depends(get_current_user)):
    """Get detailed metrics for a specific post"""
    metrics = await analytics_service.fetch_metrics_for_post(post_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Post not found or no metrics available")
    
    return {
        "post_id": metrics.post_id,
        "urn": metrics.urn,
        "metrics": {
            "impressions": metrics.impressions,
            "unique_impressions": metrics.unique_impressions,
            "likes": metrics.likes,
            "comments": metrics.comments,
            "shares": metrics.shares,
            "clicks": metrics.clicks,
            "engagement_rate": metrics.engagement_rate,
            "profile_views": metrics.profile_views,
            "new_followers": metrics.new_followers
        },
        "performance_tier": analytics_service._determine_performance_tier(metrics.engagement_rate),
        "captured_at": metrics.captured_at.isoformat()
    }

@app.post("/api/posts/{post_id}/refresh")
async def refresh_post_metrics(post_id: int, user=Depends(get_current_user)):
    """Manually trigger metrics refresh for a post"""
    metrics = await analytics_service.fetch_metrics_for_post(post_id)
    if metrics:
        return {"status": "success", "message": f"Metrics updated for post {post_id}"}
    else:
        raise HTTPException(status_code=400, detail="Could not update metrics")

@app.get("/api/dashboard/summary")
async def get_dashboard_summary(days: int = 30, user=Depends(get_current_user)):
    """Get analytics summary for dashboard"""
    summary = await analytics_service.get_analytics_summary(days)
    return summary

@app.get("/api/posts/top")
async def get_top_posts(
    days: int = 30,
    limit: int = 10,
    user=Depends(get_current_user)
):
    """Get top performing posts"""
    # Implementation...
    pass

@app.get("/api/metrics/export")
async def export_metrics(
    format: str = "csv",
    days: int = 30,
    user=Depends(get_current_user)
):
    """Export metrics data in various formats"""
    # Implementation for CSV, JSON, Excel export
    pass

# WebSocket for real-time updates
@app.websocket("/ws/metrics")
async def metrics_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics updates"""
    await websocket.accept()
    
    try:
        while True:
            # Send real-time updates to connected clients
            # Implementation for live metrics streaming
            data = await websocket.receive_text()
            # Handle client messages if needed
    except WebSocketDisconnect:
        pass
```

### iOS/macOS Integration Points

Future native applications can integrate using:

1. **REST API Consumption**:
   ```swift
   // iOS Swift example
   class LinkedInAnalyticsAPI {
       private let baseURL = "https://your-api.com/api"
       private let session = URLSession.shared
       
       func fetchPostMetrics(postID: Int) async throws -> PostMetrics {
           let url = URL(string: "\(baseURL)/posts/\(postID)/metrics")!
           let (data, _) = try await session.data(from: url)
           return try JSONDecoder().decode(PostMetrics.self, from: data)
       }
       
       func refreshMetrics(postID: Int) async throws {
           let url = URL(string: "\(baseURL)/posts/\(postID)/refresh")!
           var request = URLRequest(url: url)
           request.httpMethod = "POST"
           let (_, _) = try await session.data(for: request)
       }
   }
   ```

2. **WebSocket for Real-time Updates**:
   ```swift
   class MetricsWebSocketManager: ObservableObject {
       private var webSocketTask: URLSessionWebSocketTask?
       
       func connect() {
           let url = URL(string: "wss://your-api.com/ws/metrics")!
           webSocketTask = URLSession.shared.webSocketTask(with: url)
           webSocketTask?.resume()
           receiveMessage()
       }
       
       private func receiveMessage() {
           webSocketTask?.receive { result in
               switch result {
               case .success(let message):
                   // Handle real-time metrics update
                   self.receiveMessage()
               case .failure(let error):
                   print("WebSocket error: \(error)")
               }
           }
       }
   }
   ```

3. **Core Data Sync**:
   - Local Core Data storage for offline access
   - Background sync with PostgreSQL via API
   - Conflict resolution for concurrent updates

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Apply for LinkedIn Marketing Developer Platform access
- [ ] Implement database schema updates (backwards compatible)
- [ ] Create `LinkedInAPIClient` class
- [ ] Create basic `LinkedInAnalyticsService` class
- [ ] Set up development environment and testing

### Phase 2: Core Analytics (Week 2)
- [ ] Implement URN extraction from existing LinkedIn URLs
- [ ] Create metrics fetching and storage logic
- [ ] Implement `MetricsScheduler` for automated updates
- [ ] Add error handling and rate limiting
- [ ] Create unit tests for core functionality

### Phase 3: Discord Integration (Week 3)
- [ ] Add analytics commands to Discord bot
- [ ] Create Discord embed formatting for metrics
- [ ] Implement webhook notifications for milestones
- [ ] Add CSV export functionality for reports
- [ ] Test with existing Discord bot functionality

### Phase 4: REST API (Week 4)
- [ ] Create FastAPI application with authentication
- [ ] Implement all REST endpoints for metrics
- [ ] Add WebSocket support for real-time updates
- [ ] Create API documentation (OpenAPI/Swagger)
- [ ] Add comprehensive API testing

### Phase 5: Testing & Optimization (Week 5)
- [ ] Performance testing with realistic data volumes
- [ ] Load testing for API endpoints
- [ ] Integration testing with mock iOS/macOS clients
- [ ] Security audit and vulnerability testing
- [ ] Documentation and deployment guides

### Phase 6: Production Deployment (Week 6)
- [ ] Set up production environment
- [ ] Configure monitoring and alerting
- [ ] Deploy with zero downtime migration
- [ ] Monitor initial performance and metrics
- [ ] User acceptance testing and feedback collection

## Testing Strategy

### Unit Tests
```python
# test_analytics_service.py
import pytest
from unittest.mock import AsyncMock, Mock
from linkedin_analytics_service import LinkedInAnalyticsService

class TestLinkedInAnalyticsService:
    @pytest.fixture
    async def analytics_service(self):
        db_mock = AsyncMock()
        api_mock = AsyncMock()
        config_mock = Mock()
        
        return LinkedInAnalyticsService(db_mock, api_mock, config_mock)
    
    @pytest.mark.asyncio
    async def test_fetch_metrics_for_post_success(self, analytics_service):
        # Mock successful API response
        analytics_service.db.get_post_by_id.return_value = Mock(
            id=1, 
            linkedin_urn="urn:li:share:123456"
        )
        
        analytics_service.linkedin_api.get_post_metrics.return_value = {
            "impressions": 1000,
            "likes": 50,
            "comments": 10,
            "shares": 5
        }
        
        metrics = await analytics_service.fetch_metrics_for_post(1)
        
        assert metrics is not None
        assert metrics.post_id == 1
        assert metrics.impressions == 1000
        assert metrics.engagement_rate > 0
    
    @pytest.mark.asyncio
    async def test_bulk_update_with_rate_limiting(self, analytics_service):
        # Test bulk update respects rate limits
        post_ids = list(range(1, 25))  # 24 posts
        
        analytics_service.fetch_metrics_for_post = AsyncMock(
            return_value=Mock()
        )
        
        result = await analytics_service.bulk_update_metrics(post_ids)
        
        assert result["success"] == 24
        assert result["failed"] == 0
```

### Integration Tests
```python
# test_discord_integration.py
import pytest
from unittest.mock import AsyncMock
from discord_linkedin_bot import LinkedInDiscordBot

class TestDiscordBotIntegration:
    @pytest.mark.asyncio
    async def test_analytics_command_with_valid_post(self):
        # Test Discord analytics command integration
        pass
    
    @pytest.mark.asyncio
    async def test_webhook_milestone_notification(self):
        # Test webhook notifications work correctly
        pass
```

### API Tests
```python
# test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app_api import app

client = TestClient(app)

def test_get_post_metrics_authorized():
    # Test API endpoint with valid authentication
    response = client.get("/api/posts/1/metrics", headers={"Authorization": "Bearer valid_token"})
    assert response.status_code == 200
    
    data = response.json()
    assert "metrics" in data
    assert "performance_tier" in data

def test_get_post_metrics_unauthorized():
    # Test API endpoint without authentication
    response = client.get("/api/posts/1/metrics")
    assert response.status_code == 401

def test_refresh_metrics_endpoint():
    # Test manual metrics refresh
    response = client.post("/api/posts/1/refresh", headers={"Authorization": "Bearer valid_token"})
    assert response.status_code in [200, 400]  # Success or valid error
```

### Performance Tests
```python
# test_performance.py
import asyncio
import time
import pytest
from linkedin_analytics_service import LinkedInAnalyticsService

class TestPerformance:
    @pytest.mark.asyncio
    async def test_bulk_update_performance(self):
        # Test bulk update can handle 100 posts in reasonable time
        start_time = time.time()
        
        # Mock service with realistic delays
        service = create_mock_service_with_delays()
        result = await service.bulk_update_metrics(list(range(100)))
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within 5 minutes (with rate limiting)
        assert duration < 300
        assert result["success"] > 90  # At least 90% success rate
    
    def test_database_query_performance(self):
        # Test database queries complete within acceptable time
        pass
```

## Migration Path

### Current State → Enhanced State

1. **Zero Downtime Migration**:
   - Database schema changes use `ALTER TABLE IF NOT EXISTS`
   - New columns are nullable to maintain compatibility
   - Existing Discord bot commands continue working

2. **Gradual Feature Rollout**:
   ```
   Week 1-2: Database + Core Service (invisible to users)
   Week 3: Discord analytics commands (new feature)
   Week 4: REST API (foundation for future apps)
   Week 5: iOS/macOS prototype development starts
   ```

3. **Data Migration Strategy**:
   ```sql
   -- Migrate existing LinkedIn URLs to URNs
   UPDATE linkedin_posts 
   SET linkedin_urn = extract_urn_from_url(linkedin_url)
   WHERE linkedin_urn IS NULL AND linkedin_url IS NOT NULL;
   
   -- Backfill metrics for recent posts
   -- Run initial metrics fetch for last 30 days of posts
   ```

### Current Discord Bot → Future Native Apps

The architecture supports both platforms simultaneously:

```
Current State:
Discord Bot → PostgreSQL

Enhanced State:
Discord Bot ↘
              Python Backend (FastAPI) → PostgreSQL
iOS/macOS App ↗

Future State (if desired):
Discord Bot ↘
              Python Backend (FastAPI) → PostgreSQL  
iOS/macOS App ↗
Web Dashboard ↗
```

### Feature Parity Matrix

| Feature | Discord Bot | REST API | iOS/macOS Ready |
|---------|-------------|----------|-----------------|
| View post metrics | ✅ | ✅ | ✅ |
| Refresh metrics | ✅ | ✅ | ✅ |
| Top posts report | ✅ | ✅ | ✅ |
| Export CSV | ✅ | ✅ | ✅ |
| Real-time updates | ❌ | ✅ (WebSocket) | ✅ |
| Push notifications | ✅ (Discord) | ✅ (API) | ✅ (APNS) |
| Visual charts | ❌ | ✅ (Data) | ✅ (Native) |
| Offline access | ❌ | ❌ | ✅ (Core Data) |

## Configuration & Deployment

### Environment Configuration

```bash
# .env file (works for all platforms)

# LinkedIn API Configuration
LINKEDIN_ACCESS_TOKEN=your_access_token_here
LINKEDIN_PERSON_ID=your_person_id_here
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/linkedin_posts

# API Configuration
ANALYTICS_API_PORT=8001
ANALYTICS_API_HOST=0.0.0.0
API_SECRET_KEY=your_jwt_secret_key_here

# Monitoring Configuration
METRICS_UPDATE_ENABLED=true
METRICS_SCHEDULER_ENABLED=true
METRICS_RATE_LIMIT=100  # API calls per day

# Webhook Configuration (optional)
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/linkedin
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook

# Logging Configuration
LOG_LEVEL=INFO
ANALYTICS_LOG_FILE=/var/log/linkedin_analytics.log
```

### Docker Deployment (Optional)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose API port
EXPOSE 8001

# Start both the scheduler and API server
CMD ["python", "start_services.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  linkedin-analytics:
    build: .
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/linkedin_posts
    depends_on:
      - db
    volumes:
      - ./logs:/var/log
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: linkedin_posts
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### Production Deployment Script

```bash
#!/bin/bash
# deploy.sh

echo "🚀 Deploying LinkedIn Analytics System..."

# Update database schema (backwards compatible)
echo "📊 Updating database schema..."
psql $DATABASE_URL < schema_updates.sql

# Install/update Python dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "🔄 Running data migrations..."
python migrate_existing_data.py

# Start services
echo "⚡ Starting services..."
systemctl restart linkedin-discord-bot
systemctl start linkedin-analytics-api
systemctl start linkedin-metrics-scheduler

echo "✅ Deployment complete!"
echo "📊 Analytics API available at: http://localhost:8001"
echo "📚 API documentation at: http://localhost:8001/docs"
```

### Monitoring & Alerting

```python
# monitoring.py
import logging
import asyncio
from datetime import datetime, timedelta
import asyncpg

class SystemMonitor:
    async def check_api_health(self):
        """Check LinkedIn API connectivity"""
        try:
            # Test API call
            result = await linkedin_api.get_profile_info()
            return {"status": "healthy", "api": "accessible"}
        except Exception as e:
            return {"status": "error", "api": str(e)}
    
    async def check_database_health(self):
        """Check database connectivity and performance"""
        try:
            start_time = datetime.now()
            await db.fetchval("SELECT 1")
            end_time = datetime.now()
            
            response_time = (end_time - start_time).total_seconds()
            
            return {
                "status": "healthy" if response_time < 1.0 else "slow",
                "response_time": response_time
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def check_metrics_freshness(self):
        """Check if metrics are being updated regularly"""
        try:
            query = """
            SELECT COUNT(*) as stale_count
            FROM linkedin_posts 
            WHERE status = 'published' 
            AND linkedin_urn IS NOT NULL
            AND (
                metrics_last_updated IS NULL 
                OR metrics_last_updated < NOW() - INTERVAL '4 hours'
            )
            """
            
            stale_count = await db.fetchval(query)
            
            return {
                "status": "healthy" if stale_count < 10 else "warning",
                "stale_posts": stale_count
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
```

## Conclusion

This comprehensive implementation plan provides:

1. **Seamless Integration**: Works with current Discord bot without breaking changes
2. **Future-Proof Architecture**: REST API ready for iOS/macOS native applications
3. **Scalable Design**: Database-centric approach supports multiple clients
4. **Robust Error Handling**: Graceful fallbacks and comprehensive monitoring
5. **Platform Agnostic**: Business logic separated from presentation layers

The phased approach ensures minimal risk while providing immediate value through Discord bot enhancements and establishing the foundation for future native applications.

### Next Steps

1. **Immediate**: Submit LinkedIn API access application
2. **Week 1**: Begin Phase 1 implementation (database + core service)
3. **Week 3**: Deploy Discord bot enhancements to production
4. **Week 4**: Complete REST API for future app development
5. **Week 6**: Begin iOS/macOS prototype development using the established API

This architecture ensures that the LinkedIn Analytics system can grow from the current Discord-based workflow to a comprehensive multi-platform solution while maintaining backwards compatibility and providing immediate value to users.