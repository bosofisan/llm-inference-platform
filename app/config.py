# app/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings and configuration"""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # Application Configuration
    APP_NAME: str = "LLM Inference Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Rate Limiting
    RATE_LIMIT: str = "10/minute"  # 10 requests per minute
    
    # API Configuration
    MAX_TOKENS: int = 500
    TEMPERATURE: float = 0.7
    
    def validate(self):
        """Validate critical configuration"""
        if not self.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set in environment variables")
        return True

# Create a global settings instance
settings = Settings()
settings.validate()
