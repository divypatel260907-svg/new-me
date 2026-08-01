import os
import re
import yaml
from typing import List

from lib.storage import read_wiki_notes, WIKI_DIR
from lib.embeddings import (
    embed_text,
    load_embeddings,
    save_embeddings,
    find_similar
)

SIMILARITY_THRESHOLD = 0.75


def build_embed_text(note) -> str:
    """Build a rich text representation for embedding: summary + tags + body."""
    parts = []
    if note.summary:
        parts.append(note.summary)
    if note.tags:
        parts.append(" ".join(note.tags))
    if note.body:
        # Use up to first 1000 chars of body for embedding
        parts.append(note.body[:1000])
    return "\n".join(parts)


def get_wiki_note_path(note) -> str:
    """Get the filesystem path of a wiki note."""
    return os.path.join(WIKI_DIR, note.para, f"{note.id}.md")


def rewrite_note_with_links(note_path: str, new_links: List[str]) -> None:
    """
    Read a wiki note .md file, update the frontmatter links[] field,
    and append [[wikilinks]] to the body (deduplicating existing ones).
    """
    with open(note_path, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---"):
        # Malformed note, skip
        return

    parts = content.split("---", 2)
    if len(parts) < 3:
        return

    frontmatter_str = parts[1]
    body = parts[2]

    # Parse existing frontmatter
    frontmatter = yaml.safe_load(frontmatter_str) or {}

    # Merge links (deduplicated)
    existing_links = frontmatter.get("links", []) or []
    merged_links = list(dict.fromkeys(existing_links + new_links))
    frontmatter["links"] = merged_links

    # Dump updated frontmatter
    new_frontmatter_str = yaml.safe_dump(frontmatter, default_flow_style=False, sort_keys=False)

    # Find existing wikilinks in body to deduplicate
    existing_wikilinks = set(re.findall(r"\[\[([^\]]+)\]\]", body))
    new_wikilink_strs = []
    for link_id in new_links:
        if link_id not in existing_wikilinks:
            new_wikilink_strs.append(f"[[{link_id}]]")

    # Append new wikilinks at bottom of body
    if new_wikilink_strs:
        body = body.rstrip() + "\n\n" + " ".join(new_wikilink_strs) + "\n"

    # Write updated file
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(f"---\n{new_frontmatter_str}---{body}")


def run_linking(threshold: float = SIMILARITY_THRESHOLD) -> None:
    """
    Main linking logic:
    1. Load all wiki notes.
    2. Load existing embeddings.
    3. Embed any new/missing notes.
    4. For each note, find similar notes above threshold.
    5. Update frontmatter links[] and append [[wikilinks]] in body.
    6. Save updated embeddings.
    """
    notes = read_wiki_notes()
    if len(notes) < 2:
        print(f"[LINK] Need at least 2 notes to link. Found {len(notes)}. Skipping.")
        return

    print(f"[LINK] Processing {len(notes)} wiki notes with threshold={threshold}...")

    # Load existing embeddings
    embeddings = load_embeddings()

    # Embed notes that don't have embeddings yet
    for note in notes:
        if note.id not in embeddings:
            print(f"  Embedding note: {note.id} ({note.para})")
            text = build_embed_text(note)
            embeddings[note.id] = embed_text(text)

    # Save updated embeddings
    save_embeddings(embeddings)
    print(f"[LINK] Embeddings saved ({len(embeddings)} total).")

    # Find and write links
    total_links = 0
    for note in notes:
        note_vec = embeddings[note.id]
        similar = find_similar(note.id, note_vec, embeddings, threshold=threshold)

        if similar:
            similar_ids = [sid for sid, _ in similar]
            note_path = get_wiki_note_path(note)

            if os.path.exists(note_path):
                rewrite_note_with_links(note_path, similar_ids)
                total_links += len(similar_ids)
                print(f"  Linked {note.id} -> {similar_ids}")

    print(f"[LINK] Done. {total_links} total link(s) written across {len(notes)} notes.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SecondSelf Auto-Linker")
    parser.add_argument(
        "--threshold", type=float, default=SIMILARITY_THRESHOLD,
        help=f"Cosine similarity threshold (default: {SIMILARITY_THRESHOLD})"
    )
    args = parser.parse_args()
    run_linking(threshold=args.threshold)
