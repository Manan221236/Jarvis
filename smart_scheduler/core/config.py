from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./smart_scheduler.db"
    
    # Security
    secret_key: str = "your-super-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # OpenAI
    openai_api_key: Optional[str] = None
    
    # Application
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    
    class Config:
        env_file = ".env"

# Fix: Remove the .env suffix that was causing the error
settings = Settings()