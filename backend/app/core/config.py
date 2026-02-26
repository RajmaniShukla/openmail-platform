"""
OpenMail Platform - Configuration Settings
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    APP_NAME: str = "OpenMail"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://openmail:openmail@localhost:5432/openmail"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Email Server
    MAIL_SERVER_HOSTNAME: str = "mail.example.com"
    POSTFIX_HOST: str = "localhost"
    POSTFIX_PORT: int = 25
    
    # MinIO / S3
    S3_ENDPOINT: str = "localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_ATTACHMENTS: str = "attachments"
    S3_BUCKET_EMAILS: str = "emails"
    S3_USE_SSL: bool = False
    
    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_INDEX_PREFIX: str = "openmail"
    
    # Spam
    SPAMASSASSIN_HOST: str = "localhost"
    SPAMASSASSIN_PORT: int = 783
    SPAM_THRESHOLD: float = 5.0
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AUTH: str = "10/minute"
    RATE_LIMIT_EMAIL_SEND: str = "100/hour"
    RATE_LIMIT_DEFAULT: str = "1000/minute"
    
    # Security
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_ATTACHMENT_TYPES: List[str] = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "image/jpeg",
        "image/png",
        "image/gif",
        "text/plain",
        "text/csv",
    ]
    
    # Quotas
    DEFAULT_MAILBOX_QUOTA_GB: int = 5
    MAX_RECIPIENTS_PER_EMAIL: int = 100
    MAX_ATTACHMENTS_PER_EMAIL: int = 20
    
    # DKIM
    DKIM_SELECTOR: str = "mail"
    DKIM_PRIVATE_KEY_PATH: str = "/etc/opendkim/keys"
    
    # Domain
    DOMAIN: str = "localhost"
    
    # SMTP Settings (for sending)
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_TLS: bool = True
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
