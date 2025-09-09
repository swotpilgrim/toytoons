#!/usr/bin/env python3

import json
import os
from pathlib import Path

# Load the current JSON data
json_path = Path("data/processed/listings.json")
with open(json_path) as f:
    listings = json.load(f)

# Get list of actual image files
images_dir = Path("data/images")
actual_images = {f.name for f in images_dir.glob("*_main.*")}

print(f"Found {len(actual_images)} image files")

# Fix the image paths to match existing files
for listing in listings:
    if listing.get("main_image_local"):
        # Extract the filename from the path
        current_path = listing["main_image_local"]
        filename = Path(current_path).name
        
        # Check if this file exists
        if filename in actual_images:
            print(f"✓ {filename} exists")
        else:
            # Try to find a matching file based on the slug or show title
            slug = listing.get("slug", "")
            show_title = listing.get("show_title", "")
            
            # Look for files that might match this listing
            possible_matches = []
            for actual_file in actual_images:
                base_name = actual_file.replace("_main.", "").lower()
                if (slug and slug.lower() in base_name) or \
                   (show_title and any(word.lower() in base_name for word in show_title.split()[:3])):
                    possible_matches.append(actual_file)
            
            if possible_matches:
                # Use the first match
                new_filename = possible_matches[0]
                new_path = f"data\\images\\{new_filename}"
                listing["main_image_local"] = new_path
                print(f"→ Updated {filename} to {new_filename}")
            else:
                print(f"✗ No match found for {filename} (slug: {slug})")

# Save the updated JSON
with open(json_path, 'w') as f:
    json.dump(listings, f, indent=2)

print("Updated JSON with corrected image paths")