"""
Image scraping and processing for the toytoons scraper.
"""

import os
import asyncio
import aiohttp
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from .config import Config

logger = logging.getLogger(__name__)


class ImageScraper:
    """Handles image scraping and storage for listings."""
    
    def __init__(self):
        self.images_dir = Config.DATA_ROOT / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # Supported image formats
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        
        # Common Wikipedia image selectors
        self.selectors = [
            'table.infobox img',  # Main infobox image
            '.infobox-image img',  # Alternative infobox
            'div[class*="infobox"] img',  # Generic infobox
        ]
        
    
    async def extract_images_from_html(self, html: str, base_url: str) -> List[Dict[str, str]]:
        """Extract image URLs and metadata from HTML."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            images = []
            
            # Try different selectors for main image
            main_image = None
            for selector in self.selectors:
                img_tags = soup.select(selector)
                if img_tags:
                    main_image = self._process_image_tag(img_tags[0], base_url)
                    if main_image:
                        break
            
            if main_image:
                images.append({
                    'url': main_image['url'],
                    'description': main_image.get('alt', 'Main image'),
                    'type': 'main',
                    'local': None
                })
            
            # Skip additional images for now - just use main images
            
            return images
            
        except Exception as e:
            logger.error(f"Error extracting images from HTML: {e}")
            return []
    
    def _process_image_tag(self, img_tag, base_url: str) -> Optional[Dict[str, str]]:
        """Process a single image tag and return normalized data."""
        try:
            src = img_tag.get('src')
            if not src:
                return None
            
            # Convert relative URLs to absolute
            img_url = urljoin(base_url, src)
            
            # Skip data URLs
            if img_url.startswith('data:'):
                return None
            
            # Check if it's a supported format
            parsed = urlparse(img_url)
            path_lower = parsed.path.lower()
            
            if not any(path_lower.endswith(ext) for ext in self.supported_formats):
                return None
            
            # Get higher resolution version for Wikipedia images
            if 'wikimedia.org' in img_url and 'thumb' in img_url:
                # Try to get larger version
                img_url = self._get_larger_wikipedia_image(img_url)
            
            return {
                'url': img_url,
                'alt': img_tag.get('alt', ''),
                'title': img_tag.get('title', ''),
                'width': img_tag.get('width'),
                'height': img_tag.get('height')
            }
            
        except Exception as e:
            logger.warning(f"Error processing image tag: {e}")
            return None
    
    def _get_larger_wikipedia_image(self, thumb_url: str) -> str:
        """Convert Wikipedia thumbnail URL to larger version."""
        try:
            # Skip processing, just return original URL - Wikipedia thumbnails work fine
            return thumb_url
            
        except Exception:
            return thumb_url
    
    def _is_relevant_image(self, img_tag, img_data: Dict[str, str]) -> bool:
        """Check if an image is relevant (not a small icon or wiki element)."""
        try:
            # Skip very small images (lowered threshold)
            width = img_data.get('width')
            height = img_data.get('height')
            
            if width and height:
                try:
                    w, h = int(width), int(height)
                    if w < 80 or h < 80:  # Raised back up to avoid tiny icons
                        return False
                except ValueError:
                    pass
            
            # Skip common Wikipedia icons and elements (expanded list)
            src = img_data['url'].lower()
            skip_patterns = [
                'commons-logo', 'wikimedia', 'edit-icon', 'folder-icon',
                'portal:', 'flag', 'coat-of-arms', '/40px-', '/20px-',
                'ambox', 'navbox', 'magnify-clip', 'wikipedia.png',
                'commons.png', 'external-link', 'icon', 'sprite',
                'commons/thumb', 'static/images/icons', 'arrow',
                'button', 'symbol', 'logo.svg', 'wiktionary', 'wikisource'
            ]
            
            for pattern in skip_patterns:
                if pattern in src:
                    return False
            
            # Check alt text for relevance
            alt = img_data.get('alt', '').lower()
            # Skip generic alt text
            if any(word in alt for word in ['icon', 'flag', 'stub', 'edit', 'arrow', 'button', 'symbol']):
                return False
            
            # Prefer images with relevant alt text
            relevant_keywords = ['screenshot', 'poster', 'logo', 'character', 'toy', 'figure', 'show', 'cartoon', 'series']
            has_relevant_alt = any(keyword in alt for keyword in relevant_keywords)
            
            # Skip very generic or empty alt text unless it's from a good source
            if not alt or alt in ['', ' ']:
                # Only allow if it's from a trusted upload source
                if 'upload.wikimedia.org' not in src:
                    return False
            
            return True
            
        except Exception:
            return True  # Default to including if unsure
    
    async def download_image(self, url: str, filename: str) -> Optional[str]:
        """Download an image and save it locally."""
        try:
            local_path = self.images_dir / filename
            
            # Skip if already exists
            if local_path.exists():
                return str(local_path.relative_to(Config.PROJECT_ROOT))
            
            # Headers to avoid 403 errors from Wikipedia
            headers = {
                'User-Agent': 'ToyToons-Scraper/0.1 (Educational Project)',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        with open(local_path, 'wb') as f:
                            f.write(content)
                        
                        logger.info(f"Downloaded image: {filename}")
                        return str(local_path.relative_to(Config.PROJECT_ROOT))
                    else:
                        logger.warning(f"Failed to download image {url}: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error downloading image {url}: {e}")
            return None
    
    def generate_image_filename(self, url: str, listing_slug: str, image_type: str = 'main') -> str:
        """Generate a filename for an image."""
        try:
            parsed = urlparse(url)
            extension = Path(parsed.path).suffix or '.jpg'
            
            # Clean the listing slug
            clean_slug = "".join(c for c in listing_slug if c.isalnum() or c in '-_')
            
            return f"{clean_slug}_{image_type}{extension}"
            
        except Exception:
            return f"{listing_slug}_{image_type}.jpg"
    
    async def process_listing_images(self, html: str, base_url: str, listing_slug: str) -> Tuple[Optional[str], List[Dict[str, str]]]:
        """Process all images for a listing and download them."""
        try:
            # Extract images from HTML
            images = await self.extract_images_from_html(html, base_url)
            
            if not images:
                return None, []
            
            main_image_local = None
            processed_additional = []
            
            # Process main image
            main_images = [img for img in images if img['type'] == 'main']
            if main_images:
                main_img = main_images[0]
                filename = self.generate_image_filename(main_img['url'], listing_slug, 'main')
                local_path = await self.download_image(main_img['url'], filename)
                if local_path:
                    main_image_local = local_path
            
            # Skip processing additional images
            
            return main_image_local, processed_additional
            
        except Exception as e:
            logger.error(f"Error processing images for {listing_slug}: {e}")
            return None, []