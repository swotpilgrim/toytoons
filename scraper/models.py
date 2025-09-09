"""
Pydantic models for the toytoons scraper data structures.
"""

from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, HttpUrl, Field


class SourceDoc(BaseModel):
    """Raw document fetched from a URL."""
    url: str
    status_code: int
    headers: Dict[str, str]
    html: str
    fetched_at: datetime
    file_path: Optional[str] = None
    parse_notes: List[str] = Field(default_factory=list)


class Show(BaseModel):
    """Animated TV show information."""
    show_title: Optional[str] = None
    era: Optional[str] = None  # "1980s" or "early 1990s"
    years_aired: Optional[str] = None
    country: Optional[str] = None
    studio_network: Optional[str] = None
    
    
class Toyline(BaseModel):
    """Toy line information."""
    toyline_name: Optional[str] = None
    years_toyline: Optional[str] = None
    manufacturer: Optional[str] = None  # Hasbro, Mattel, Bandai, Kenner, etc.
    

class Listing(BaseModel):
    """A complete show + toyline listing."""
    # Core identifiers
    show_title: Optional[str] = None
    toyline_name: Optional[str] = None
    slug: Optional[str] = None  # URL-friendly identifier
    
    # Temporal information
    era: Optional[str] = None  # "1980s" or "early 1990s"
    years_aired: Optional[str] = None
    years_toyline: Optional[str] = None
    
    # Production information
    manufacturer: Optional[str] = None  # Hasbro, Mattel, Bandai, Kenner, etc.
    country: Optional[str] = None
    studio_network: Optional[str] = None
    
    # Content
    description_summary: Optional[str] = None
    notable_characters: List[str] = Field(default_factory=list)
    
    # Source tracking
    source_url: str
    source_title: Optional[str] = None
    first_seen: datetime
    
    # Processing metadata
    parse_notes: List[str] = Field(default_factory=list)
    
    def generate_slug(self) -> str:
        """Generate a URL-friendly slug from show and toyline names."""
        parts = []
        if self.show_title:
            parts.append(self.show_title.lower())
        if self.toyline_name and self.toyline_name.lower() != (self.show_title or "").lower():
            parts.append(self.toyline_name.lower())
        
        if not parts:
            # Fallback to source URL
            from urllib.parse import urlparse
            domain = urlparse(self.source_url).netloc
            parts.append(domain.replace(".", "-"))
        
        slug = "-".join(parts)
        # Clean up the slug
        slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in slug)
        slug = "-".join(filter(None, slug.split("-")))  # Remove empty parts
        return slug[:100]  # Limit length
    
    def model_post_init(self, __context: Any) -> None:
        """Post-initialization hook to set slug if not provided."""
        if not self.slug:
            self.slug = self.generate_slug()