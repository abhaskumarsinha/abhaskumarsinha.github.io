import os
import json
from datetime import datetime

# Path setup
IMAGE_DIR = "./images"
GALLERY_JSON = os.path.join(IMAGE_DIR, "gallery.json")

# Load existing JSON if exists, else empty
if os.path.exists(GALLERY_JSON):
    with open(GALLERY_JSON, "r", encoding="utf-8") as f:
        try:
            gallery = json.load(f)
        except json.JSONDecodeError:
            gallery = []
else:
    gallery = []

# Collect existing image names to avoid duplicates
existing_images = {os.path.basename(item["image"]) for item in gallery}

# Find all images and their thumbnails
jpg_files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(".jpg")]

new_entries = []
next_id = max([item["id"] for item in gallery], default=0) + 1

for f in jpg_files:
    if f.endswith("-thumb.jpg"):
        continue
    thumb_name = f.replace(".jpg", "-thumb.jpg")
    if thumb_name in jpg_files:
        if f not in existing_images:
            entry = {
                "id": next_id,
                "title": "Null",
                "description": "NaN",
                "category": "None",
                "thumbnail": f"./images/{thumb_name}",
                "image": f"./images/{f}",
                "location": "None",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "camera": "None",
                "tags": ["None"]
            }
            new_entries.append(entry)
            next_id += 1

# Only update if there are new entries
if new_entries:
    gallery.extend(new_entries)
    with open(GALLERY_JSON, "w", encoding="utf-8") as f:
        json.dump(gallery, f, indent=2, ensure_ascii=False)
    print(f"✅ Added {len(new_entries)} new entries to gallery.json")
else:
    print("✅ No new image pairs found. gallery.json is up-to-date.")
