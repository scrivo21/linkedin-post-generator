from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from enum import Enum
import datetime
import uuid
from config import Config

Base = declarative_base()

class PostStatus(Enum):
    PENDING = "pending"
    APPROVED_FOR_SOCIALS = "approved_for_socials"  # Matches your existing DB
    DECLINED = "declined"  # Matches your existing DB
    POSTED = "posted"  # Matches your existing DB

class LinkedInDraft(Base):
    __tablename__ = 'linkedin_drafts'
    
    # Existing fields from your database
    draft_id = Column(Text, primary_key=True)  # Your existing primary key
    status = Column(Text, nullable=False)
    post = Column(Text)  # Post content
    image_base64 = Column(Text)
    image_mime = Column(Text)
    source = Column(Text)
    token = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    approved_at = Column(DateTime(timezone=True))
    posted_at = Column(DateTime(timezone=True))
    linkedin_post_id = Column(Text)
    approver_email = Column(Text)
    post_path = Column(Text)
    image_path = Column(Text)
    
    # New fields for Discord integration (we'll add these as nullable)
    discord_message_id = Column(Text)  # To track approval messages
    discord_channel_id = Column(Text)
    discord_approver = Column(Text)  # Discord username
    
    # Additional metadata fields (nullable to not break existing data)
    industry = Column(Text)
    audience = Column(Text)
    golden_threads = Column(Text)  # JSON string of selected themes
    last_error = Column(Text)
    retry_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<LinkedInDraft(draft_id={self.draft_id}, status={self.status}, created_at={self.created_at})>"
    
    @property
    def content(self):
        """Get content from post field for compatibility"""
        return self.post
    
    @property
    def id(self):
        """Get ID from draft_id for compatibility"""
        return self.draft_id
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.draft_id,
            'content': self.post,
            'image_base64': self.image_base64,
            'image_path': self.image_path,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'posted_at': self.posted_at.isoformat() if self.posted_at else None,
            'approver_email': self.approver_email,
            'discord_approver': self.discord_approver,
            'industry': self.industry,
            'audience': self.audience,
            'golden_threads': self.golden_threads,
            'linkedin_post_id': self.linkedin_post_id,
            'source': self.source
        }

class FormSubmissionStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"  
    COMPLETED = "completed"
    FAILED = "failed"

class FormSubmission(Base):
    __tablename__ = 'form_submissions'
    
    submission_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    form_data = Column(JSONB, nullable=False)
    source = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    draft_id = Column(Text, ForeignKey('linkedin_drafts.draft_id'))
    status = Column(String(20), default='pending')
    error_message = Column(Text)
    
    # Relationship to LinkedInDraft
    linkedin_draft = relationship("LinkedInDraft", backref="form_submission")
    
    def __repr__(self):
        return f"<FormSubmission(submission_id={self.submission_id}, status={self.status}, created_at={self.created_at})>"
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'submission_id': str(self.submission_id),
            'form_data': self.form_data,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'draft_id': self.draft_id,
            'status': self.status,
            'error_message': self.error_message
        }

class Database:
    def __init__(self):
        self.engine = create_engine(Config.DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
    
    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Get a new database session"""
        return self.Session()
    
    def get_pending_posts(self):
        """Get all pending posts that haven't been sent to Discord"""
        session = self.get_session()
        try:
            return session.query(LinkedInDraft).filter(
                LinkedInDraft.status == PostStatus.PENDING.value,
                LinkedInDraft.discord_message_id.is_(None)
            ).all()
        finally:
            session.close()
    
    def get_approved_posts(self):
        """Get all approved posts that haven't been published"""
        session = self.get_session()
        try:
            return session.query(LinkedInDraft).filter(
                LinkedInDraft.status == PostStatus.APPROVED_FOR_SOCIALS.value,
                LinkedInDraft.linkedin_post_id.is_(None)
            ).all()
        finally:
            session.close()
    
    def update_post_status(self, draft_id, status, **kwargs):
        """Update post status and related fields"""
        session = self.get_session()
        try:
            post = session.query(LinkedInDraft).filter(LinkedInDraft.draft_id == draft_id).first()
            if post:
                post.status = status.value if isinstance(status, PostStatus) else status
                
                # Update timestamp based on status
                if status == PostStatus.APPROVED_FOR_SOCIALS:
                    post.approved_at = datetime.datetime.now()
                elif status == PostStatus.POSTED:
                    post.posted_at = datetime.datetime.now()
                
                # Update additional fields
                for key, value in kwargs.items():
                    if hasattr(post, key):
                        setattr(post, key, value)
                
                session.commit()
                return post
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def create_post(self, content, **kwargs):
        """Create a new LinkedIn draft record"""
        import uuid
        session = self.get_session()
        try:
            # Generate a unique draft_id if not provided
            draft_id = kwargs.pop('draft_id', str(uuid.uuid4()))
            
            # Set default source if not provided
            if 'source' not in kwargs:
                kwargs['source'] = 'discord-bot'
            
            post = LinkedInDraft(
                draft_id=draft_id,
                post=content,
                status=PostStatus.PENDING.value,
                **kwargs
            )
            session.add(post)
            session.commit()
            session.refresh(post)
            return post
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def create_form_submission(self, form_data, source):
        """Create a new form submission record"""
        session = self.get_session()
        try:
            submission = FormSubmission(
                form_data=form_data,
                source=source,
                status=FormSubmissionStatus.PENDING.value
            )
            session.add(submission)
            session.commit()
            session.refresh(submission)
            return submission
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_form_submission_status(self, submission_id, status, **kwargs):
        """Update form submission status and related fields"""
        session = self.get_session()
        try:
            submission = session.query(FormSubmission).filter(
                FormSubmission.submission_id == submission_id
            ).first()
            
            if submission:
                submission.status = status.value if isinstance(status, FormSubmissionStatus) else status
                
                # Update timestamp based on status
                if status in [FormSubmissionStatus.COMPLETED, FormSubmissionStatus.FAILED]:
                    submission.processed_at = datetime.datetime.now()
                
                # Update additional fields
                for key, value in kwargs.items():
                    if hasattr(submission, key):
                        setattr(submission, key, value)
                
                session.commit()
                return submission
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_pending_form_submissions(self):
        """Get all pending form submissions"""
        session = self.get_session()
        try:
            return session.query(FormSubmission).filter(
                FormSubmission.status == FormSubmissionStatus.PENDING.value
            ).all()
        finally:
            session.close()

# Global database instance
db = Database()