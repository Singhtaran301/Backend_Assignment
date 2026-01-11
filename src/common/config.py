from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 1. Database
    DATABASE_URL: str
    
    # 2. Environment (Dev/Prod) - THIS WAS MISSING
    ENVIRONMENT: str = "development"

    # 3. Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    
    # 4. Expiration Times
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        env_file = ".env"
        extra = "ignore" 

settings = Settings()