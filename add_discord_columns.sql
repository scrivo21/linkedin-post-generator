-- Add Discord integration columns to existing linkedin_drafts table
-- Run this to extend your existing table with Discord bot functionality

-- Add Discord integration columns
ALTER TABLE linkedin_drafts 
ADD COLUMN IF NOT EXISTS discord_message_id TEXT,
ADD COLUMN IF NOT EXISTS discord_channel_id TEXT,
ADD COLUMN IF NOT EXISTS discord_approver TEXT;

-- Add metadata columns for better content management
ALTER TABLE linkedin_drafts 
ADD COLUMN IF NOT EXISTS industry TEXT,
ADD COLUMN IF NOT EXISTS audience TEXT,
ADD COLUMN IF NOT EXISTS golden_threads TEXT;

-- Add error tracking columns
ALTER TABLE linkedin_drafts 
ADD COLUMN IF NOT EXISTS last_error TEXT,
ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;

-- Create indexes for better Discord bot performance
CREATE INDEX IF NOT EXISTS idx_drafts_discord_message ON linkedin_drafts(discord_message_id);
CREATE INDEX IF NOT EXISTS idx_drafts_status_discord ON linkedin_drafts(status) WHERE discord_message_id IS NULL;

-- Create a view for pending posts that need Discord notification (compatible with existing status values)
CREATE OR REPLACE VIEW pending_posts_for_discord AS
SELECT * FROM linkedin_drafts 
WHERE status = 'pending' 
AND discord_message_id IS NULL
ORDER BY created_at ASC;

-- Create a view for approved posts ready for publishing
CREATE OR REPLACE VIEW approved_posts_for_publishing AS
SELECT * FROM linkedin_drafts 
WHERE status = 'approved_for_socials' 
AND linkedin_post_id IS NULL
ORDER BY approved_at ASC;

-- Add comments for new columns
COMMENT ON COLUMN linkedin_drafts.discord_message_id IS 'Discord message ID for approval workflow tracking';
COMMENT ON COLUMN linkedin_drafts.discord_channel_id IS 'Discord channel ID where approval message was sent';
COMMENT ON COLUMN linkedin_drafts.discord_approver IS 'Discord username of person who approved/declined';
COMMENT ON COLUMN linkedin_drafts.industry IS 'Industry/topic category for content';
COMMENT ON COLUMN linkedin_drafts.audience IS 'Target audience for the post';
COMMENT ON COLUMN linkedin_drafts.golden_threads IS 'Selected content themes (JSON)';
COMMENT ON COLUMN linkedin_drafts.last_error IS 'Last error message if publishing failed';
COMMENT ON COLUMN linkedin_drafts.retry_count IS 'Number of retry attempts for failed posts';

-- Show current table structure
\d linkedin_drafts