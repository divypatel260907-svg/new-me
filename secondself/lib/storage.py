import os
import uuid
import json
import yaml
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

from lib.models import CaptureMetadata, WikiNote

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "raw")
WIKI_DIR = os.path.join(BASE_DIR, "wiki")
DATA_DIR = os.path.join(BASE_DIR, "data")
INDEX_PATH = os.path.join(DATA_DIR, "index.json")

def generate_capture_id() -> str:
    """Generates an ID in the format YYYY-MM-DD_uuid8."""
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    unique_suffix = uuid.uuid4().hex[:8]
    return f"{date_str}_{unique_suffix}"

def content_hash(data: str) -> str:
    """Computes SHA-256 hash of a string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def load_index() -> Dict[str, Any]:
    """Loads index.json. If it does not exist, returns initial state."""
    if not os.path.exists(INDEX_PATH):
        os.makedirs(DATA_DIR, exist_ok=True)
        initial_index = {
            "raw_processed": {},
            "embeddings_version": "all-MiniLM-L6-v2",
            "last_graph_build": None
        }
        save_index(initial_index)
        return initial_index
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_index(index_data: Dict[str, Any]) -> None:
    """Saves index.json."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2)

def write_raw_capture(meta: CaptureMetadata, content: str) -> str:
    """Creates a raw/{id}/ folder and writes meta.json and content.*"""
    os.makedirs(RAW_DIR, exist_ok=True)
    capture_dir = os.path.join(RAW_DIR, meta.id)
    os.makedirs(capture_dir, exist_ok=True)
    
    # Save meta.json
    meta_path = os.path.join(capture_dir, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta.to_dict(), f, indent=2)
        
    # Save content file
    ext = "txt"
    if meta.type == "note":
        ext = "md"
    elif meta.type == "link":
        ext = "html"
    elif meta.original_filename:
        _, file_ext = os.path.splitext(meta.original_filename)
        if file_ext:
            ext = file_ext.lstrip(".")
            
    content_filename = f"content.{ext}"
    content_path = os.path.join(capture_dir, content_filename)
    
    # Write content as string or bytes depending on source
    # For text/links, we write string.
    with open(content_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return capture_dir

def read_raw_captures() -> List[Dict[str, Any]]:
    """Lists all unprocessed raw items."""
    if not os.path.exists(RAW_DIR):
        return []
    
    captures = []
    index = load_index()
    processed = index.get("raw_processed", {})
    
    for item in os.listdir(RAW_DIR):
        item_path = os.path.join(RAW_DIR, item)
        if os.path.isdir(item_path) and item not in processed:
            meta_path = os.path.join(item_path, "meta.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta_dict = json.load(f)
                    
                # Find content file
                content_file = None
                for f in os.listdir(item_path):
                    if f.startswith("content."):
                        content_file = f
                        break
                
                captures.append({
                    "meta": CaptureMetadata.from_dict(meta_dict),
                    "content_file": content_file,
                    "dir_path": item_path
                })
    return captures

def write_wiki_note(note: WikiNote) -> str:
    """Writes wiki/{para}/{id}.md with YAML frontmatter."""
    para_dir = os.path.join(WIKI_DIR, note.para)
    os.makedirs(para_dir, exist_ok=True)
    
    frontmatter = {
        "id": note.id,
        "raw_id": note.raw_id,
        "para": note.para,
        "tags": note.tags,
        "summary": note.summary,
        "created": note.created,
        "links": note.links
    }
    
    frontmatter_str = yaml.safe_dump(frontmatter, default_flow_style=False, sort_keys=False)
    wiki_content = f"---\n{frontmatter_str}---\n{note.body}"
    
    note_path = os.path.join(para_dir, f"{note.id}.md")
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(wiki_content)
        
    return note_path

def read_wiki_notes() -> List[WikiNote]:
    """Parses all wiki markdown files."""
    notes = []
    if not os.path.exists(WIKI_DIR):
        return []
        
    for root, _, files in os.walk(WIKI_DIR):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read()
                    
                    if text.startswith("---"):
                        parts = text.split("---", 2)
                        if len(parts) >= 3:
                            frontmatter = yaml.safe_load(parts[1])
                            body = parts[2].strip()
                            
                            notes.append(WikiNote(
                                id=frontmatter["id"],
                                raw_id=frontmatter["raw_id"],
                                para=frontmatter["para"],
                                tags=frontmatter.get("tags", []),
                                summary=frontmatter.get("summary", ""),
                                created=frontmatter["created"],
                                links=frontmatter.get("links", []),
                                body=body
                            ))
                except Exception as e:
                    print(f"Error parsing wiki note {file}: {e}")
    return notes

# Extraction Helpers
def extract_text_from_note(content_path: str) -> str:
    with open(content_path, "r", encoding="utf-8") as f:
        return f.read()

def extract_text_from_link(content_path: str, url: str) -> str:
    try:
        with open(content_path, "r", encoding="utf-8") as f:
            html = f.read()
        
        # If file is failed download
        if html.strip() == "Failed to fetch content.":
            return f"Link: {url}\n\nFailed to fetch content."
            
        soup = BeautifulSoup(html, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
            
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = "\n".join(chunk for chunk in chunks if chunk)
        
        title = soup.title.string if soup.title else "No Title"
        return f"URL: {url}\nTitle: {title}\n\n{text}"
    except Exception as e:
        print(f"Failed parsing downloaded HTML, fallback to URL: {e}")
        return f"URL: {url}"

def extract_text_from_pdf(content_path: str, filename: str) -> str:
    try:
        reader = PdfReader(content_path)
        text_list = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text_list.append(t)
        
        extracted_text = "\n".join(text_list).strip()
        if not extracted_text:
            return f"File: {filename}\n[Empty PDF / Image-only PDF]"
        return f"File: {filename}\n\n{extracted_text}"
    except Exception as e:
        print(f"Failed parsing PDF: {e}")
        return f"File: {filename}"
