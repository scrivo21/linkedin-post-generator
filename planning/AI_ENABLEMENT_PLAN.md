# AI Enablement Integration Plan - Complete Pipeline Replacement

**Associated Feature Branch:** `feature/ai-enablement`

## Architecture Overview
Replace the n8n webhook entirely with a direct AI pipeline:
1. Discord form submission → FormSubmission table
2. Process form data through Anthropic Claude API for post generation
3. Extract image prompt from Claude's response
4. Generate image via OpenAI DALL-E 3 API  
5. Store content + image in PostgreSQL as LinkedInDraft
6. Send mockup to Discord for approval
7. Schedule and publish to LinkedIn at optimal time

## Phase 1: Database Schema Updates

**Update `linkedin_drafts` table:**
```sql
ALTER TABLE linkedin_drafts ADD COLUMN IF NOT EXISTS ai_generated BOOLEAN DEFAULT FALSE;
ALTER TABLE linkedin_drafts ADD COLUMN IF NOT EXISTS anthropic_prompt TEXT;
ALTER TABLE linkedin_drafts ADD COLUMN IF NOT EXISTS anthropic_response JSONB;
ALTER TABLE linkedin_drafts ADD COLUMN IF NOT EXISTS dalle_prompt TEXT;
ALTER TABLE linkedin_drafts ADD COLUMN IF NOT EXISTS dalle_response JSONB;
ALTER TABLE linkedin_drafts ADD COLUMN IF NOT EXISTS scheduled_publish_time TIMESTAMP WITH TIME ZONE;
ALTER TABLE linkedin_drafts ADD COLUMN IF NOT EXISTS generation_metadata JSONB;
```

**Update `form_submissions` table:**
```sql
ALTER TABLE form_submissions ADD COLUMN IF NOT EXISTS ai_processing_status VARCHAR(50);
ALTER TABLE form_submissions ADD COLUMN IF NOT EXISTS ai_processed_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE form_submissions ADD COLUMN IF NOT EXISTS ai_error_message TEXT;
```

## Phase 2: Core AI Service Module (`ai_services.py`)

**AnthropicService class:**
```python
class AnthropicService:
    def __init__(self):
        self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        
    async def generate_linkedin_post(self, form_data):
        # Build comprehensive prompt from form data
        prompt = self.build_prompt(form_data)
        
        # Call Claude API with structured format
        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            temperature=0.7,
            system="You are an expert LinkedIn content creator...",
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse response to extract post and image prompt
        return self.parse_response(response)
```

**OpenAIService class:**
```python
class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
    async def generate_image(self, image_prompt):
        response = await self.client.images.generate(
            model="dall-e-3",
            prompt=image_prompt,
            size="1792x1024",  # LinkedIn optimal size
            quality="hd",
            style="natural"
        )
        return response.data[0].url
```

## Phase 3: Enhanced Post Processor (`ai_processor.py`)

**AIPostProcessor class:**
```python
class AIPostProcessor:
    async def process_form_submission(self, submission):
        try:
            # 1. Update status to processing
            db.update_form_submission_status(
                submission.submission_id, 
                FormSubmissionStatus.PROCESSING,
                ai_processing_status='generating_content'
            )
            
            # 2. Generate post with Claude
            anthropic = AnthropicService()
            post_data = await anthropic.generate_linkedin_post(submission.form_data)
            
            # 3. Generate image with DALL-E
            openai = OpenAIService()
            image_url = await openai.generate_image(post_data['image_prompt'])
            
            # 4. Create LinkedInDraft with scheduled time
            scheduled_time = self.calculate_optimal_posting_time()
            draft = db.create_post(
                content=post_data['content'],
                image_url=image_url,
                dalle_prompt=post_data['image_prompt'],
                anthropic_response=post_data['full_response'],
                scheduled_publish_time=scheduled_time,
                ai_generated=True,
                draft_id=submission.submission_id,
                **submission.form_data
            )
            
            # 5. Send to Discord for approval
            await self.send_approval_mockup(draft)
            
            # 6. Update submission status
            db.update_form_submission_status(
                submission.submission_id,
                FormSubmissionStatus.COMPLETED,
                draft_id=draft.draft_id
            )
            
        except Exception as e:
            # Handle errors
            db.update_form_submission_status(
                submission.submission_id,
                FormSubmissionStatus.FAILED,
                ai_error_message=str(e)
            )
```

## Phase 4: LinkedIn Scheduler Module (`scheduler.py`)

**LinkedInScheduler class:**
```python
class LinkedInScheduler:
    def __init__(self):
        self.optimal_times = {
            'monday': ['08:00', '12:00', '17:00'],
            'tuesday': ['09:00', '13:00', '18:00'],
            'wednesday': ['08:30', '12:30', '17:30'],
            'thursday': ['09:00', '14:00', '18:00'],
            'friday': ['08:00', '11:00', '15:00']
        }
    
    async def schedule_approved_posts(self):
        """Check for approved posts and publish at scheduled time"""
        approved_posts = db.get_approved_posts()
        current_time = datetime.now()
        
        for post in approved_posts:
            if post.scheduled_publish_time <= current_time:
                await self.publish_to_linkedin(post)
    
    def calculate_next_slot(self, industry, audience):
        """Calculate optimal posting time based on industry/audience"""
        # Algorithm to determine best time slot
        return next_optimal_datetime
```

## Phase 5: Prompt Engineering System (`prompt_templates.py`)

**LinkedInPromptBuilder class:**
```python
class LinkedInPromptBuilder:
    BASE_TEMPLATE = """
    Create a LinkedIn post for the following context:
    
    Industry: {industry}
    Target Audience: {audience}
    Situation/Challenge: {situation}
    Key Insight: {key_insight}
    Personal Anecdote: {anecdote}
    Golden Threads to Include: {golden_threads}
    
    Requirements:
    1. Write in Australian English with natural, conversational tone
    2. First 3 lines must be compelling hook (max 200 chars total)
    3. Include ONE deliberate minor spelling error for authenticity
    4. No hashtags, emojis, or explicit CTAs
    5. Focus on storytelling and value delivery
    
    After the post, provide an image generation prompt in this exact format:
    
    IMAGE_PROMPT: [Professional LinkedIn image description that complements the post, focusing on abstract business concepts, modern workspace, or relevant industry imagery]
    
    Generate the post now:
    """
    
    def build_prompt(self, form_data):
        # Customize prompt based on form data
        return self.BASE_TEMPLATE.format(**form_data)
```

## Phase 6: Discord Integration Updates

**Update Discord Bot Commands:**
```python
@bot.command(name='process_pending')
async def process_pending_submissions(ctx):
    """Manually trigger AI processing of pending submissions"""
    processor = AIPostProcessor()
    pending = db.get_pending_form_submissions()
    
    for submission in pending:
        await processor.process_form_submission(submission)
    
    await ctx.send(f"✅ Processed {len(pending)} submissions")

@bot.command(name='schedule_status')
async def check_schedule(ctx):
    """Show scheduled posts and their publish times"""
    scheduled = db.get_scheduled_posts()
    # Display scheduled posts in embed
```

## Phase 7: Remove n8n Dependencies

**Files to Update:**
1. **`discord_linkedin_bot.py`:**
   - Remove `send_to_n8n_webhook()` method
   - Replace with `process_with_ai()` method
   - Update form submission handler to trigger AI processing

2. **`config.py`:**
   - Remove `N8N_WEBHOOK_URL`
   - Add AI service configurations:
   ```python
   ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
   OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
   AI_PROCESSING_ENABLED = os.getenv('AI_PROCESSING_ENABLED', 'true')
   POST_SCHEDULING_ENABLED = os.getenv('POST_SCHEDULING_ENABLED', 'true')
   ```

## Phase 8: Background Tasks

**Add to `discord_linkedin_bot.py`:**
```python
@tasks.loop(minutes=1)
async def process_ai_queue():
    """Process pending form submissions through AI pipeline"""
    if Config.AI_PROCESSING_ENABLED:
        processor = AIPostProcessor()
        pending = db.get_pending_form_submissions()
        
        for submission in pending[:5]:  # Process 5 at a time
            await processor.process_form_submission(submission)

@tasks.loop(minutes=5)
async def publish_scheduled_posts():
    """Publish approved posts at their scheduled times"""
    if Config.POST_SCHEDULING_ENABLED:
        scheduler = LinkedInScheduler()
        await scheduler.schedule_approved_posts()
```

## Phase 9: Testing & Monitoring

**Create `test_ai_pipeline.py`:**
```python
async def test_full_pipeline():
    # Test form submission → AI generation → approval → scheduling
    test_form_data = {
        'industry': 'Technology',
        'audience': 'CTOs and tech leaders',
        'situation': 'Dealing with technical debt',
        'key_insight': 'Incremental refactoring beats big rewrites',
        'anecdote': 'Last sprint we reduced load time by 40%'
    }
    
    # Test each component
    await test_anthropic_generation(test_form_data)
    await test_dalle_generation()
    await test_scheduling_logic()
    await test_linkedin_publishing()
```

## Phase 10: Implementation Order

1. **Day 1-2:** Set up AI service classes and API integrations
2. **Day 3:** Implement prompt templates and response parsing
3. **Day 4:** Update database schema and models
4. **Day 5:** Integrate AI processor with form submissions
5. **Day 6:** Implement scheduling system
6. **Day 7:** Remove n8n webhook, add Discord commands
7. **Day 8:** Testing and error handling
8. **Day 9:** Deploy and monitor

## New File Structure:
```
linkedin-post-generator/
├── ai_services.py          # Anthropic & OpenAI integrations
├── ai_processor.py          # Form → AI → Database pipeline
├── prompt_templates.py      # Prompt engineering
├── scheduler.py            # LinkedIn posting scheduler
├── test_ai_pipeline.py     # Comprehensive testing
└── migrations/
    └── add_ai_fields.sql   # Database migrations
```

## Benefits of This Approach:
- **No external dependencies:** Removes n8n webhook requirement
- **Full control:** Direct API integration for better error handling
- **Intelligent scheduling:** Posts at optimal times for engagement
- **Cost efficient:** Only processes when needed
- **Scalable:** Can handle multiple submissions in parallel
- **Auditable:** Complete tracking of AI generation process

## Required Environment Variables:
```bash
# AI Service Configuration
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
OPENAI_MODEL=dall-e-3
AI_PROCESSING_ENABLED=true
POST_SCHEDULING_ENABLED=true
AI_RETRY_ATTEMPTS=3
AI_TIMEOUT_SECONDS=30

# Remove these n8n variables:
# N8N_WEBHOOK_URL (no longer needed)
```

## Required Package Updates:
```bash
pip install anthropic openai
```

This plan creates a fully integrated AI pipeline that replaces the n8n webhook entirely while adding intelligent scheduling for maximum LinkedIn engagement.