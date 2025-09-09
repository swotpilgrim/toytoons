#!/usr/bin/env python3

import asyncio
import json
from scraper.images import ImageScraper

async def debug_images():
    """Debug image URL extraction"""
    
    # Use the existing raw HTML file
    import os
    from pathlib import Path
    
    raw_files = list(Path("data/raw").glob("*.json"))
    if not raw_files:
        print("No raw files found")
        return
    
    # Load the most recent raw file
    with open(raw_files[0], 'r', encoding='utf-8') as f:
        doc_data = json.load(f)
    
    print(f"Loaded document: {doc_data['url']}")
    print(f"HTML length: {len(doc_data['html'])} characters")
    
    # Test image extraction
    image_scraper = ImageScraper()
    images = await image_scraper.extract_images_from_html(doc_data['html'], doc_data['url'])
    
    print(f"Found {len(images)} images:")
    for i, img in enumerate(images):
        print(f"  {i+1}. Type: {img['type']}")
        print(f"      URL: {repr(img['url'])}")  # Use repr to see full URL
        print(f"      Desc: {img['description']}")
        print()
    
    # Test one image download
    if images:
        test_img = images[0]
        print(f"Testing download of: {repr(test_img['url'])}")
        
        filename = image_scraper.generate_image_filename(test_img['url'], 'test-slug', 'main')
        print(f"Generated filename: {filename}")
        
        result = await image_scraper.download_image(test_img['url'], filename)
        print(f"Download result: {result}")

if __name__ == "__main__":
    asyncio.run(debug_images())