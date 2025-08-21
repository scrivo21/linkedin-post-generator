import discord
from discord.ext import commands, tasks
import asyncio
import logging
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import requests
import aiohttp

from config import Config
from models import db, LinkedInDraft, PostStatus, FormSubmission, FormSubmissionStatus
from db_monitor import monitor, PostProcessor
from linkedin_publisher import publisher
from enhanced_logging import get_enhanced_logger, setup_enhanced_logging, check_dependencies
try:
    from colorama import Fore, Back, Style, init
    init(autoreset=True)
except ImportError:
    # Fallback if colorama is not available
    class MockColor:
        def __getattr__(self, name): return ''
    Fore = Back = Style = MockColor()

# Setup enhanced logging system
setup_enhanced_logging()
logger = get_enhanced_logger(__name__)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix=Config.BOT_PREFIX, intents=intents)

class LinkedInPostModal(discord.ui.Modal, title="Create LinkedIn Post"):
    """Modal form for creating LinkedIn posts - matches HTML form structure"""
    
    def __init__(self):
        super().__init__()
    
    # Core Content Details
    industry = discord.ui.TextInput(
        label="Topic/Industry",
        placeholder="e.g., Digital Marketing, Recruitment, SaaS",
        style=discord.TextStyle.short,
        max_length=100,
        required=True
    )
    
    audience = discord.ui.TextInput(
        label="Target Audience",
        placeholder="e.g., startup founders, marketing managers",
        style=discord.TextStyle.short,
        max_length=100,
        required=True
    )
    
    situation = discord.ui.TextInput(
        label="Specific Situation/Challenge",
        placeholder="Describe the specific scenario or challenge you're addressing...",
        style=discord.TextStyle.paragraph,
        max_length=500,
        required=True
    )
    
    key_insight = discord.ui.TextInput(
        label="Key Insight/Lesson",
        placeholder="What's your main point or takeaway?",
        style=discord.TextStyle.paragraph,
        max_length=400,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission - show second modal for additional fields"""
        try:
            logger.info(f"📝 LinkedIn post form step 1 submitted by {interaction.user.name}")
            
            # Store first modal data temporarily
            user_data = {
                'industry': self.industry.value,
                'audience': self.audience.value,
                'situation': self.situation.value,
                'key_insight': self.key_insight.value,
                'user_id': interaction.user.id,
                'username': interaction.user.name
            }
            
            # Create embed showing progress and next steps
            embed = discord.Embed(
                title="✅ Step 1 Complete - Continue to Step 2",
                description="Great! Your core content details have been saved.\n\n**Next:** Please complete the remaining fields to create your LinkedIn post.",
                color=0x0077B5,  # LinkedIn blue
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📋 Step 1 Summary",
                value=f"**Industry:** {self.industry.value}\n**Audience:** {self.audience.value}",
                inline=False
            )
            
            embed.add_field(
                name="📝 Step 2 Required",
                value="• Your Experience/Background\n• Credibility Signpost\n• Personal Anecdote\n• Timeframe/Context\n• Additional Context (Optional)",
                inline=False
            )
            
            embed.set_footer(text="Click the button below to continue to Step 2")
            
            # Show second modal with clear instructions
            second_modal = LinkedInPostModalStep2(user_data)
            await interaction.response.send_message(
                embed=embed, 
                view=SecondFormView(second_modal), 
                ephemeral=True
            )
            
        except Exception as e:
            logger.error(f"Error handling form submission step 1: {e}")
            await interaction.response.send_message("❌ Error processing form. Please try again.", ephemeral=True)

class LinkedInPostModalStep2(discord.ui.Modal, title="LinkedIn Post - Additional Details"):
    """Second step modal for remaining LinkedIn post fields"""
    
    def __init__(self, first_step_data):
        super().__init__()
        self.first_step_data = first_step_data
    
    # Background & Credibility
    experience = discord.ui.TextInput(
        label="Your Experience/Background",
        placeholder="Your relevant experience, qualifications, or credentials...",
        style=discord.TextStyle.paragraph,
        max_length=600,
        required=True
    )
    
    credibility_signpost = discord.ui.TextInput(
        label="Credibility Signpost",
        placeholder='e.g., "After 12 years in recruitment..." or "Having closed over 200 deals..."',
        style=discord.TextStyle.short,
        max_length=150,
        required=True
    )
    
    # Story & Context
    personal_anecdote = discord.ui.TextInput(
        label="Personal Anecdote",
        placeholder="Share a brief personal story or example that illustrates your point...",
        style=discord.TextStyle.paragraph,
        max_length=800,
        required=True
    )
    
    timeframe = discord.ui.TextInput(
        label="Timeframe/Context",
        placeholder="e.g., Last quarter, During the pandemic, 3 months ago",
        style=discord.TextStyle.short,
        max_length=100,
        required=True
    )
    
    contextual_info = discord.ui.TextInput(
        label="Contextual Information (Optional)",
        placeholder="Industry trends, statistics, background info, market conditions, etc...",
        style=discord.TextStyle.paragraph,
        max_length=600,
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle final form submission"""
        try:
            await interaction.response.defer()
            logger.info(f"📝 LinkedIn post form completed by {self.first_step_data['username']}")
            
            # Combine all form data
            full_form_data = {
                **self.first_step_data,
                'experience': self.experience.value,
                'credibility_signpost': self.credibility_signpost.value,
                'personal_anecdote': self.personal_anecdote.value,
                'timeframe': self.timeframe.value,
                'contextual_info': self.contextual_info.value or "",
                'golden_threads': "",  # Will be handled separately
                'spelling_error': ""   # Optional field
            }
            
            # Create form submission in database (not a LinkedIn draft yet)
            form_submission = db.create_form_submission(
                form_data=full_form_data,
                source=f"discord-form-{full_form_data['username']}"
            )
            
            # Send form data to n8n webhook for LLM processing
            webhook_success = await self.send_to_n8n_webhook(full_form_data, str(form_submission.submission_id))
            
            if webhook_success:
                embed = discord.Embed(
                    title="✅ Form Submitted & Sent to n8n",
                    description=f"Form submission ID: `{form_submission.submission_id}` sent to n8n for LinkedIn post generation",
                    color=0x00FF00,
                    timestamp=datetime.now()
                )
                embed.add_field(name="📊 Status", value="Processing via LLM workflow", inline=True)
            else:
                embed = discord.Embed(
                    title="⚠️ Form Submitted (Webhook Failed)",
                    description=f"Form submission ID: `{form_submission.submission_id}` created but n8n webhook failed",
                    color=0xFFA500,
                    timestamp=datetime.now()
                )
                embed.add_field(name="📊 Status", value="Saved in database, webhook failed", inline=True)
            
            # Add field previews
            embed.add_field(name="🏢 Industry", value=full_form_data['industry'], inline=True)
            embed.add_field(name="👥 Audience", value=full_form_data['audience'], inline=True)
            
            # Add situation preview
            situation_preview = full_form_data['situation'][:100] + "..." if len(full_form_data['situation']) > 100 else full_form_data['situation']
            embed.add_field(name="🎯 Situation", value=situation_preview, inline=False)
            
            # Add insight preview
            insight_preview = full_form_data['key_insight'][:100] + "..." if len(full_form_data['key_insight']) > 100 else full_form_data['key_insight']
            embed.add_field(name="💡 Key Insight", value=insight_preview, inline=False)
            
            embed.set_footer(text=f"Created by @{full_form_data['username']} • {datetime.now().strftime('%H:%M')}")
            
            await interaction.followup.send(embed=embed)
            logger.info(f"Form submission created by {full_form_data['username']}: {form_submission.submission_id}")
            
        except Exception as e:
            logger.error(f"Error handling complete form submission: {e}")
            await interaction.followup.send("❌ Error creating post. Please try again.", ephemeral=True)
    
    def build_comprehensive_content(self, data):
        """Build comprehensive content from all form fields"""
        content_parts = [
            f"Industry: {data['industry']}",
            f"Target Audience: {data['audience']}",
            f"",
            f"Situation/Challenge:",
            data['situation'],
            f"",
            f"Key Insight/Lesson:",
            data['key_insight'],
            f"",
            f"Experience/Background:",
            data['experience'],
            f"",
            f"Credibility Signpost: {data['credibility_signpost']}",
            f"",
            f"Personal Anecdote:",
            data['personal_anecdote'],
            f"",
            f"Timeframe: {data['timeframe']}"
        ]
        
        if data['contextual_info']:
            content_parts.extend([
                f"",
                f"Contextual Information:",
                data['contextual_info']
            ])
        
        return "\n".join(content_parts)
    
    async def send_to_n8n_webhook(self, form_data, submission_id):
        """Send form data directly to n8n webhook"""
        try:
            from config import Config
            
            # Get webhook URL from config - no hardcoded fallbacks
            webhook_url = Config.N8N_WEBHOOK_URL
            if not webhook_url or webhook_url == "https://your-n8n-instance.com/webhook/linkedin-published":
                logger.error("❌ N8N_WEBHOOK_URL not configured in .env file")
                return False
            
            # Prepare payload with form submission data
            payload = {
                "submission_id": submission_id,
                "industry": form_data['industry'],
                "audience": form_data['audience'],
                "situation": form_data['situation'],
                "keyInsight": form_data['key_insight'],
                "experience": form_data['experience'],
                "credibilitySignpost": form_data['credibility_signpost'],
                "personalAnecdote": form_data['personal_anecdote'],
                "timeframe": form_data['timeframe'],
                "contextualInfo": form_data['contextual_info'],
                "goldenThreads": [],  # Could be expanded later
                "spellingError": "",  # Optional field
                "timestamp": datetime.now().isoformat(),
                "source": "discord-linkedin-bot"
            }
            
            logger.info(f"🔗 Sending form submission {submission_id} to n8n webhook: {webhook_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.text()
                        logger.info(f"✅ n8n webhook success for submission {submission_id}: {response.status}")
                        return True
                    else:
                        logger.error(f"❌ n8n webhook failed for submission {submission_id}: {response.status} - {await response.text()}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Error sending to n8n webhook: {e}")
            return False

class SecondFormView(discord.ui.View):
    """View to hold the button for the second form"""
    
    def __init__(self, modal):
        super().__init__(timeout=300)  # 5 minute timeout
        self.modal = modal
    
    @discord.ui.button(label='Continue to Step 2 - Complete Your Post', style=discord.ButtonStyle.primary, emoji='➡️')
    async def continue_form(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open the second form with remaining fields"""
        await interaction.response.send_modal(self.modal)
        # Update the original message to show the user has proceeded
        try:
            embed = discord.Embed(
                title="📝 Step 2 Form Opened",
                description="Please complete the form that just opened to finish creating your LinkedIn post.",
                color=0x00FF00
            )
            await interaction.edit_original_response(embed=embed, view=None)
        except:
            pass  # In case the interaction has already been responded to

class ApprovalView(discord.ui.View):
    def __init__(self, draft_id):
        super().__init__(timeout=24*60*60)  # 24 hour timeout
        self.draft_id = draft_id
    
    @discord.ui.button(label='✅ Approve', style=discord.ButtonStyle.green, custom_id='approve')
    async def approve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_approval(interaction, 'approved')
    
    @discord.ui.button(label='❌ Reject', style=discord.ButtonStyle.red, custom_id='reject')
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_approval(interaction, 'rejected')
    
    @discord.ui.button(label='📝 Request Edit', style=discord.ButtonStyle.secondary, custom_id='edit')
    async def edit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_approval(interaction, 'edit_requested')
    
    async def handle_approval(self, interaction: discord.Interaction, action):
        try:
            # Defer the response to give us time to process
            await interaction.response.defer()
            
            # Update database based on action
            if action == 'approved':
                # Handle Discord's new username system (discriminator can be None)
                user_identifier = f"{interaction.user.name}#{interaction.user.discriminator}" if interaction.user.discriminator else interaction.user.name
                
                db.update_post_status(
                    self.draft_id,
                    PostStatus.APPROVED_FOR_SOCIALS,
                    discord_approver=user_identifier
                )
                
                # Create success embed
                embed = discord.Embed(
                    title="✅ Post Approved",
                    description=f"Post `{self.draft_id}` approved by {interaction.user.mention}",
                    color=0x00FF00,
                    timestamp=datetime.now()
                )
                
                logger.post_activity('approved', self.draft_id, f"by {interaction.user.name}")
                
            elif action == 'rejected':
                # Handle Discord's new username system (discriminator can be None)
                user_identifier = f"{interaction.user.name}#{interaction.user.discriminator}" if interaction.user.discriminator else interaction.user.name
                
                db.update_post_status(
                    self.draft_id,
                    PostStatus.DECLINED,
                    discord_approver=user_identifier,
                    last_error="Rejected via Discord button"
                )
                
                # Create rejection embed
                embed = discord.Embed(
                    title="❌ Post Rejected",
                    description=f"Post `{self.draft_id}` rejected by {interaction.user.mention}",
                    color=0xFF0000,
                    timestamp=datetime.now()
                )
                
                logger.post_activity('rejected', self.draft_id, f"by {interaction.user.name}")
                
            elif action == 'edit_requested':
                # Handle Discord's new username system (discriminator can be None)
                user_identifier = f"{interaction.user.name}#{interaction.user.discriminator}" if interaction.user.discriminator else interaction.user.name
                
                db.update_post_status(
                    self.draft_id,
                    PostStatus.PENDING,
                    discord_approver=user_identifier,
                    last_error="Edit requested via Discord button"
                )
                
                # Create edit request embed
                embed = discord.Embed(
                    title="📝 Edit Requested",
                    description=f"Edit requested for post `{self.draft_id}` by {interaction.user.mention}",
                    color=0xFFA500,
                    timestamp=datetime.now()
                )
                
                logger.post_activity('edited', self.draft_id, f"edit requested by {interaction.user.name}")
            
            # Disable all buttons after action
            for item in self.children:
                item.disabled = True
            
            # Update the message
            await interaction.edit_original_response(embed=embed, view=self)
            
        except Exception as e:
            logger.error(f"Error handling approval action: {e}")
            await interaction.followup.send(f"❌ Error processing approval: {e}", ephemeral=True)
    
    async def on_timeout(self):
        # Disable all buttons when timeout occurs
        for item in self.children:
            item.disabled = True

class LinkedInBot:
    def __init__(self):
        self.approval_channel = None
        self.notification_channel = None
        
    async def setup_channels(self):
        """Setup Discord channels"""
        try:
            self.approval_channel = bot.get_channel(Config.DISCORD_APPROVAL_CHANNEL_ID)
            self.notification_channel = bot.get_channel(Config.DISCORD_NOTIFICATION_CHANNEL_ID)
            
            if not self.approval_channel:
                logger.error(f"Could not find approval channel with ID: {Config.DISCORD_APPROVAL_CHANNEL_ID}")
            
            if not self.notification_channel:
                logger.warning(f"Could not find notification channel with ID: {Config.DISCORD_NOTIFICATION_CHANNEL_ID}")
                
        except Exception as e:
            logger.error(f"Error setting up channels: {e}")
    
    async def send_approval_request(self, post):
        """Send a post to Discord for approval"""
        try:
            if not self.approval_channel:
                await self.setup_channels()
                
            if not self.approval_channel:
                logger.error("Approval channel not available")
                return
            
            # Create LinkedIn-style preview embed
            embed = self.create_post_preview_embed(post)
            
            # Generate mockup image
            mockup_file = await self.create_linkedin_mockup(post)
            
            # Create approval buttons
            view = ApprovalView(post.draft_id)
            
            # Send message with embed, buttons, and full content
            message = await self.approval_channel.send(
                content=f"🔔 **New LinkedIn Post Pending Approval** (ID: {post.draft_id})\n\n**Full Post Content:**\n```\n{post.content}\n```",
                embed=embed,
                view=view,
                file=mockup_file if mockup_file else None
            )
            
            # Update database with Discord message ID
            db.update_post_status(
                post.draft_id,
                PostStatus.PENDING,
                discord_message_id=str(message.id),
                discord_channel_id=str(self.approval_channel.id)
            )
            
            logger.post_activity('created', post.draft_id, 'sent to Discord for approval')
            
        except Exception as e:
            logger.error(f"Error sending approval request for post {post.draft_id}: {e}")
    
    def create_post_preview_embed(self, post):
        """Create a Discord embed showing LinkedIn post preview"""
        preview = PostProcessor.create_linkedin_preview(post)
        
        embed = discord.Embed(
            title="📱 LinkedIn Post Preview",
            description=preview["content"],
            color=0x0077B5,  # LinkedIn blue
            timestamp=datetime.now()
        )
        
        # Add post metadata
        embed.add_field(
            name="📊 Post Analytics",
            value=f"**Characters:** {preview['character_count']}/3000\n"
                  f"**Estimated Engagement:** {preview['estimated_engagement']}\n"
                  f"**Has Image:** {'Yes' if preview['has_image'] else 'No'}",
            inline=True
        )
        
        if post.industry:
            embed.add_field(
                name="🏢 Industry",
                value=post.industry,
                inline=True
            )
        
        if post.audience:
            embed.add_field(
                name="🎯 Target Audience",
                value=post.audience,
                inline=True
            )
        
        if post.golden_threads:
            embed.add_field(
                name="🧵 Golden Threads",
                value=post.golden_threads,
                inline=False
            )
        
        # Add hashtags and mentions if present
        if preview["hashtags"]:
            embed.add_field(
                name="# Hashtags",
                value=" ".join(preview["hashtags"]),
                inline=True
            )
        
        if preview["mentions"]:
            embed.add_field(
                name="@ Mentions",
                value=" ".join(preview["mentions"]),
                inline=True
            )
        
        # Add image if present
        if post.image_path:
            embed.set_image(url=post.image_path)
        
        embed.set_footer(
            text=f"Post ID: {post.draft_id} | Created: {post.created_at.strftime('%Y-%m-%d %H:%M')}"
        )
        
        return embed
    
    async def create_linkedin_mockup(self, post):
        """Create a LinkedIn-style mockup image"""
        try:
            # Create a simple mockup (you can enhance this with more sophisticated graphics)
            width, height = 600, 400
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Try to use a nice font, fallback to default
            try:
                font_large = ImageFont.truetype("arial.ttf", 16)
                font_small = ImageFont.truetype("arial.ttf", 12)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # LinkedIn header
            draw.rectangle([(0, 0), (width, 60)], fill='#0077B5')
            draw.text((20, 20), "LinkedIn Post Preview", fill='white', font=font_large)
            
            # Post content
            content = post.content
            if len(content) > 300:
                content = content[:297] + "..."
            
            # Wrap text
            lines = []
            words = content.split()
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if len(test_line) > 70:  # Approximate character limit per line
                    lines.append(current_line)
                    current_line = word
                else:
                    current_line = test_line
            
            if current_line:
                lines.append(current_line)
            
            # Draw text lines
            y_offset = 80
            for line in lines[:15]:  # Limit to 15 lines
                draw.text((20, y_offset), line, fill='black', font=font_small)
                y_offset += 20
            
            # Save to bytes
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            return discord.File(img_bytes, filename=f"linkedin_preview_{post.draft_id}.png")
            
        except Exception as e:
            logger.error(f"Error creating LinkedIn mockup: {e}")
            return None
    
    async def publish_to_linkedin(self, post):
        """Publish approved post to LinkedIn"""
        try:
            result = await publisher.publish_post(post)
            
            if result["success"]:
                # Notify success
                if self.notification_channel:
                    embed = discord.Embed(
                        title="✅ LinkedIn Post Published Successfully",
                        description=f"Post {post.draft_id} has been published to LinkedIn!",
                        color=0x00FF00,
                        timestamp=datetime.now()
                    )
                    
                    if result.get("linkedin_url"):
                        embed.add_field(
                            name="🔗 LinkedIn URL",
                            value=f"[View Post]({result['linkedin_url']})",
                            inline=False
                        )
                    
                    embed.add_field(
                        name="📝 Content Preview",
                        value=post.content[:200] + "..." if len(post.content) > 200 else post.content,
                        inline=False
                    )
                    
                    await self.notification_channel.send(embed=embed)
                
                logger.post_activity('published', post.draft_id, 'to LinkedIn successfully')
            else:
                # Notify failure
                if self.notification_channel:
                    embed = discord.Embed(
                        title="❌ LinkedIn Post Publishing Failed",
                        description=f"Failed to publish post {post.draft_id}",
                        color=0xFF0000,
                        timestamp=datetime.now()
                    )
                    
                    embed.add_field(
                        name="Error",
                        value=result.get("error", "Unknown error"),
                        inline=False
                    )
                    
                    await self.notification_channel.send(embed=embed)
                
                logger.error(f"❌ Failed to publish post {post.draft_id}: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error in publish_to_linkedin: {e}")

# Global bot instance
linkedin_bot = LinkedInBot()

@bot.event
async def on_ready():
    """Bot startup event"""
    # Display impressive startup banner with ASCII art
    logger.startup_banner("Discord LinkedIn Bot", "v1.0")
    
    # Log Discord connection with enhanced styling
    logger.connection_status("Discord", True, f"Connected as {bot.user} ({bot.user.id})")
    
    # Display bot statistics
    guild_count = len(bot.guilds)
    total_members = sum(guild.member_count for guild in bot.guilds if guild.member_count)
    logger.info(f"🏠 Connected to {guild_count} guilds with {total_members} total members")
    
    # Start the command sync task
    logger.info("📝 Starting post-initialization command sync task...")
    sync_commands_after_ready.start()
    
    # Note: Approval process removed - posts go directly to n8n webhook
    logger.info("📝 Direct-to-n8n mode: Posts will be sent directly to webhook without approval")
    
    # Test LinkedIn connection with enhanced feedback
    logger.info("🔗 Testing LinkedIn API connection...")
    connection_success = publisher.test_connection()
    logger.connection_status("LinkedIn API", connection_success, 
                           "Ready for automated posting" if connection_success else "Check API credentials")
    
    # Final startup message
    logger.info("🎉 Discord LinkedIn Bot is fully operational and ready!")
    logger.info(f"💡 Use {Config.BOT_PREFIX}help for commands or try slash commands with /")
    
    # Show divider for clean separation from runtime logs
    print(f"\n{Fore.CYAN}{'═' * 88}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}🚀 BOT READY - Runtime logs will appear below{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'═' * 88}{Style.RESET_ALL}\n")

# Reaction-based approval removed - now using Discord UI buttons

# Slash Commands
@bot.tree.command(name="status", description="Check bot status and statistics")
async def status_slash(interaction: discord.Interaction):
    """Check bot status via slash command"""
    embed = discord.Embed(
        title="🤖 Bot Status",
        color=0x0077B5,
        timestamp=datetime.now()
    )
    
    # Database connection
    try:
        pending_count = len(db.get_pending_posts())
        approved_count = len(db.get_approved_posts())
        embed.add_field(
            name="📊 Database",
            value=f"✅ Connected\nPending: {pending_count}\nApproved: {approved_count}",
            inline=True
        )
    except Exception as e:
        embed.add_field(
            name="📊 Database",
            value=f"❌ Error: {str(e)[:50]}",
            inline=True
        )
    
    # LinkedIn API
    linkedin_status = "✅ Connected" if publisher.test_connection() else "❌ Disconnected"
    embed.add_field(
        name="🔗 LinkedIn API",
        value=linkedin_status,
        inline=True
    )
    
    # Channels
    approval_status = "✅ Found" if linkedin_bot.approval_channel else "❌ Not Found"
    embed.add_field(
        name="📢 Approval Channel",
        value=approval_status,
        inline=True
    )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="linkedin", description="Create a new LinkedIn post for approval")
async def linkedin_slash(interaction: discord.Interaction):
    """Show LinkedIn post creation form"""
    logger.info(f"🎯 LinkedIn slash command called by {interaction.user.name}")
    try:
        modal = LinkedInPostModal()
        await interaction.response.send_modal(modal)
        logger.info(f"📝 LinkedIn post form shown to {interaction.user.name}")
    except Exception as e:
        logger.error(f"Error showing LinkedIn form: {e}")
        await interaction.response.send_message("❌ Error opening LinkedIn post form.", ephemeral=True)

@bot.command(name='status')
async def status_command(ctx):
    """Check bot status"""
    embed = discord.Embed(
        title="🤖 Bot Status",
        color=0x0077B5,
        timestamp=datetime.now()
    )
    
    # Database connection
    try:
        pending_count = len(db.get_pending_posts())
        approved_count = len(db.get_approved_posts())
        embed.add_field(
            name="📊 Database",
            value=f"✅ Connected\nPending: {pending_count}\nApproved: {approved_count}",
            inline=True
        )
    except Exception as e:
        embed.add_field(
            name="📊 Database",
            value=f"❌ Error: {str(e)[:50]}",
            inline=True
        )
    
    # LinkedIn API
    linkedin_status = "✅ Connected" if publisher.test_connection() else "❌ Disconnected"
    embed.add_field(
        name="🔗 LinkedIn API",
        value=linkedin_status,
        inline=True
    )
    
    # Channels
    approval_status = "✅ Found" if linkedin_bot.approval_channel else "❌ Not Found"
    embed.add_field(
        name="📢 Approval Channel",
        value=approval_status,
        inline=True
    )
    
    await ctx.send(embed=embed)

@bot.command(name='test_post')
async def test_post_command(ctx, *, content="This is a test LinkedIn post from the Discord bot!"):
    """Create a test post for approval"""
    if ctx.author.id not in Config.ADMIN_USER_IDS and Config.ADMIN_USER_IDS:
        await ctx.send("❌ You don't have permission to create test posts.")
        return
    
    try:
        # Create test post
        post = db.create_post(
            content=content,
            industry="Technology",
            audience="Tech professionals",
            golden_threads="Test post"
        )
        
        await ctx.send(f"✅ Created test post with ID: {post.draft_id}")
        
    except Exception as e:
        await ctx.send(f"❌ Error creating test post: {e}")

# Command sync task - runs after bot is ready and commands are defined
@tasks.loop(count=1)  # Run only once
async def sync_commands_after_ready():
    """Sync commands after bot is ready and commands are defined"""
    try:
        await bot.wait_until_ready()
        await asyncio.sleep(2)  # Wait a bit for full initialization
        
        logger.info("🔄 Starting post-initialization command sync...")
        
        # Debug: Show what commands are in the tree
        all_commands = [cmd.name for cmd in bot.tree.get_commands()]
        logger.info(f"📋 Commands in tree before sync: {all_commands}")
        
        # Prioritize guild sync for immediate availability
        if hasattr(Config, 'DISCORD_GUILD_ID') and Config.DISCORD_GUILD_ID:
            guild = discord.Object(id=int(Config.DISCORD_GUILD_ID))
            # Copy global commands to guild for immediate availability
            for command in bot.tree.get_commands():
                bot.tree.add_command(command, guild=guild)
            synced_guild = await bot.tree.sync(guild=guild)
            logger.info(f"🎯 Synced {len(synced_guild)} slash commands to guild: {[cmd.name for cmd in synced_guild]}")
        
        # Also sync globally (takes up to 1 hour to propagate)
        synced_global = await bot.tree.sync()
        logger.info(f"🌍 Synced {len(synced_global)} global slash commands: {[cmd.name for cmd in synced_global]}")
        
        logger.info(f"⚡ Post-initialization command sync complete!")
        
    except Exception as e:
        logger.error(f"❌ Failed to sync commands after ready: {e}")

if __name__ == "__main__":
    # Check enhanced logging dependencies first
    check_dependencies()
    
    # Show startup banner even before validation for immediate visual feedback
    print(f"\n{Fore.MAGENTA}{'=' * 88}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}🤖 INITIALIZING DISCORD LINKEDIN BOT SYSTEM 🤖{Style.RESET_ALL}".center(88))
    print(f"{Fore.MAGENTA}{'=' * 88}{Style.RESET_ALL}\n")
    
    # Validate configuration
    try:
        logger.info("🔧 Validating system configuration...")
        Config.validate()
        logger.system_health("Configuration", "healthy", {"status": "validated"})
        
        # Create database tables
        logger.info("🗃️  Initializing database tables...")
        db.create_tables()
        logger.system_health("Database", "healthy", {"tables": "initialized"})
        
        # Pre-flight checks complete
        logger.info("✅ All pre-flight checks completed successfully")
        
        
        # Start the bot (this will trigger the on_ready event with the full banner)
        logger.info("🚀 Launching Discord bot connection...")
        bot.run(Config.DISCORD_TOKEN)
        
    except ValueError as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        print(f"\n{Fore.RED}💀 STARTUP FAILED - Fix configuration and try again{Style.RESET_ALL}")
    except KeyboardInterrupt:
        logger.info("👋 Bot shutdown requested by user")
        print(f"\n{Fore.YELLOW}🛑 Discord LinkedIn Bot shutdown complete{Style.RESET_ALL}")
    except Exception as e:
        logger.error(f"❌ Critical error during startup: {e}")
        print(f"\n{Fore.RED}💥 FATAL ERROR - Check logs and configuration{Style.RESET_ALL}")