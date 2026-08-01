import os
import sys
from datetime import datetime, timezone

from lib.models import WikiNote
from lib.storage import (
    load_index,
    save_index,
    read_raw_captures,
    write_wiki_note,
    extract_text_from_note,
    extract_text_from_link,
    extract_text_from_pdf
)
from lib.llm import classify_content

def run_classification():
    index = load_index()
    raw_processed = index.setdefault("raw_processed", {})
    
    unprocessed_captures = read_raw_captures()
    if not unprocessed_captures:
        print("No new raw captures to process.")
        return
        
    print(f"Found {len(unprocessed_captures)} new captures to process.")
    
    for capture in unprocessed_captures:
        meta = capture["meta"]
        raw_id = meta.id
        content_file = capture["content_file"]
        dir_path = capture["dir_path"]
        
        if not content_file:
            print(f"[WARNING] No content file found in {dir_path}. Skipping.")
            continue
            
        content_path = os.path.join(dir_path, content_file)
        print(f"Processing capture {raw_id} (Type: {meta.type})...")
        
        # 1. Extract text based on type
        extracted_text = ""
        if meta.type == "note":
            extracted_text = extract_text_from_note(content_path)
        elif meta.type == "link":
            extracted_text = extract_text_from_link(content_path, meta.source)
        elif meta.type == "file":
            _, ext = os.path.splitext(content_file)
            if ext.lower() == ".pdf":
                extracted_text = extract_text_from_pdf(content_path, meta.original_filename or content_file)
            else:
                # Fallback to plain reading
                try:
                    with open(content_path, "r", encoding="utf-8") as f:
                        extracted_text = f.read()
                except Exception:
                    extracted_text = f"File: {meta.original_filename or content_file}"
                    
        # 2. Classify content using LLM
        try:
            classification = classify_content(extracted_text)
            
            # Extract short ID from raw_id
            # raw_id is YYYY-MM-DD_shortid. Short ID is the suffix.
            short_id = raw_id.split("_")[-1] if "_" in raw_id else raw_id
            
            # 3. Create WikiNote
            note = WikiNote(
                id=short_id,
                raw_id=raw_id,
                para=classification["para"],
                tags=classification.get("tags", []),
                summary=classification.get("summary", ""),
                created=meta.timestamp,
                links=[],
                body=extracted_text
            )
            
            # 4. Write wiki note
            write_wiki_note(note)
            
            # 5. Update index
            raw_processed[raw_id] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            save_index(index)
            
            print(f"[SUCCESS] Classified and saved to wiki/{note.para}/{note.id}.md")
            
        except Exception as e:
            print(f"[ERROR] Failed to classify capture {raw_id}: {e}")

if __name__ == "__main__":
    run_classification()
