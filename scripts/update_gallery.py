#!/usr/bin/env python3
"""
scripts/update_gallery.py

- Safe, idempotent update of images/gallery.json
- Creates missing thumbnails
- Preserves all metadata for existing entries
- Normalizes image path comparisons (handles "./images/..." vs "images/...")
- Writes gallery.json only if something changed
- Prints detailed debug logs for CI
"""

import json
from pathlib import Path
from PIL import Image
import tempfile
import os
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "images"
GALLERY_PATH = IMAGES_DIR / "gallery.json"
THUMB_SUFFIX = "-thumb"
THUMB_SIZE = (400, 400)

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
    if dst.exists():
        print(f"Thumbnail already exists: {dst.name}")
        return True
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
        print("No gallery.json found; starting with empty gallery.")
        return []
    try:
        data = json.loads(GALLERY_PATH.read_text(encoding="utf-8"))
        print(f"Loaded gallery.json with {len(data)} entries.")
        return data
    except Exception as e:
        print(f"Warning: failed to parse gallery.json: {e}")
        return []

def atomic_write(path: Path, data: str):
    # write to temp and move into place (atomic-ish)
    tmp_fd, tmp_path = tempfile.mkstemp(prefix="gallery-", dir=str(path.parent))
    with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
        f.write(data)
    os.replace(tmp_path, str(path))
    print(f"Wrote {path} (atomic replace).")

def normalize_key(p: str):
    # normalize stored image path for lookup: remove leading "./" if present
    if p is None:
        return ""
    return p[2:] if p.startswith("./") else p

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
    if not IMAGES_DIR.exists():
        print(f"Images directory not found at {IMAGES_DIR}. Exiting.")
        sys.exit(0)

    gallery = load_gallery()
    # build normalized lookup for existing entries (preserve original entry object)
    existing = {}
    for e in gallery:
        key = normalize_key(e.get("image", ""))
        if key:
            existing[key] = e

    max_id = max((e.get("id", 0) for e in gallery), default=0)
    changed = False
    new_entries = []

    # scan actual image files
    files = sorted([p for p in IMAGES_DIR.iterdir() if p.is_file() and is_image_file(p)])
    print(f"Found {len(files)} image files in images/ (including thumbs).")

    for img in files:
        # skip files that are thumbs themselves
        if img.stem.lower().endswith(THUMB_SUFFIX.lstrip("-")):
            continue

        thumb = IMAGES_DIR / f"{img.stem}{THUMB_SUFFIX}.jpg"
        ok = create_thumbnail(img, thumb)
        if not ok:
            print(f"Skipping JSON update for {img.name} because thumbnail creation failed.")
            continue

        normalized = f"images/{img.name}"              # normalized lookup key (no leading ./)
        rel_image_to_store = f"./images/{img.name}"   # canonical stored format (keeps ./ like your examples)
        rel_thumb_to_store = f"./images/{thumb.name}"

        if normalized in existing:
            # preserve the entry; ensure thumbnail path exists in entry but DO NOT overwrite other fields
            ent = existing[normalized]
            if not ent.get("thumbnail"):
                ent["thumbnail"] = rel_thumb_to_store
                changed = True
                print(f"Updated thumbnail field for existing entry: {rel_image_to_store}")
            else:
                # If thumbnail differs but user edited it intentionally, don't force overwrite.
                if ent.get("thumbnail") != rel_thumb_to_store:
                    # Only set if current thumbnail points to a non-existing file (safety)
                    cur_thumb = Path(ent.get("thumbnail", "")[2:] if ent.get("thumbnail","").startswith("./") else ent.get("thumbnail",""))
                    if not cur_thumb.exists():
                        ent["thumbnail"] = rel_thumb_to_store
                        changed = True
                        print(f"Normalized/updated missing thumbnail for {rel_image_to_store}")
                    else:
                        print(f"Keeping user thumbnail for {rel_image_to_store} (different from generated).")
            # do not touch other metadata
        else:
            # add a new entry (preserves existing gallery list order by appending)
            max_id += 1
            new_ent = default_entry(img.name, max_id)
            new_ent["thumbnail"] = rel_thumb_to_store
            new_ent["image"] = rel_image_to_store
            new_entries.append(new_ent)
            changed = True
            print(f"Adding NEW gallery entry: {rel_image_to_store} (id={max_id})")

    if new_entries:
        gallery.extend(new_entries)

    if changed:
        # pretty print and atomic write
        pretty = json.dumps(gallery, indent=2, ensure_ascii=False)
        atomic_write(GALLERY_PATH, pretty)
        print(f"gallery.json updated (total entries={len(gallery)}).")
    else:
        print("No changes detected; not writing gallery.json.")

if __name__ == "__main__":
    main()
