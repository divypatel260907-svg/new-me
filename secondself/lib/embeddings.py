import os
import pickle
import numpy as np
from typing import List, Dict, Optional, Tuple

# Lazy import so the model only loads when first needed
_model = None

MODEL_NAME = "all-MiniLM-L6-v2"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMBEDDINGS_PATH = os.path.join(BASE_DIR, "data", "embeddings.pkl")


def load_model():
    """Load the sentence-transformers model (cached in module-level var)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print(f"[EMBEDDINGS] Loading model '{MODEL_NAME}'... (first run may be slow)")
        _model = SentenceTransformer(MODEL_NAME)
        print("[EMBEDDINGS] Model loaded.")
    return _model


def embed_text(text: str) -> np.ndarray:
    """Embed a single text string into a 384-dim vector."""
    model = load_model()
    return model.encode(text, convert_to_numpy=True)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def load_embeddings() -> Dict[str, np.ndarray]:
    """Load embeddings dict {note_id: vector} from data/embeddings.pkl."""
    if not os.path.exists(EMBEDDINGS_PATH):
        return {}
    with open(EMBEDDINGS_PATH, "rb") as f:
        return pickle.load(f)


def save_embeddings(embeddings: Dict[str, np.ndarray]) -> None:
    """Save embeddings dict {note_id: vector} to data/embeddings.pkl."""
    os.makedirs(os.path.dirname(EMBEDDINGS_PATH), exist_ok=True)
    with open(EMBEDDINGS_PATH, "wb") as f:
        pickle.dump(embeddings, f)


def find_similar(
    note_id: str,
    note_vector: np.ndarray,
    all_embeddings: Dict[str, np.ndarray],
    threshold: float = 0.75,
    top_k: int = 10
) -> List[Tuple[str, float]]:
    """
    Compare note_vector against all_embeddings, returning a list of
    (other_id, score) pairs where score >= threshold, excluding self.
    Sorted by score descending, limited to top_k results.
    """
    scores = []
    for other_id, other_vec in all_embeddings.items():
        if other_id == note_id:
            continue
        score = cosine_similarity(note_vector, other_vec)
        if score >= threshold:
            scores.append((other_id, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]
