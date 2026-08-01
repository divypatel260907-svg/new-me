import os
import sys
import argparse
import shutil
from datetime import datetime, timezone

from lib.models import CaptureMetadata, CaptureResult
from lib.storage import (
    generate_capture_id,
    content_hash,
    write_raw_capture,
    load_index,
    RAW_DIR
)
import requests

def capture_note(text: str) -> CaptureResult:
    if not text.strip():
        print("[ERROR] Empty note text. Capture rejected.")
        sys.exit(1)
        
    cap_id = generate_capture_id()
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    h = content_hash(text)
    
    # Check duplicates across existing raw directories (optional warning)
    # We will warn if the hash matches any existing note.
    check_duplicates(h)
    
    meta = CaptureMetadata(
        id=cap_id,
        timestamp=timestamp,
        type="note",
        source="cli",
        content_hash=h
    )
    
    path = write_raw_capture(meta, text)
    print(f"Captured -> {os.path.relpath(path, os.getcwd())}")
    return CaptureResult(id=cap_id, path=path, type="note")

def capture_link(url: str, notes: str = "") -> CaptureResult:
    cap_id = generate_capture_id()
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    # Attempt to fetch content
    content = "Failed to fetch content."
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        content = response.text
    except Exception as e:
        print(f"[WARNING] Failed to fetch URL content. Saving link only. ({e})")
        
    if notes:
        # Prepend notes to the html or store it (we can append to content)
        content = f"<!-- Notes: {notes} -->\n" + content
        
    h = content_hash(content)
    check_duplicates(h)
    
    meta = CaptureMetadata(
        id=cap_id,
        timestamp=timestamp,
        type="link",
        source=url,
        content_hash=h
    )
    
    path = write_raw_capture(meta, content)
    print(f"Captured -> {os.path.relpath(path, os.getcwd())}")
    return CaptureResult(id=cap_id, path=path, type="link")

def capture_file(path: str) -> CaptureResult:
    if not os.path.exists(path):
        print(f"[ERROR] File does not exist: {path}")
        sys.exit(1)
        
    filename = os.path.basename(path)
    cap_id = generate_capture_id()
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    
    # If it's a binary file or PDF, we copy it.
    # To determine if it's text or binary, let's try reading as utf-8 or copy directly.
    is_binary = False
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        is_binary = True
        
    if is_binary:
        # For binary files, read as bytes
        with open(path, "rb") as f:
            bytes_content = f.read()
        h = hashlib.sha256(bytes_content).hexdigest() if 'hashlib' in globals() else content_hash(filename)
        # Note: we need content_hash for bytes.
        import hashlib
        h = hashlib.sha256(bytes_content).hexdigest()
    else:
        h = content_hash(content)
        
    check_duplicates(h)
    
    meta = CaptureMetadata(
        id=cap_id,
        timestamp=timestamp,
        type="file",
        source="local",
        original_filename=filename,
        content_hash=h
    )
    
    # Write metadata and content
    os.makedirs(RAW_DIR, exist_ok=True)
    capture_dir = os.path.join(RAW_DIR, cap_id)
    os.makedirs(capture_dir, exist_ok=True)
    
    # Write meta.json
    import json
    meta_path = os.path.join(capture_dir, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta.to_dict(), f, indent=2)
        
    # Copy file content
    dest_path = os.path.join(capture_dir, f"content{os.path.splitext(filename)[1]}")
    shutil.copy(path, dest_path)
    
    print(f"Captured -> {os.path.relpath(capture_dir, os.getcwd())}")
    return CaptureResult(id=cap_id, path=capture_dir, type="file")

def check_duplicates(h: str) -> None:
    """Warns if content_hash already exists in the raw/ folder."""
    if not os.path.exists(RAW_DIR):
        return
    for item in os.listdir(RAW_DIR):
        item_path = os.path.join(RAW_DIR, item)
        if os.path.isdir(item_path):
            meta_path = os.path.join(item_path, "meta.json")
            if os.path.exists(meta_path):
                try:
                    import json
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta_dict = json.load(f)
                    if meta_dict.get("content_hash") == h:
                        print("[WARNING] Duplicate content detected (matching hash). continuing capture.")
                        return
                except Exception:
                    pass

def run_interactive():
    print("SecondSelf Interactive Capture Mode. Press Ctrl+C to exit.")
    try:
        while True:
            text = input("Note > ").strip()
            if text:
                capture_note(text)
    except KeyboardInterrupt:
        print("\nExited interactive mode.")

def main():
    parser = argparse.ArgumentParser(description="SecondSelf Ingestion Pipeline (The Archivist)")
    subparsers = parser.add_subparsers(dest="command", help="Capture command")
    
    # note parser
    note_parser = subparsers.add_parser("note", help="Capture a text note")
    note_parser.add_argument("text", type=str, help="Text content of the note")
    
    # link parser
    link_parser = subparsers.add_parser("link", help="Capture a URL link")
    link_parser.add_argument("url", type=str, help="URL to capture")
    link_parser.add_argument("--notes", type=str, default="", help="Optional notes on the link")
    
    # file parser
    file_parser = subparsers.add_parser("file", help="Capture a local file")
    file_parser.add_argument("path", type=str, help="Path to the local file")
    
    args = parser.parse_args()
    
    if args.command == "note":
        capture_note(args.text)
    elif args.command == "link":
        capture_link(args.url, args.notes)
    elif args.command == "file":
        capture_file(args.path)
    else:
        # Interactive stdin mode
        run_interactive()

if __name__ == "__main__":
    main()
