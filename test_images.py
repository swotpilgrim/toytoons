#!/usr/bin/env python3

import asyncio
from scraper.images import ImageScraper
from scraper.crawl import Crawler

async def test_image_scraping():
    """Test image scraping on He-Man Wikipedia page"""
    
    # Crawl the He-Man page
    crawler = Crawler()
    urls = ["https://en.wikipedia.org/wiki/He-Man_and_the_Masters_of_the_Universe"]
    docs = await crawler.crawl_urls(urls)
    
    if not docs:
        print("❌ Failed to crawl document")
        return
    
    doc = docs[0]
    print(f"✅ Crawled document: {len(doc.html)} characters")
    
    # Test image extraction
    image_scraper = ImageScraper()
    images = await image_scraper.extract_images_from_html(doc.html, doc.url)
    
    print(f"\n🖼️  Found {len(images)} images:")
    for i, img in enumerate(images):
        print(f"  {i+1}. Type: {img['type']}")
        print(f"      URL: {img['url']}")
        print(f"      Description: {img['description']}")
        print()
    
    # Test image processing
    if images:
        main_image_local, additional_images = await image_scraper.process_listing_images(
            doc.html, doc.url, "test-slug"
        )
        
        print(f"📁 Processing results:")
        print(f"   Main image local: {main_image_local}")
        print(f"   Additional images: {len(additional_images)}")

if __name__ == "__main__":
    asyncio.run(test_image_scraping())