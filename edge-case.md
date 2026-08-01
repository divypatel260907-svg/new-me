# Edge Cases and Corner Scenarios: SecondSelf

This document outlines potential edge cases, corner scenarios, and failure modes for the SecondSelf project, categorized by the pipeline phases described in the `architecture.md` and `Implementation-plan.md`.

## 1. Capture Pipeline (`capture.py`)
*   **Empty Input**: The user runs the capture command without providing any text or with only whitespace.
    *   *Mitigation*: Implement input validation to reject empty captures or prompt the user.
*   **Massive Inputs**: The user tries to capture a massive file (e.g., an entire book or a 100MB log file) which will later exceed LLM token limits.
    *   *Mitigation*: Implement a file size or character limit on the capture script, or truncate inputs with a warning.
*   **Unsupported File Types**: The user captures a binary file (e.g., an image or executable) expecting it to be processed as text.
    *   *Mitigation*: Restrict capture to supported text formats (.txt, .md) or implement basic mimetype checking before saving to `raw/`.
*   **Special Characters & Encoding Issues**: Inputs containing complex Unicode characters or emojis that might break standard file saving.
    *   *Mitigation*: Always force UTF-8 encoding when reading and writing files.

## 2. Classification (`classify.py`)
*   **LLM API Failures**: The Groq API is down, times out, or the user hits rate limits.
    *   *Mitigation*: Implement robust error handling, exponential backoff retries, and ensure the script doesn't crash mid-batch. Leave failed files in `raw/` for the next run.
*   **LLM Output Hallucination/Format Breaking**: The LLM fails to return the exact requested structure (e.g., returns conversational text instead of clean YAML frontmatter).
    *   *Mitigation*: Use strict system prompts, request JSON output if the API supports it (JSON mode), or write robust parsing logic (Regex) that can gracefully handle slight formatting deviations.
*   **Context Window Exceeded**: The captured text is too long for the LLaMA 3 context window.
    *   *Mitigation*: Truncate the text before sending it to the LLM (e.g., send only the first 4000 tokens for classification).

## 3. Auto-Linking (`link.py`)
*   **Zero or One Note**: Running the script when `wiki/` is empty or only has one note.
    *   *Mitigation*: Add a check to exit gracefully if `len(notes) < 2`.
*   **Threshold Tuning**: A static similarity threshold might result in either a fully connected graph (threshold too low) or no links at all (threshold too high).
    *   *Mitigation*: Experiment with a reasonable default (e.g., 0.70 for sentence-transformers). Consider dynamically adjusting the threshold based on the distribution of similarities, or keeping only the top-K links per node.
*   **Memory Exhaustion**: If the wiki grows to thousands of notes, computing the full $N \times N$ similarity matrix in memory might cause an Out-Of-Memory (OOM) error.
    *   *Mitigation*: For a prototype, this is unlikely. For scale, use a proper vector database (FAISS/Chroma) instead of an in-memory matrix.

## 4. Graph Generation & UI (`build_graph.py` & `app.py`)
*   **Graph Rendering Performance**: If the user has thousands of nodes, `vis-network` or `Cytoscape.js` will lag significantly and the browser might crash.
    *   *Mitigation*: Cap the number of rendered nodes in the UI, use clustering, or disable physics/force-direction after initial stabilization.
*   **Disconnected/Isolated Nodes**: Notes that have no similarity above the threshold to any other note.
    *   *Mitigation*: Ensure the graph library handles disconnected nodes gracefully without breaking the layout.
*   **Corrupted `graph.json`**: The file is partially written or malformed.
    *   *Mitigation*: The frontend should validate the JSON structure before attempting to render and display a user-friendly error if it fails.

## 5. The Oracle / Search (`ask.py`)
*   **Irrelevant Queries**: The user asks a question completely unrelated to anything in their second brain (e.g., "What is the weather?").
    *   *Mitigation*: The LLM prompt must explicitly state: "If the answer is not contained in the provided context, say 'I don't know based on your notes.'"
*   **Context Window Overflow during RAG**: The top-K retrieved notes are very long, and combining them exceeds the LLM's input limit.
    *   *Mitigation*: Dynamically calculate token counts. Add notes to the context only until a safe token limit is reached, discarding the rest.
*   **Retrieval Failure**: The embedding model retrieves technically similar but contextually useless notes.
    *   *Mitigation*: This is a fundamental limitation of basic RAG. Improving it requires better embedding models or hybrid search (keyword + semantic).
