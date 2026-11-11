from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    HONEYPOT_BASE_URL: str = "https://agentic-honeypot-sb7i.onrender.com"
    HONEYPOT_API_KEY: Optional[str] = None
    
    LLM_PROVIDER: str = "mock"  # "gemini", "openai", "mock"
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gemini-1.5-flash"
    LLM_TEMPERATURE: float = 0.7
    
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "honeypot_simulator"
    
    MAX_CONVERSATION_TURNS: int = 15
    HONEYPOT_TIMEOUT_SECONDS: int = 90
    HONEYPOT_MAX_RETRIES: int = 2
    
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
