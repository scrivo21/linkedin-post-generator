import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Discord Configuration
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    DISCORD_GUILD_ID = os.getenv('DISCORD_GUILD_ID')
    DISCORD_APPROVAL_CHANNEL_ID = int(os.getenv('DISCORD_APPROVAL_CHANNEL_ID', 0))
    DISCORD_NOTIFICATION_CHANNEL_ID = int(os.getenv('DISCORD_NOTIFICATION_CHANNEL_ID', 0))
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://sasreliability@localhost/sas_social')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'sas_social')
    DB_USER = os.getenv('DB_USER', 'sasreliability')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    # LinkedIn Configuration
    LINKEDIN_CLIENT_ID = os.getenv('LINKEDIN_CLIENT_ID')
    LINKEDIN_CLIENT_SECRET = os.getenv('LINKEDIN_CLIENT_SECRET')
    LINKEDIN_ACCESS_TOKEN = os.getenv('LINKEDIN_ACCESS_TOKEN')
    LINKEDIN_PERSON_ID = os.getenv('LINKEDIN_PERSON_ID')
    
    # Webhook Configuration (for n8n integration)
    N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL')
    
    # Monitoring Configuration
    POLL_INTERVAL = int(os.getenv('POLL_INTERVAL', '30'))  # seconds
    
    # Bot Configuration
    BOT_PREFIX = os.getenv('BOT_PREFIX', '!')
    ADMIN_USER_IDS = [int(id.strip()) for id in os.getenv('ADMIN_USER_IDS', '').split(',') if id.strip()]
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_vars = [
            'DISCORD_TOKEN',
            'DISCORD_APPROVAL_CHANNEL_ID',
            'DATABASE_URL'
        ]
        
        missing = []
        for var in required_vars:
            if not getattr(cls, var):
                missing.append(var)
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True