import os
import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Set, Tuple

from lib.storage import read_wiki_notes, DATA_DIR, save_index, load_index

def extract_wikilinks(text: str) -> List[str]:
    """Extracts wikilinks in the form [[id]] from text."""
    pattern = r'\[\[(.*?)\]\]'
    matches = re.findall(pattern, text)
    return matches

def build_graph():
    notes = read_wiki_notes()
    
    nodes = []
    edges = []
    
    seen_edges: Set[Tuple[str, str]] = set()
    
    for note in notes:
        # Create node
        content_preview = note.body[:200] if note.body else ""
        nodes.append({
            "id": note.id,
            "label": note.summary,
            "para": note.para,
            "tags": note.tags,
            "summary": note.summary,
            "content_preview": content_preview,
            "group": note.para
        })
        
        # Collect links
        linked_ids = set(note.links)
        linked_ids.update(extract_wikilinks(note.body))
        
        for tgt in linked_ids:
            src, trg = min(note.id, tgt), max(note.id, tgt)
            if (src, trg) not in seen_edges:
                seen_edges.add((src, trg))
                edges.append({
                    "source": src,
                    "target": trg,
                    "weight": 1.0,
                    "type": "link"
                })
                
    # Prepare graph data
    graph_data = {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "node_count": len(nodes),
            "edge_count": len(edges)
        }
    }
    
    # Save graph.json
    graph_path = os.path.join(DATA_DIR, "graph.json")
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(graph_data, f, indent=2)
        
    print(f"Graph built successfully. {len(nodes)} nodes, {len(edges)} edges.")
    
    # Update index.json
    index = load_index()
    index["last_graph_build"] = graph_data["metadata"]["generated_at"]
    save_index(index)
    
if __name__ == "__main__":
    build_graph()
