#!/usr/bin/env python3
"""
Safe update_gallery.py

- Only adds new images to gallery.json
- Preserves all metadata for existing entries
- Generates missing thumbnails
"""

import json
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "images"
GALLERY_PATH = IMAGES_DIR / "gallery.json"
THUMB_SUFFIX = "-thumb"
THUMB_SIZE = (400, 400)

def is_image_file(p: Path):
    return p.suffix.lower() in [".jpg", ".jpeg"]

def make_center_square(im: Image.Image):
    w, h = im.size
    if w == h: return im
    min_side = min(w, h)
    left = (w - min_side) // 2
    top = (h - min_side) // 2
    return im.crop((left, top, left + min_side, top + min_side))

def create_thumbnail(src: Path, dst: Path):
    if dst.exists():
        return
    try:
        with Image.open(src) as im:
            im = im.convert("RGB")
            im = make_center_square(im)
            im = im.resize(THUMB_SIZE, Image.LANCZOS)
            dst.parent.mkdir(parents=True, exist_ok=True)
            im.save(dst, "JPEG", quality=85)
            print(f"Created thumbnail: {dst.name}")
    except Exception as e:
        print(f"Failed thumbnail for {src.name}: {e}")

def load_gallery():
    if not GALLERY_PATH.exists():
        return []
    try:
        return json.loads(GALLERY_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Warning reading gallery.json: {e}")
        return []

def save_gallery(entries):
    GALLERY_PATH.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved gallery.json with {len(entries)} entries.")

def default_entry(img_name: str, next_id: int):
    stem = Path(img_name).stem
    return {
        "id": next_id,
        "title": stem,
        "description": "NaN",
        "category": "None",
        "thumbnail": f"./images/{stem}{THUMB_SUFFIX}.jpg",
        "image": f"./images/{stem}.jpg",
        "location": "None",
        "date": "2000-01-01",
        "camera": "None",
        "tags": ["None"]
    }

def main():
    if not IMAGES_DIR.exists(): return

    gallery = load_gallery()
    existing_images = {entry["image"]: entry for entry in gallery}
    max_id = max([entry.get("id", 0) for entry in gallery], default=0)

    images = [p for p in IMAGES_DIR.iterdir() if p.is_file() and is_image_file(p)]
    new_entries = []

    for img in images:
        if img.stem.lower().endswith(THUMB_SUFFIX.lstrip("-")):
            continue

        thumb_path = IMAGES_DIR / f"{img.stem}{THUMB_SUFFIX}.jpg"
        create_thumbnail(img, thumb_path)

        rel_image = f"./images/{img.name}"
        rel_thumb = f"./images/{thumb_path.name}"

        if rel_image not in existing_images:
            max_id += 1
            entry = default_entry(img.name, max_id)
            entry["thumbnail"] = rel_thumb
            new_entries.append(entry)
        else:
            # Preserve existing metadata, only update thumbnail if missing
            if existing_images[rel_image].get("thumbnail") != rel_thumb:
                existing_images[rel_image]["thumbnail"] = rel_thumb

    # Append only new entries
    gallery.extend(new_entries)
    save_gallery(gallery)

if __name__ == "__main__":
    main()
