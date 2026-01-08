from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # App
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = Field(..., description="JWT Secret Key is missing!")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = Field(..., description="Database URL is missing!")

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"
        case_sensitive = True

# Initialize settings
try:
    settings = Settings()
except Exception as e:
    print("❌ CRITICAL: Missing Environment Variables")
    raise e