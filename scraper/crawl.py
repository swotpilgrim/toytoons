"""
Web crawler with robots.txt respect, retries, and polite delays.
"""

import asyncio
import random
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from .config import Config
from .models import SourceDoc
from .utils import setup_logging, url_to_hash, get_domain, generate_timestamp, save_json

logger = setup_logging()


class RobotsChecker:
    """Check robots.txt compliance for URLs."""
    
    def __init__(self):
        self._cache = {}
    
    def can_fetch(self, url: str, user_agent: str) -> bool:
        """Check if URL can be fetched according to robots.txt."""
        domain = get_domain(url)
        
        if domain not in self._cache:
            robots_url = f"https://{domain}/robots.txt"
            rp = RobotFileParser()
            rp.set_url(robots_url)
            
            try:
                rp.read()
                self._cache[domain] = rp
                logger.debug(f"Loaded robots.txt for {domain}")
            except Exception as e:
                logger.warning(f"Could not load robots.txt for {domain}: {e}")
                # If we can't load robots.txt, assume we can fetch
                self._cache[domain] = None
        
        robots = self._cache[domain]
        if robots is None:
            return True
        
        return robots.can_fetch(user_agent, url)


class PoliteHTTPClient:
    """HTTP client with polite delays, retries, and timeout handling."""
    
    def __init__(self):
        self.robots = RobotsChecker()
        self.last_request_time = {}  # domain -> timestamp
        
        # Configure httpx client
        timeout = httpx.Timeout(Config.TIMEOUT_SECONDS, read=Config.TIMEOUT_SECONDS)
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": Config.USER_AGENT},
            follow_redirects=True
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def _wait_politely(self, domain: str):
        """Wait politely between requests to the same domain."""
        if domain in self.last_request_time:
            time_since_last = time.time() - self.last_request_time[domain]
            delay = random.uniform(Config.DELAY_MIN, Config.DELAY_MAX)
            
            if time_since_last < delay:
                wait_time = delay - time_since_last
                logger.debug(f"Waiting {wait_time:.1f}s before requesting from {domain}")
                await asyncio.sleep(wait_time)
        
        self.last_request_time[domain] = time.time()
    
    async def fetch_with_retries(self, url: str) -> Optional[SourceDoc]:
        """Fetch URL with retries and exponential backoff."""
        domain = get_domain(url)
        
        # Check robots.txt
        if not self.robots.can_fetch(url, Config.USER_AGENT):
            logger.warning(f"Robots.txt disallows fetching {url}")
            return None
        
        # Wait politely
        await self._wait_politely(domain)
        
        last_exception = None
        
        for attempt in range(Config.MAX_RETRIES + 1):
            try:
                logger.debug(f"Fetching {url} (attempt {attempt + 1})")
                
                response = await self.client.get(url)
                
                # Create source document
                doc = SourceDoc(
                    url=url,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    html=response.text,
                    fetched_at=datetime.now()
                )
                
                if response.status_code == 200:
                    logger.info(f"✓ Fetched {url} ({len(response.text)} chars)")
                    return doc
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    return doc  # Return even non-200 responses for inspection
                    
            except Exception as e:
                last_exception = e
                if attempt < Config.MAX_RETRIES:
                    backoff = 2 ** attempt
                    logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}. Retrying in {backoff}s...")
                    await asyncio.sleep(backoff)
                else:
                    logger.error(f"Failed to fetch {url} after {Config.MAX_RETRIES + 1} attempts: {e}")
        
        return None


class Crawler:
    """Main crawler class that orchestrates fetching."""
    
    def __init__(self):
        Config.ensure_directories()
    
    async def crawl_urls(self, urls: List[str], max_concurrent: int = None) -> List[SourceDoc]:
        """Crawl multiple URLs with controlled concurrency."""
        if not urls:
            logger.warning("No URLs to crawl")
            return []
        
        max_concurrent = max_concurrent or Config.CONCURRENCY
        logger.info(f"Starting crawl of {len(urls)} URLs with concurrency={max_concurrent}")
        
        docs = []
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_one(url: str) -> Optional[SourceDoc]:
            async with semaphore:
                async with PoliteHTTPClient() as client:
                    return await client.fetch_with_retries(url)
        
        # Create progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=logger.handlers[0].console
        ) as progress:
            
            task = progress.add_task("Crawling URLs...", total=len(urls))
            
            # Launch all fetch tasks
            tasks = []
            for url in urls:
                task_coro = fetch_one(url)
                tasks.append(task_coro)
            
            # Process results as they complete
            for coro in asyncio.as_completed(tasks):
                doc = await coro
                if doc:
                    # Save raw document
                    await self._save_raw_doc(doc)
                    docs.append(doc)
                
                progress.advance(task)
        
        logger.info(f"Crawling completed. Fetched {len(docs)} documents successfully.")
        return docs
    
    async def _save_raw_doc(self, doc: SourceDoc):
        """Save raw document to disk."""
        timestamp = generate_timestamp()
        url_hash = url_to_hash(doc.url)
        filename = f"{timestamp}_{url_hash}.json"
        filepath = Config.RAW_DATA_DIR / filename
        
        doc.file_path = str(filepath)
        
        # Save as JSON
        doc_data = doc.model_dump(mode='json')
        save_json(doc_data, filepath)
        
        logger.debug(f"Saved raw document: {filename}")
    
    def load_existing_docs(self) -> List[SourceDoc]:
        """Load previously crawled documents."""
        docs = []
        
        if not Config.RAW_DATA_DIR.exists():
            return docs
        
        for json_file in Config.RAW_DATA_DIR.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    import json
                    data = json.load(f)
                    doc = SourceDoc(**data)
                    docs.append(doc)
            except Exception as e:
                logger.warning(f"Could not load {json_file}: {e}")
        
        logger.info(f"Loaded {len(docs)} existing documents")
        return docs