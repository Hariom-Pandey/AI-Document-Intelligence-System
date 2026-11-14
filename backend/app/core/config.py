import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BASE_DIR.parent
DATA_DIR = ROOT_DIR / "data"

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Document Intelligence System"
    API_V1_STR: str = "/api"
    
    # Storage & Database
    DATA_DIR: Path = DATA_DIR
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    INDEX_DIR: Path = DATA_DIR / "indexes"
    REDACTED_DIR: Path = DATA_DIR / "redacted"
    DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'app.db'}"
    
    # NLP & Embedding Models
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    SUMMARIZATION_MODEL_NAME: str = "sshleifer/distilbart-cnn-12-6"
    QA_MODEL_NAME: str = "deepset/roberta-base-squad2"
    NLI_MODEL_NAME: str = "cross-encoder/nli-deberta-v3-base"
    
    # Chunking & Retrieval parameters
    CHUNK_SIZE: int = 700
    CHUNK_OVERLAP: int = 100
    TOP_K_CHUNKS: int = 4
    
    # Cross-Document Consistency & Contradiction Parameters
    CONSISTENCY_SIMILARITY_THRESHOLD: float = 0.45
    CONTRADICTION_CONFIDENCE_THRESHOLD: float = 0.60
    CONSISTENCY_BATCH_SIZE: int = 16
    
    # Allowed Extensions
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".txt"}
    MAX_FILE_SIZE_MB: int = 50
    
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.INDEX_DIR.mkdir(parents=True, exist_ok=True)
settings.REDACTED_DIR.mkdir(parents=True, exist_ok=True)
