import os
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import List

load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    APP_NAME: str = "Crime Analysis API"
    API_PREFIX: str = "/api"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = Field(default=os.getenv("DATABASE_URL", "sqlite:///./crime-analysis.db"))
    
    # Authentication
    SECRET_KEY: str = Field(default=os.getenv("SECRET_KEY", "supersecretkey"))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Application URLs
    FRONTEND_URL: str = Field(default=os.getenv("FRONTEND_URL", "http://localhost:3000"))
    
    # JWT
    JWT_SECRET_KEY: str = Field(default=os.getenv("JWT_SECRET_KEY", "supersecretjwtkey"))
    JWT_ALGORITHM: str = "HS256"
    
    class Config:
        case_sensitive = True

settings = Settings()