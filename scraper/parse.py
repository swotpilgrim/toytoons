"""
Parser for extracting show and toyline information from web pages.
"""

import re
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from readability import Document

from .config import Config
from .models import SourceDoc, Listing
from .utils import setup_logging, clean_text, extract_characters

logger = setup_logging()


class ContentExtractor:
    """Extract structured content from HTML using various strategies."""
    
    def __init__(self):
        self.era_patterns = [
            (r'198[0-9]', '1980s'),
            (r'199[0-3]', 'early 1990s'),
            (r'eighties?', '1980s'),
            (r'80s?', '1980s'),
            (r'early.?nine?ties?', 'early 1990s'),
            (r'early.?90s?', 'early 1990s')
        ]
        
        self.manufacturer_patterns = [
            r'\b(?:hasbro|mattel|bandai|kenner|playmates|ljn|coleco|tonka|galoob)\b'
        ]
        
        # Common year range patterns
        self.year_patterns = [
            r'\b(?:19[0-9]{2})\s*[-–—]\s*(?:19[0-9]{2})\b',  # 1985-1987
            r'\b(?:19[0-9]{2})\s*(?:to|through)\s*(?:19[0-9]{2})\b',  # 1985 to 1987
            r'\b(?:19[0-9]{2})\b'  # Single year
        ]
    
    def extract_main_content(self, html: str, url: str) -> Dict[str, Any]:
        """Extract main content using readability and BeautifulSoup."""
        soup = BeautifulSoup(html, 'lxml')
        
        # Use readability to extract main content
        doc = Document(html)
        readable_html = doc.summary()
        main_soup = BeautifulSoup(readable_html, 'lxml')
        
        # Extract key elements
        title = self._extract_title(soup, main_soup)
        main_text = self._extract_text_content(main_soup)
        
        # Extract structured data
        meta_info = self._extract_meta_info(soup)
        
        return {
            'title': title,
            'main_text': main_text,
            'meta_info': meta_info,
            'url': url,
            'extracted_at': datetime.now()
        }
    
    def _extract_title(self, soup: BeautifulSoup, main_soup: BeautifulSoup) -> Optional[str]:
        """Extract the most relevant title from the page."""
        # Try different title sources in order of preference
        title_candidates = []
        
        # Page title
        if soup.title:
            title_candidates.append(soup.title.get_text().strip())
        
        # Main content h1
        h1 = main_soup.find('h1')
        if h1:
            title_candidates.append(h1.get_text().strip())
        
        # First heading in main content
        for tag in main_soup.find_all(['h1', 'h2', 'h3']):
            text = tag.get_text().strip()
            if len(text) > 5:  # Avoid very short headings
                title_candidates.append(text)
                break
        
        # Clean and return best title
        for title in title_candidates:
            cleaned = clean_text(title)
            if cleaned and len(cleaned) > 3:
                return cleaned[:200]  # Limit length
        
        return None
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from soup."""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        # Clean up whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _extract_meta_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from HTML head."""
        meta_info = {}
        
        # Common meta tags
        meta_tags = {
            'description': ['meta[name="description"]', 'meta[property="og:description"]'],
            'keywords': ['meta[name="keywords"]'],
            'canonical': ['link[rel="canonical"]'],
            'og_title': ['meta[property="og:title"]'],
            'og_type': ['meta[property="og:type"]']
        }
        
        for key, selectors in meta_tags.items():
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    content = element.get('content') or element.get('href')
                    if content:
                        meta_info[key] = content.strip()
                        break
        
        return meta_info


class ShowToylineParser:
    """Parse show and toyline information from extracted content."""
    
    def __init__(self):
        self.extractor = ContentExtractor()
    
    def parse_document(self, doc: SourceDoc) -> List[Listing]:
        """Parse a source document into listings."""
        try:
            # Extract content
            content = self.extractor.extract_main_content(doc.html, doc.url)
            
            # Create listing
            listing = self._create_listing(doc, content)
            
            if listing:
                return [listing]
            else:
                logger.warning(f"Could not create listing from {doc.url}")
                return []
                
        except Exception as e:
            logger.error(f"Error parsing {doc.url}: {e}")
            return []
    
    def _create_listing(self, doc: SourceDoc, content: Dict[str, Any]) -> Optional[Listing]:
        """Create a listing from extracted content."""
        parse_notes = []
        
        # Extract show title (prefer title from content over page title)
        show_title = self._extract_show_title(content, parse_notes)
        
        # Extract toyline name (might be same as show or different)
        toyline_name = self._extract_toyline_name(content, show_title, parse_notes)
        
        # Extract temporal information
        era = self._extract_era(content['main_text'], parse_notes)
        years_aired = self._extract_years_aired(content['main_text'], parse_notes)
        years_toyline = self._extract_years_toyline(content['main_text'], parse_notes)
        
        # Extract production info
        manufacturer = self._extract_manufacturer(content['main_text'], parse_notes)
        country = self._extract_country(content['main_text'], parse_notes)
        studio_network = self._extract_studio_network(content['main_text'], parse_notes)
        
        # Extract characters
        notable_characters = extract_characters(content['main_text'])
        
        # Source information
        source_title = content.get('title') or content.get('meta_info', {}).get('og_title')
        
        # Create listing
        listing = Listing(
            show_title=show_title,
            toyline_name=toyline_name,
            era=era,
            years_aired=years_aired,
            years_toyline=years_toyline,
            manufacturer=manufacturer,
            country=country,
            studio_network=studio_network,
            notable_characters=notable_characters,
            source_url=doc.url,
            source_title=source_title,
            first_seen=doc.fetched_at,
            parse_notes=parse_notes
        )
        
        # Only return if we have at least show_title or toyline_name
        if listing.show_title or listing.toyline_name:
            return listing
        
        parse_notes.append("No show title or toyline name found")
        return None
    
    def _extract_show_title(self, content: Dict[str, Any], notes: List[str]) -> Optional[str]:
        """Extract show title from content."""
        title = content.get('title')
        if title:
            # Clean up common title patterns
            title = re.sub(r'\s*[-|•]\s*.*$', '', title)  # Remove " - Site Name" parts
            title = clean_text(title)
            
            if title and len(title) > 3:
                notes.append(f"Show title from page title: {title}")
                return title
        
        # Try to extract from main text
        text = content['main_text'][:1000]  # Look in first part of text
        
        # Look for patterns like "The X Show" or "X (TV series)"
        show_patterns = [
            r'\b([A-Z][^.!?]*?(?:Show|Series|Chronicles|Adventures))\b',
            r'\b([A-Z][^(]*?)\s*\((?:TV|television|animated)\s*(?:series|show)\)',
            r'\b([A-Z][^.!?]*?(?:Cartoon|Animation))\b'
        ]
        
        for pattern in show_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                show_title = clean_text(matches[0])
                if show_title and len(show_title) > 3:
                    notes.append(f"Show title from text pattern: {show_title}")
                    return show_title
        
        return None
    
    def _extract_toyline_name(self, content: Dict[str, Any], show_title: Optional[str], notes: List[str]) -> Optional[str]:
        """Extract toyline name, which might be different from show title."""
        text = content['main_text']
        
        # Look for toy line patterns
        toy_patterns = [
            r'\b([A-Z][^.!?]*?(?:toys?|figures?|action figures?|toyline|toy line))\b',
            r'\b([A-Z][^.!?]*?(?:by|from)\s+(?:Hasbro|Mattel|Bandai|Kenner))\b'
        ]
        
        for pattern in toy_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                toyline_name = clean_text(matches[0])
                if toyline_name and len(toyline_name) > 3:
                    notes.append(f"Toyline name from text: {toyline_name}")
                    return toyline_name
        
        # If no specific toyline found, use show title
        if show_title:
            notes.append("Toyline name assumed same as show title")
            return show_title
        
        return None
    
    def _extract_era(self, text: str, notes: List[str]) -> Optional[str]:
        """Extract era (1980s or early 1990s) from text."""
        text_lower = text.lower()
        
        for pattern, era in self.extractor.era_patterns:
            if re.search(pattern, text_lower):
                notes.append(f"Era '{era}' from pattern: {pattern}")
                return era
        
        return None
    
    def _extract_years_aired(self, text: str, notes: List[str]) -> Optional[str]:
        """Extract years the show aired."""
        # Look for patterns like "aired from 1985 to 1987" or "1985-1987"
        aired_patterns = [
            r'aired\s+(?:from\s+)?(\d{4}(?:\s*[-–—]\s*\d{4})?)',
            r'broadcast\s+(?:from\s+)?(\d{4}(?:\s*[-–—]\s*\d{4})?)',
            r'ran\s+(?:from\s+)?(\d{4}(?:\s*[-–—]\s*\d{4})?)'
        ]
        
        for pattern in aired_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                years = match.group(1)
                notes.append(f"Years aired from pattern: {years}")
                return years
        
        return None
    
    def _extract_years_toyline(self, text: str, notes: List[str]) -> Optional[str]:
        """Extract years the toyline was produced."""
        # Look for toy-specific year patterns
        toy_year_patterns = [
            r'toys?\s+(?:produced|made|released)\s+(?:from\s+)?(\d{4}(?:\s*[-–—]\s*\d{4})?)',
            r'figures?\s+(?:produced|made|released)\s+(?:from\s+)?(\d{4}(?:\s*[-–—]\s*\d{4})?)'
        ]
        
        for pattern in toy_year_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                years = match.group(1)
                notes.append(f"Toyline years from pattern: {years}")
                return years
        
        return None
    
    def _extract_manufacturer(self, text: str, notes: List[str]) -> Optional[str]:
        """Extract toy manufacturer."""
        manufacturer_pattern = r'\b(Hasbro|Mattel|Bandai|Kenner|Playmates|LJN|Coleco|Tonka|Galoob)\b'
        
        match = re.search(manufacturer_pattern, text, re.IGNORECASE)
        if match:
            manufacturer = match.group(1).title()
            notes.append(f"Manufacturer found: {manufacturer}")
            return manufacturer
        
        return None
    
    def _extract_country(self, text: str, notes: List[str]) -> Optional[str]:
        """Extract country of origin."""
        # Look for country patterns
        country_patterns = [
            r'(?:from|in|produced in|made in)\s+((?:United States|USA|US|America|Japan|Canada|UK|Britain))',
            r'\b(American|Japanese|Canadian|British)\s+(?:animated|cartoon|series|show)'
        ]
        
        country_map = {
            'american': 'United States',
            'usa': 'United States', 
            'us': 'United States',
            'america': 'United States',
            'japanese': 'Japan',
            'canadian': 'Canada',
            'british': 'United Kingdom',
            'uk': 'United Kingdom',
            'britain': 'United Kingdom'
        }
        
        for pattern in country_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                country = match.group(1).lower()
                country = country_map.get(country, match.group(1).title())
                notes.append(f"Country found: {country}")
                return country
        
        return None
    
    def _extract_studio_network(self, text: str, notes: List[str]) -> Optional[str]:
        """Extract studio or network information."""
        # Look for studio/network patterns
        studio_patterns = [
            r'(?:produced by|by|from)\s+([A-Z][^.!?]*?(?:Studios?|Productions?|Entertainment|Animation))',
            r'(?:aired on|on)\s+([A-Z][^.!?]*?(?:Network|Channel|TV|Television|Broadcasting))'
        ]
        
        for pattern in studio_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                studio = clean_text(match.group(1))
                if studio and len(studio) > 3:
                    notes.append(f"Studio/Network found: {studio}")
                    return studio
        
        return None