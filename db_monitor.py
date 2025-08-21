import asyncio
import logging
from datetime import datetime
from models import db, LinkedInDraft, PostStatus
from config import Config
from enhanced_logging import get_enhanced_logger

logger = get_enhanced_logger(__name__)

class DatabaseMonitor:
    def __init__(self, discord_bot=None):
        self.discord_bot = discord_bot
        self.running = False
        
    async def start_monitoring(self):
        """Start monitoring the database for new pending posts"""
        self.running = True
        logger.system_health('Database Monitor', 'healthy', {'poll_interval': f'{Config.POLL_INTERVAL}s'})
        
        while self.running:
            try:
                await self.check_for_pending_posts()
                await self.check_for_approved_posts()
                await asyncio.sleep(Config.POLL_INTERVAL)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)  # Wait before retrying
    
    def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.running = False
        logger.info("🔴 Stopping database monitoring...")
    
    async def check_for_pending_posts(self):
        """Check for new pending posts and notify Discord"""
        try:
            pending_posts = db.get_pending_posts()
            
            for post in pending_posts:
                logger.post_activity('detected', f'post_{post.id}', 'pending approval')
                
                if self.discord_bot:
                    # Send to Discord for approval
                    await self.discord_bot.send_approval_request(post)
                else:
                    logger.warning("Discord bot not available, skipping notification")
                    
        except Exception as e:
            logger.error(f"Error checking pending posts: {e}")
    
    async def check_for_approved_posts(self):
        """Check for approved posts ready for LinkedIn publishing"""
        try:
            approved_posts = db.get_approved_posts()
            
            for post in approved_posts:
                logger.post_activity('detected', f'post_{post.id}', 'ready for publishing')
                
                if self.discord_bot:
                    # Trigger LinkedIn publishing
                    await self.discord_bot.publish_to_linkedin(post)
                else:
                    logger.warning("Discord bot not available, skipping publication")
                    
        except Exception as e:
            logger.error(f"Error checking approved posts: {e}")

class PostProcessor:
    """Utility class for processing posts"""
    
    @staticmethod
    def create_linkedin_preview(post):
        """Create a preview of how the post will look on LinkedIn"""
        content = post.content
        
        # Truncate if too long for preview
        if len(content) > 500:
            content = content[:497] + "..."
        
        return {
            "content": content,
            "has_image": bool(post.image_path or post.image_base64),
            "image_url": post.image_path,
            "character_count": len(post.content),
            "estimated_engagement": PostProcessor.estimate_engagement(post),
            "hashtags": PostProcessor.extract_hashtags(post.content),
            "mentions": PostProcessor.extract_mentions(post.content)
        }
    
    @staticmethod
    def estimate_engagement(post):
        """Simple heuristic to estimate potential engagement"""
        content = post.content.lower()
        
        # Basic engagement factors
        score = 0
        
        # Length factor (optimal LinkedIn posts are 1-3 sentences)
        word_count = len(content.split())
        if 20 <= word_count <= 150:
            score += 10
        
        # Question factor
        if '?' in content:
            score += 5
        
        # Personal story factor
        personal_indicators = ['i ', 'my ', 'me ', 'personally', 'experience']
        if any(indicator in content for indicator in personal_indicators):
            score += 8
        
        # Industry relevance
        if post.industry:
            score += 5
        
        # Image factor
        if post.image_path or post.image_base64:
            score += 7
        
        # Convert to engagement estimate
        if score >= 25:
            return "High"
        elif score >= 15:
            return "Medium"
        else:
            return "Low"
    
    @staticmethod
    def extract_hashtags(content):
        """Extract hashtags from content"""
        import re
        return re.findall(r'#\w+', content)
    
    @staticmethod
    def extract_mentions(content):
        """Extract mentions from content"""
        import re
        return re.findall(r'@\w+', content)
    
    @staticmethod
    def validate_post_content(content):
        """Validate LinkedIn post content"""
        errors = []
        
        if not content or not content.strip():
            errors.append("Content cannot be empty")
        
        if len(content) > 3000:
            errors.append("Content exceeds LinkedIn's 3000 character limit")
        
        # Check for appropriate professional tone
        inappropriate_words = ['fuck', 'shit', 'damn']  # Basic profanity check
        for word in inappropriate_words:
            if word.lower() in content.lower():
                errors.append(f"Content contains inappropriate language: {word}")
        
        return errors

# Global monitor instance
monitor = DatabaseMonitor()