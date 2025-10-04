#!/usr/bin/env python3
"""
scripts/update_gallery.py

- Update /images/gallery.json automatically
- Ensure every .jpg has a corresponding -thumb.jpg
- Add new entries for new images, preserve old entries
"""

import json
from pathlib import Path
from PIL import Image

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "images"
GALLERY_PATH = IMAGES_DIR / "gallery.json"
THUMB_SUFFIX = "-thumb"
THUMB_SIZE = (400, 400)  # px

# ------------------- Helper Functions -------------------

def is_image_file(p: Path):
    return p.suffix.lower() in [".jpg", ".jpeg"]

def make_center_square(im: Image.Image):
    w, h = im.size
    if w == h:
        return im
    min_side = min(w, h)
    left = (w - min_side) // 2
    top = (h - min_side) // 2
    return im.crop((left, top, left + min_side, top + min_side))

def create_thumbnail(src: Path, dst: Path):
    try:
        with Image.open(src) as im:
            im = im.convert("RGB")
            im = make_center_square(im)
            im = im.resize(THUMB_SIZE, Image.LANCZOS)
            dst.parent.mkdir(parents=True, exist_ok=True)
            im.save(dst, "JPEG", quality=85)
            print(f"Created thumbnail: {dst.name}")
    except Exception as e:
        print(f"Failed to create thumbnail for {src.name}: {e}")
        return False
    return True

def load_gallery():
    if not GALLERY_PATH.exists():
        return []
    try:
        return json.loads(GALLERY_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Warning: failed to read existing gallery.json: {e}")
        return []

def save_gallery(entries):
    GALLERY_PATH.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved gallery with {len(entries)} entries.")

def default_entry(image_name: str):
    name = Path(image_name).stem
    return {
        "id": None,
        "title": name,
        "description": "NaN",
        "category": "None",
        "thumbnail": f"./images/{name}{THUMB_SUFFIX}.jpg",
        "image": f"./images/{name}.jpg",
        "location": "None",
        "date": "2000-01-01",
        "camera": "None",
        "tags": ["None"]
    }

# ------------------- Main -------------------

def main():
    if not IMAGES_DIR.exists():
        print(f"No images directory found at {IMAGES_DIR}. Exiting.")
        return

    # Load existing gallery and create a lookup map by image path
    gallery = load_gallery()
    gallery_map = {entry["image"]: entry for entry in gallery}

    # Scan for images
    images = [p for p in IMAGES_DIR.iterdir() if p.is_file() and is_image_file(p)]
    for img in images:
        if img.stem.lower().endswith(THUMB_SUFFIX.lstrip("-")):
            continue  # skip thumbnails

        thumb_path = IMAGES_DIR / f"{img.stem}{THUMB_SUFFIX}.jpg"
        if not thumb_path.exists():
            create_thumbnail(img, thumb_path)

        rel_image_path = f"./images/{img.name}"
        rel_thumb_path = f"./images/{thumb_path.name}"

        if rel_image_path not in gallery_map:
            # New entry
            entry = default_entry(img.name)
            entry["thumbnail"] = rel_thumb_path
            entry["image"] = rel_image_path
            gallery.append(entry)
        else:
            # Ensure thumbnail path is correct
            gallery_map[rel_image_path]["thumbnail"] = rel_thumb_path

    # Assign stable incremental IDs starting from 1
    for idx, entry in enumerate(sorted(gallery, key=lambda x: x["image"]), start=1):
        entry["id"] = idx

    save_gallery(gallery)

if __name__ == "__main__":
    main()
