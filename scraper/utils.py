"""
Utility functions for logging, hashing, and file operations.
"""

import hashlib
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from rich.console import Console
from rich.logging import RichHandler

console = Console()

def setup_logging(level: str = "INFO") -> logging.Logger:
    """Set up rich logging with console output."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )
    return logging.getLogger("toytoons")

def url_to_hash(url: str) -> str:
    """Convert URL to a short hash for filename purposes."""
    return hashlib.md5(url.encode()).hexdigest()[:12]

def get_domain(url: str) -> str:
    """Extract domain from URL."""
    return urlparse(url).netloc

def load_seeds(seeds_file: Path) -> List[str]:
    """Load seed URLs from file, filtering out comments and empty lines."""
    if not seeds_file.exists():
        return []
    
    seeds = []
    with open(seeds_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                seeds.append(line)
    return seeds

def save_json(data, filepath: Path, indent: Optional[int] = 2):
    """Save data as JSON file with pretty formatting."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False, default=str)

def load_json(filepath: Path):
    """Load data from JSON file."""
    if not filepath.exists():
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_jsonl(items: List[dict], filepath: Path):
    """Save items as JSON Lines file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        for item in items:
            json.dump(item, f, ensure_ascii=False, default=str)
            f.write('\n')

def load_jsonl(filepath: Path) -> List[dict]:
    """Load items from JSON Lines file."""
    if not filepath.exists():
        return []
    
    items = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items

def generate_timestamp() -> str:
    """Generate timestamp string for filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def clean_text(text: Optional[str]) -> Optional[str]:
    """Clean and normalize text content."""
    if not text:
        return None
    
    # Basic text cleaning
    text = text.strip()
    # Normalize whitespace
    text = ' '.join(text.split())
    
    return text if text else None

def extract_characters(text: str, max_chars: int = 8) -> List[str]:
    """
    Extract notable character names from text.
    This is a simple heuristic - looks for capitalized words that might be names.
    """
    if not text:
        return []
    
    # Simple pattern: look for capitalized words, but avoid common words
    import re
    
    # Common words to exclude
    exclude = {
        'The', 'And', 'Or', 'But', 'In', 'On', 'At', 'To', 'For', 'Of', 'With',
        'By', 'From', 'Up', 'About', 'Into', 'Through', 'During', 'Before',
        'After', 'Above', 'Below', 'Between', 'Among', 'This', 'That', 'These',
        'Those', 'He', 'She', 'It', 'They', 'We', 'You', 'His', 'Her', 'Its',
        'Their', 'Our', 'Your', 'Episode', 'Season', 'Series', 'Show', 'Character',
        'Characters', 'Story', 'Plot'
    }
    
    # Find capitalized words (potential names)
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
    
    # Filter out common words and duplicates
    characters = []
    seen = set()
    
    for word in words:
        if word not in exclude and word.lower() not in seen and len(word) > 2:
            characters.append(word)
            seen.add(word.lower())
            if len(characters) >= max_chars:
                break
    
    return characters[:max_chars]