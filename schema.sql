-- LinkedIn Post Generator Database Schema
-- PostgreSQL database schema for managing LinkedIn posts and approval workflow

-- Create database (run this manually if needed)
-- CREATE DATABASE linkedin_posts;

-- Main table for storing LinkedIn posts
CREATE TABLE IF NOT EXISTS linkedin_posts (
    id SERIAL PRIMARY KEY,
    
    -- Post content
    content TEXT NOT NULL,
    image_url VARCHAR(512),
    image_prompt TEXT,
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    CHECK (status IN ('pending', 'approved', 'rejected', 'published', 'failed')),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    approved_at TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE,
    rejected_at TIMESTAMP WITH TIME ZONE,
    
    -- Approval tracking
    approved_by VARCHAR(100),
    rejection_reason TEXT,
    
    -- Discord integration
    discord_message_id VARCHAR(20),
    discord_channel_id VARCHAR(20),
    
    -- Post metadata
    industry VARCHAR(100),
    audience VARCHAR(200),
    golden_threads TEXT,
    
    -- LinkedIn integration
    linkedin_post_id VARCHAR(50),
    linkedin_url VARCHAR(512),
    
    -- Error handling
    last_error TEXT,
    retry_count INTEGER DEFAULT 0
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_linkedin_posts_status ON linkedin_posts(status);
CREATE INDEX IF NOT EXISTS idx_linkedin_posts_created_at ON linkedin_posts(created_at);
CREATE INDEX IF NOT EXISTS idx_linkedin_posts_discord_message ON linkedin_posts(discord_message_id);
CREATE INDEX IF NOT EXISTS idx_linkedin_posts_linkedin_id ON linkedin_posts(linkedin_post_id);

-- Create a view for pending posts that need Discord notification
CREATE OR REPLACE VIEW pending_posts_for_notification AS
SELECT * FROM linkedin_posts 
WHERE status = 'pending' 
AND discord_message_id IS NULL
ORDER BY created_at ASC;

-- Create a view for approved posts ready for publishing
CREATE OR REPLACE VIEW approved_posts_for_publishing AS
SELECT * FROM linkedin_posts 
WHERE status = 'approved' 
AND linkedin_post_id IS NULL
ORDER BY approved_at ASC;

-- Sample data insertion function
CREATE OR REPLACE FUNCTION insert_sample_post(
    p_content TEXT,
    p_industry VARCHAR(100) DEFAULT NULL,
    p_audience VARCHAR(200) DEFAULT NULL,
    p_golden_threads TEXT DEFAULT NULL,
    p_image_url VARCHAR(512) DEFAULT NULL
) RETURNS INTEGER AS $$
DECLARE
    new_post_id INTEGER;
BEGIN
    INSERT INTO linkedin_posts (content, industry, audience, golden_threads, image_url)
    VALUES (p_content, p_industry, p_audience, p_golden_threads, p_image_url)
    RETURNING id INTO new_post_id;
    
    RETURN new_post_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get post statistics
CREATE OR REPLACE FUNCTION get_post_statistics()
RETURNS TABLE(
    total_posts INTEGER,
    pending_posts INTEGER,
    approved_posts INTEGER,
    published_posts INTEGER,
    rejected_posts INTEGER,
    failed_posts INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_posts,
        COUNT(CASE WHEN status = 'pending' THEN 1 END)::INTEGER as pending_posts,
        COUNT(CASE WHEN status = 'approved' THEN 1 END)::INTEGER as approved_posts,
        COUNT(CASE WHEN status = 'published' THEN 1 END)::INTEGER as published_posts,
        COUNT(CASE WHEN status = 'rejected' THEN 1 END)::INTEGER as rejected_posts,
        COUNT(CASE WHEN status = 'failed' THEN 1 END)::INTEGER as failed_posts
    FROM linkedin_posts;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update timestamps
CREATE OR REPLACE FUNCTION update_post_timestamps()
RETURNS TRIGGER AS $$
BEGIN
    -- Update approved_at when status changes to approved
    IF NEW.status = 'approved' AND OLD.status != 'approved' THEN
        NEW.approved_at = CURRENT_TIMESTAMP;
    END IF;
    
    -- Update published_at when status changes to published
    IF NEW.status = 'published' AND OLD.status != 'published' THEN
        NEW.published_at = CURRENT_TIMESTAMP;
    END IF;
    
    -- Update rejected_at when status changes to rejected
    IF NEW.status = 'rejected' AND OLD.status != 'rejected' THEN
        NEW.rejected_at = CURRENT_TIMESTAMP;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS update_post_timestamps_trigger ON linkedin_posts;
CREATE TRIGGER update_post_timestamps_trigger
    BEFORE UPDATE ON linkedin_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_post_timestamps();

-- Function to clean up old posts (optional maintenance)
CREATE OR REPLACE FUNCTION cleanup_old_posts(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM linkedin_posts 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * days_to_keep
    AND status IN ('published', 'rejected');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Sample data for testing (uncomment to insert test data)
/*
-- Insert sample posts
SELECT insert_sample_post(
    'Just had an amazing breakthrough in our data analysis project! The insights we uncovered will reshape how we approach customer segmentation. Sometimes the best discoveries come from asking the right questions rather than having all the answers. #DataScience #Analytics',
    'Data Science',
    'Data analysts and business professionals',
    'Data Analysis Value: Data needs analysis to become an asset'
);

SELECT insert_sample_post(
    'Building strong teams isn''t just about hiring talented individuals - it''s about creating an environment where those individuals can thrive together. Today our team solved a complex problem that none of us could have tackled alone. Collaboration truly is our greatest asset.',
    'Management',
    'Team leaders and managers',
    'Community Asset Management: Community is critical to asset management'
);

SELECT insert_sample_post(
    'The future of work isn''t just remote or hybrid - it''s about giving people the flexibility to do their best work wherever that happens to be. What matters most is the output, not the office.',
    'Future of Work',
    'HR professionals and business leaders',
    null
);
*/

-- Display schema information
COMMENT ON TABLE linkedin_posts IS 'Main table for storing LinkedIn posts and tracking their approval workflow';
COMMENT ON COLUMN linkedin_posts.status IS 'Current status: pending, approved, rejected, published, failed';
COMMENT ON COLUMN linkedin_posts.discord_message_id IS 'ID of the Discord message for approval workflow';
COMMENT ON COLUMN linkedin_posts.linkedin_post_id IS 'LinkedIn post ID after successful publishing';
COMMENT ON COLUMN linkedin_posts.golden_threads IS 'Selected content themes for consistency';
COMMENT ON COLUMN linkedin_posts.retry_count IS 'Number of publishing retry attempts';