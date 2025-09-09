"""
Configuration management for the toytoons scraper.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the scraper."""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_ROOT = PROJECT_ROOT / "data"
    RAW_DATA_DIR = DATA_ROOT / "raw"
    PROCESSED_DATA_DIR = DATA_ROOT / "processed"
    
    # Scraping settings
    USER_AGENT = os.getenv("USER_AGENT", "toytoons-scraper/0.1")
    DELAY_MIN = float(os.getenv("DELAY_MIN", "0.8"))
    DELAY_MAX = float(os.getenv("DELAY_MAX", "2.0"))
    CONCURRENCY = int(os.getenv("CONCURRENCY", "2"))
    TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "30"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    
    # Summarization settings
    OLLAMA_MODEL: Optional[str] = os.getenv("OLLAMA_MODEL")
    SUMMARY_SENTENCES = int(os.getenv("SUMMARY_SENTENCES", "2"))
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "4000"))
    
    # File paths
    SEEDS_FILE = PROJECT_ROOT / "scraper" / "seeds.txt"
    DOCS_JSONL = PROCESSED_DATA_DIR / "docs.jsonl"
    LISTINGS_JSON = PROCESSED_DATA_DIR / "listings.json"
    LISTINGS_CSV = PROCESSED_DATA_DIR / "listings.csv"
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist."""
        cls.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def has_ollama(cls) -> bool:
        """Check if Ollama model is configured."""
        return cls.OLLAMA_MODEL is not None and cls.OLLAMA_MODEL.strip() != ""