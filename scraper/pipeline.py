"""
Main pipeline that orchestrates crawl -> parse -> summarize -> export.
"""

import asyncio
import pandas as pd
from datetime import datetime
from typing import List, Optional, Dict, Any

from .config import Config
from .models import SourceDoc, Listing
from .crawl import Crawler
from .parse import ShowToylineParser
from .summarize import SummarizationPipeline
from .utils import setup_logging, load_seeds, save_json, save_jsonl, load_jsonl

logger = setup_logging()


class ToytoonsePipeline:
    """Main pipeline orchestrating the entire scraping and processing workflow."""
    
    def __init__(self):
        self.crawler = Crawler()
        self.parser = ShowToylineParser()
        self.summarizer = SummarizationPipeline()
        Config.ensure_directories()
    
    async def run_full_pipeline(self, 
                               max_urls: Optional[int] = None,
                               force_crawl: bool = False,
                               force_parse: bool = False,
                               force_summarize: bool = False) -> Dict[str, Any]:
        """Run the complete pipeline: crawl -> parse -> summarize -> export."""
        
        stats = {
            'started_at': datetime.now(),
            'urls_crawled': 0,
            'docs_parsed': 0,
            'listings_created': 0,
            'summaries_generated': 0,
            'exports_created': 0
        }
        
        logger.info("🚀 Starting Toytoons pipeline")
        
        # Step 1: Crawl URLs
        docs = await self._crawl_stage(max_urls, force_crawl)
        stats['urls_crawled'] = len(docs)
        
        if not docs:
            logger.warning("No documents to process")
            stats['completed_at'] = datetime.now()
            stats['duration'] = stats['completed_at'] - stats['started_at']
            return stats
        
        # Step 2: Parse documents into listings
        listings = await self._parse_stage(docs, force_parse)
        stats['docs_parsed'] = len(docs)
        stats['listings_created'] = len(listings)
        
        if not listings:
            logger.warning("No listings created")
            return stats
        
        # Step 3: Generate summaries
        listings = await self._summarize_stage(listings, docs, force_summarize)
        stats['summaries_generated'] = sum(1 for l in listings if l.description_summary)
        
        # Step 4: Export data
        export_paths = self._export_stage(listings)
        stats['exports_created'] = len(export_paths)
        
        stats['completed_at'] = datetime.now()
        stats['duration'] = stats['completed_at'] - stats['started_at']
        
        self._print_stats(stats)
        
        return stats
    
    async def _crawl_stage(self, max_urls: Optional[int], force: bool) -> List[SourceDoc]:
        """Crawl URLs from seeds file."""
        logger.info("📡 Step 1: Crawling URLs")
        
        # Load existing docs if not forcing
        if not force:
            existing_docs = self.crawler.load_existing_docs()
            if existing_docs:
                logger.info(f"Using {len(existing_docs)} existing documents")
                return existing_docs[:max_urls] if max_urls else existing_docs
        
        # Load seed URLs
        seed_urls = load_seeds(Config.SEEDS_FILE)
        
        if not seed_urls:
            logger.error("No seed URLs found. Please add URLs to scraper/seeds.txt")
            return []
        
        if max_urls:
            seed_urls = seed_urls[:max_urls]
        
        logger.info(f"Crawling {len(seed_urls)} URLs")
        
        # Crawl URLs
        docs = await self.crawler.crawl_urls(seed_urls)
        
        logger.info(f"✓ Crawled {len(docs)} documents")
        return docs
    
    async def _parse_stage(self, docs: List[SourceDoc], force: bool) -> List[Listing]:
        """Parse documents into structured listings."""
        logger.info("🔍 Step 2: Parsing documents")
        
        # Check for existing parsed data
        if not force and Config.DOCS_JSONL.exists():
            existing_listings = self._load_existing_listings()
            if existing_listings:
                logger.info(f"Using {len(existing_listings)} existing listings")
                return existing_listings
        
        # Parse all documents
        all_listings = []
        
        for i, doc in enumerate(docs, 1):
            logger.debug(f"Parsing document {i}/{len(docs)}: {doc.url}")
            
            try:
                doc_listings = await self.parser.parse_document(doc)
                all_listings.extend(doc_listings)
                
            except Exception as e:
                logger.error(f"Error parsing {doc.url}: {e}")
        
        logger.info(f"✓ Created {len(all_listings)} listings from {len(docs)} documents")
        
        # Save parsed listings
        self._save_listings_jsonl(all_listings)
        
        return all_listings
    
    async def _summarize_stage(self, listings: List[Listing], docs: List[SourceDoc], force: bool) -> List[Listing]:
        """Generate summaries for listings."""
        logger.info("📝 Step 3: Generating summaries")
        
        # Create URL to document mapping
        url_to_doc = {doc.url: doc for doc in docs}
        
        summaries_needed = [l for l in listings if not l.description_summary or force]
        
        if not summaries_needed:
            logger.info("All listings already have summaries")
            return listings
        
        logger.info(f"Generating summaries for {len(summaries_needed)} listings")
        
        # Generate summaries
        for i, listing in enumerate(summaries_needed, 1):
            logger.debug(f"Summarizing {i}/{len(summaries_needed)}: {listing.slug}")
            
            # Get source document
            source_doc = url_to_doc.get(listing.source_url)
            if not source_doc:
                logger.warning(f"No source document for {listing.source_url}")
                continue
            
            try:
                # Enhance listing with summary
                self.summarizer.enhance_listing_with_summary(listing, source_doc.html)
                
            except Exception as e:
                logger.error(f"Error summarizing {listing.slug}: {e}")
        
        summaries_count = sum(1 for l in listings if l.description_summary)
        logger.info(f"✓ Generated summaries ({summaries_count}/{len(listings)} total)")
        
        return listings
    
    def _export_stage(self, listings: List[Listing]) -> List[str]:
        """Export listings to JSON and CSV formats."""
        logger.info("💾 Step 4: Exporting data")
        
        export_paths = []
        
        # Export to JSON
        listings_data = [listing.model_dump(mode='json') for listing in listings]
        save_json(listings_data, Config.LISTINGS_JSON)
        export_paths.append(str(Config.LISTINGS_JSON))
        logger.info(f"✓ Exported to {Config.LISTINGS_JSON}")
        
        # Export to CSV
        if listings_data:
            df = pd.DataFrame(listings_data)
            
            # Flatten list fields for CSV
            if 'notable_characters' in df.columns:
                df['notable_characters'] = df['notable_characters'].apply(
                    lambda x: ', '.join(x) if isinstance(x, list) else x
                )
            
            if 'parse_notes' in df.columns:
                df['parse_notes'] = df['parse_notes'].apply(
                    lambda x: ' | '.join(x) if isinstance(x, list) else x
                )
            
            df.to_csv(Config.LISTINGS_CSV, index=False)
            export_paths.append(str(Config.LISTINGS_CSV))
            logger.info(f"✓ Exported to {Config.LISTINGS_CSV}")
        
        return export_paths
    
    def _load_existing_listings(self) -> List[Listing]:
        """Load existing parsed listings."""
        try:
            data = load_jsonl(Config.DOCS_JSONL)
            return [Listing(**item) for item in data]
        except Exception as e:
            logger.warning(f"Could not load existing listings: {e}")
            return []
    
    def _save_listings_jsonl(self, listings: List[Listing]):
        """Save listings to JSONL format."""
        data = [listing.model_dump(mode='json') for listing in listings]
        save_jsonl(data, Config.DOCS_JSONL)
        logger.debug(f"Saved {len(listings)} listings to {Config.DOCS_JSONL}")
    
    def _print_stats(self, stats: Dict[str, Any]):
        """Print pipeline statistics."""
        logger.info("📊 Pipeline completed!")
        logger.info(f"   • URLs crawled: {stats['urls_crawled']}")
        logger.info(f"   • Documents parsed: {stats['docs_parsed']}")
        logger.info(f"   • Listings created: {stats['listings_created']}")
        logger.info(f"   • Summaries generated: {stats['summaries_generated']}")
        logger.info(f"   • Export files created: {stats['exports_created']}")
        logger.info(f"   • Duration: {stats['duration']}")
    
    async def crawl_only(self, max_urls: Optional[int] = None) -> List[SourceDoc]:
        """Run only the crawling stage."""
        logger.info("🚀 Running crawl-only pipeline")
        return await self._crawl_stage(max_urls, force=True)
    
    def parse_only(self) -> List[Listing]:
        """Run only the parsing stage on existing documents."""
        logger.info("🚀 Running parse-only pipeline")
        docs = self.crawler.load_existing_docs()
        return self._parse_stage(docs, force=True)
    
    async def summarize_only(self) -> List[Listing]:
        """Run only the summarization stage on existing listings."""
        logger.info("🚀 Running summarize-only pipeline")
        
        # Load existing data
        docs = self.crawler.load_existing_docs()
        listings = self._load_existing_listings()
        
        if not listings:
            logger.error("No existing listings found. Run parse first.")
            return []
        
        # Generate summaries
        listings = await self._summarize_stage(listings, docs, force=True)
        
        # Re-export with summaries
        self._export_stage(listings)
        
        return listings