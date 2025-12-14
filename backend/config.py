"""
Configuration management using Pydantic settings
"""

import json
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Keys
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = "us-east-1-aws"
    
    # Application
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Data Directories
    RAW_DATA_DIR: str = "./data/raw"
    MAX_DOCS: int = 1000  # Maximum number of documents to process in one ingestion run
    
    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./data/embeddings"
    CHROMA_DIR: str = "./data/embeddings"  # Alias for CHROMA_PERSIST_DIR for consistency
    
    # LLM Settings
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_TEMPERATURE: float = 0.3
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from string (comma-separated or JSON) to list"""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            # Try JSON first (for arrays like ["http://localhost:3000"])
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
            # Fall back to comma-separated string
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        # Default fallback
        return ["http://localhost:3000"]
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }


settings = Settings()

