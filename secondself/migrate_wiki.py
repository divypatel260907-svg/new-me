"""
migrate_wiki.py — One-time migration script.

Converts old-format wiki notes (using 'category' key, no id/raw_id/created/links)
at the wiki/ root level into the canonical format and moves them into the correct
PARA subfolder (wiki/{para}/{id}.md).

Run once: python migrate_wiki.py
"""

import os
import re
import yaml
import shutil
from datetime import timezone
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WIKI_DIR = os.path.join(BASE_DIR, "wiki")

VALID_PARA = {"Projects", "Areas", "Resources", "Archives"}
# Map old category names → canonical PARA category
CATEGORY_MAP = {
    "projects": "Projects",
    "areas":    "Areas",
    "resources": "Resources",
    "archives": "Archives",
}


def migrate():
    migrated = 0
    skipped = 0

    for fname in os.listdir(WIKI_DIR):
        fpath = os.path.join(WIKI_DIR, fname)
        if not os.path.isfile(fpath) or not fname.endswith(".md"):
            continue  # Skip subdirs and non-.md files

        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"  [SKIP] Could not read {fname}: {e}")
            skipped += 1
            continue

        # Must start with frontmatter
        if not content.startswith("---"):
            print(f"  [SKIP] No frontmatter: {fname}")
            skipped += 1
            continue

        parts = content.split("---", 2)
        if len(parts) < 3:
            print(f"  [SKIP] Malformed frontmatter: {fname}")
            skipped += 1
            continue

        fm = yaml.safe_load(parts[1]) or {}
        body = parts[2].strip()

        # Already in new format (has 'id' and 'para')
        if "id" in fm and "para" in fm:
            print(f"  [SKIP] Already migrated: {fname}")
            skipped += 1
            continue

        # --- Build new frontmatter ---
        # Derive PARA from 'category'
        raw_category = fm.get("category", "Resources")
        para = CATEGORY_MAP.get(raw_category.lower(), "Resources")

        # Derive a short ID from the filename (strip date prefix if present)
        # Filename pattern: YYYYMMDD_HHMMSS_<shortid>.md
        name_stem = os.path.splitext(fname)[0]
        # Try to extract the hex suffix (last 8 hex chars after last underscore)
        hex_match = re.search(r"_([0-9a-f]{8})$", name_stem)
        if hex_match:
            note_id = hex_match.group(1)
        else:
            note_id = name_stem  # fallback: use whole stem

        # Derive created timestamp from filename if possible
        # Pattern: YYYYMMDD_HHMMSS_...
        ts_match = re.match(r"(\d{8})_(\d{6})", name_stem)
        if ts_match:
            date_part = ts_match.group(1)  # e.g. 20260709
            time_part = ts_match.group(2)  # e.g. 201155
            created = (
                f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                f"T{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}Z"
            )
        else:
            created = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        new_fm = {
            "id":      note_id,
            "raw_id":  name_stem,          # original filename stem as legacy raw_id
            "para":    para,
            "tags":    fm.get("tags", []),
            "summary": fm.get("summary", ""),
            "created": created,
            "links":   [],
        }

        new_fm_str = yaml.safe_dump(new_fm, default_flow_style=False, sort_keys=False)
        new_content = f"---\n{new_fm_str}---\n{body}\n"

        # Write into wiki/{para}/{id}.md
        dest_dir = os.path.join(WIKI_DIR, para)
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, f"{note_id}.md")

        # Avoid overwriting an existing canonical note
        if os.path.exists(dest_path):
            print(f"  [SKIP] Destination already exists: {dest_path}")
            skipped += 1
            continue

        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        # Remove old root-level file
        os.remove(fpath)

        print(f"  [OK] {fname} -> wiki/{para}/{note_id}.md")
        migrated += 1

    print(f"\nMigration complete: {migrated} migrated, {skipped} skipped.")


if __name__ == "__main__":
    migrate()
