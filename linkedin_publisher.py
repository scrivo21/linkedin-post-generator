import requests
import json
import logging
from datetime import datetime
from config import Config
from models import db, PostStatus
from enhanced_logging import get_enhanced_logger

logger = get_enhanced_logger(__name__)

class LinkedInPublisher:
    def __init__(self):
        self.access_token = Config.LINKEDIN_ACCESS_TOKEN
        self.person_id = Config.LINKEDIN_PERSON_ID
        self.base_url = "https://api.linkedin.com/v2"
        
    def _get_headers(self):
        """Get headers for LinkedIn API requests"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
    
    async def publish_post(self, post):
        """Publish a post to LinkedIn"""
        try:
            logger.post_activity('publishing', post.draft_id, 'to LinkedIn...')
            
            # Validate post content
            validation_errors = self._validate_post(post)
            if validation_errors:
                raise ValueError(f"Post validation failed: {'; '.join(validation_errors)}")
            
            # Prepare the post data
            post_data = self._prepare_post_data(post)
            
            # Make the API request
            response = requests.post(
                f"{self.base_url}/ugcPosts",
                headers=self._get_headers(),
                data=json.dumps(post_data)
            )
            
            if response.status_code == 201:
                # Success
                result = response.json()
                linkedin_post_id = result.get('id')
                
                # Update database
                db.update_post_status(
                    post.draft_id, 
                    PostStatus.POSTED,
                    linkedin_post_id=linkedin_post_id,
                    linkedin_url=self._generate_post_url(linkedin_post_id)
                )
                
                logger.post_activity('published', post.draft_id, f'to LinkedIn (ID: {linkedin_post_id})')
                
                # Send webhook notification if configured
                await self._send_webhook_notification(post, linkedin_post_id)
                
                return {
                    "success": True,
                    "linkedin_post_id": linkedin_post_id,
                    "linkedin_url": self._generate_post_url(linkedin_post_id)
                }
            else:
                # Error
                error_message = f"LinkedIn API error: {response.status_code} - {response.text}"
                logger.error(error_message)
                
                # Update post with error
                db.update_post_status(
                    post.draft_id,
                    PostStatus.DECLINED,
                    last_error=error_message,
                    retry_count=post.retry_count + 1
                )
                
                return {
                    "success": False,
                    "error": error_message
                }
                
        except Exception as e:
            error_message = f"Error publishing post {post.draft_id}: {str(e)}"
            logger.error(error_message)
            
            # Update post with error
            db.update_post_status(
                post.draft_id,
                PostStatus.DECLINED,
                last_error=error_message,
                retry_count=post.retry_count + 1 if hasattr(post, 'retry_count') else 1
            )
            
            return {
                "success": False,
                "error": error_message
            }
    
    def _prepare_post_data(self, post):
        """Prepare post data for LinkedIn API"""
        data = {
            "author": f"urn:li:person:{self.person_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": post.content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        # Add image if present
        if post.image_path or post.image_base64:
            data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
            data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                {
                    "status": "READY",
                    "description": {
                        "text": "LinkedIn post image"
                    },
                    "media": post.image_path or post.image_base64,
                    "title": {
                        "text": "LinkedIn Post"
                    }
                }
            ]
        
        return data
    
    def _validate_post(self, post):
        """Validate post before publishing"""
        errors = []
        
        if not self.access_token:
            errors.append("LinkedIn access token not configured")
        
        if not self.person_id:
            errors.append("LinkedIn person ID not configured")
        
        if not post.content or not post.content.strip():
            errors.append("Post content is empty")
        
        if len(post.content) > 3000:
            errors.append("Post content exceeds LinkedIn's 3000 character limit")
        
        return errors
    
    def _generate_post_url(self, linkedin_post_id):
        """Generate a direct URL to the LinkedIn post"""
        if linkedin_post_id:
            # Extract numeric ID from URN format
            if "urn:li:share:" in linkedin_post_id:
                numeric_id = linkedin_post_id.split(":")[-1]
                return f"https://www.linkedin.com/posts/activity-{numeric_id}"
        return None
    
    async def _send_webhook_notification(self, post, linkedin_post_id):
        """Send webhook notification to n8n or other services"""
        if not Config.N8N_WEBHOOK_URL:
            return
        
        try:
            webhook_data = {
                "event": "linkedin_post_published",
                "post_id": post.draft_id,
                "linkedin_post_id": linkedin_post_id,
                "linkedin_url": self._generate_post_url(linkedin_post_id),
                "content": post.content,
                "published_at": datetime.now().isoformat(),
                "industry": post.industry,
                "audience": post.audience
            }
            
            response = requests.post(
                Config.N8N_WEBHOOK_URL,
                json=webhook_data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"🔔 Webhook notification sent successfully for post {post.draft_id}")
            else:
                logger.warning(f"Webhook notification failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
    
    def get_profile_info(self):
        """Get LinkedIn profile information"""
        try:
            response = requests.get(
                f"{self.base_url}/people/(id:{self.person_id})",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.api_call('LinkedIn', 'profile', response.status_code)
                return None
                
        except Exception as e:
            logger.error(f"Error fetching LinkedIn profile: {e}")
            return None
    
    def test_connection(self):
        """Test LinkedIn API connection"""
        try:
            profile = self.get_profile_info()
            if profile:
                logger.connection_status('LinkedIn API', True, 'Profile access confirmed')
                return True
            else:
                logger.connection_status('LinkedIn API', False, 'Profile access failed')
                return False
        except Exception as e:
            logger.error(f"LinkedIn API connection test failed: {e}")
            return False

# Global publisher instance
publisher = LinkedInPublisher()