from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # PostgreSQL
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str

    # MongoDB
    MONGO_URL: str
    MONGO_DB: str

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    ALGORITHM : str
    SECRET_KEY : str
    REFRESH_SECRET_KEY : str
    
    class Config:
        env_file = ".env"
        extra = "allow"
        
@lru_cache
def get_settings():
    return Settings()
