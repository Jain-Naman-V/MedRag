import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field
from typing import Optional, ClassVar, Set
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "MedRAG"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # File upload settings
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS_STR: str = "pdf"  # Comma-separated string for env var
    UPLOAD_FOLDER: str = str(Path("./data/uploads").resolve())
    VECTOR_STORE_PATH: str = str(Path("./data/vector_store").resolve())  # Optional: Only needed if using RAG/vector store, not used in default flow
    
    # Model configuration
    model_config = ConfigDict(
        extra='ignore',  # Ignore extra fields
        case_sensitive=True,
        env_file=".env",
        env_file_encoding='utf-8'
    )
    
    @property
    def ALLOWED_EXTENSIONS(self) -> Set[str]:
        """Get allowed extensions as a set."""
        return set(ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS_STR.split(','))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # LLM and Embedding settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    HUGGINGFACEHUB_API_TOKEN: Optional[str] = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Chunking settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Configuration moved to model_config above

# Create settings instance
settings = Settings()

# Create necessary directories
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(settings.VECTOR_STORE_PATH, exist_ok=True)
