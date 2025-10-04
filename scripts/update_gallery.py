#!/usr/bin/env python3
"""
scripts/update_gallery.py

- Scan ./images for .jpg/.jpeg (case-insensitive)
- For each image (excluding files ending with -thumb.jpg), ensure a corresponding -thumb.jpg exists.
- Build/update images/gallery.json: keep existing metadata for files that remain; add defaults for new ones.
- Remove entries which no longer have both image and thumbnail.
"""

import json
from pathlib import Path
from PIL import Image
import sys

# Resolve paths relative to the script's location
BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "images"
GALLERY_PATH = IMAGES_DIR / "gallery.json"
THUMB_SUFFIX = "-thumb"
THUMB_SIZE = (400, 400)   # output thumbnail dimensions (px)

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
            print(f"Created thumbnail: {dst}")
    except Exception as e:
        print(f"Failed to make thumbnail for {src}: {e}")
        # do not crash entire workflow for a single bad file
        return False
    return True

def load_existing_gallery():
    if not GALLERY_PATH.exists():
        return []
    try:
        return json.loads(GALLERY_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Warning: failed to read existing gallery.json: {e}")
        return []

def save_gallery(entries):
    GALLERY_PATH.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved gallery: {GALLERY_PATH} (entries={len(entries)})")

def default_entry_for(image_rel):
    name = Path(image_rel).stem
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

def main():
    if not IMAGES_DIR.exists() or not IMAGES_DIR.is_dir():
        print("No images directory found. Exiting.")
        sys.exit(0)

    # collect all source images (not thumbs)
    all_images = [p for p in IMAGES_DIR.iterdir() if p.is_file() and is_image_file(p)]
    src_images = [p for p in all_images if not p.stem.lower().endswith(THUMB_SUFFIX.lstrip('-'))]

    # ensure thumbs exist
    for src in src_images:
        thumb_name = src.with_name(f"{src.stem}{THUMB_SUFFIX}.jpg")
        if not thumb_name.exists():
            # create thumbnail
            ok = create_thumbnail(src, thumb_name)
            if not ok:
                print(f"Skipping {src} (thumbnail creation failed).")

    # now find pairs (image + thumb)
    pairs = []
    for src in src_images:
        thumb = IMAGES_DIR / f"{src.stem}{THUMB_SUFFIX}.jpg"
        if thumb.exists():
            pairs.append((src, thumb))

    # load existing gallery entries and index by image path (./images/<name>.jpg)
    existing = load_existing_gallery()
    existing_map = {}
    for e in existing:
        key = e.get("image", "").replace("./", "")
        existing_map[key] = e

    # build new entries, preserving metadata if possible
    new_entries = []
    for src, thumb in sorted(pairs, key=lambda x: x[0].name):
        rel_image = f"images/{src.name}"
        # attempt to find existing entry
        existing_entry = existing_map.get(rel_image)
        if existing_entry:
            # keep it but update thumbnail path if necessary
            existing_entry["thumbnail"] = f"./{thumb.as_posix()}"
            existing_entry["image"] = f"./{src.as_posix()}"
            new_entries.append(existing_entry)
        else:
            # add default entry
            ent = default_entry_for(src.name)
            new_entries.append(ent)

    # assign stable incremental ids starting at 1
    for i, e in enumerate(new_entries, start=1):
        e["id"] = i

    save_gallery(new_entries)

if __name__ == "__main__":
    main()
