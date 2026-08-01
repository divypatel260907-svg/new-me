# Project Architecture: SecondSelf — Your Personal AI Second Brain

## 1. Overview
SecondSelf is an end-to-end personal AI second brain system. It allows users to capture information (notes, links, files) seamlessly, leverages AI to automatically organize (classify and link) this knowledge, visualizes the connections in an interactive graph, and provides a conversational interface to query the accumulated knowledge using Retrieval-Augmented Generation (RAG).

## 2. High-Level Architecture
The system is divided into an asynchronous data processing pipeline (ETL) and a synchronous serving application:
1. **Ingestion (Capture):** A simple interface/script to quickly save raw content.
2. **AI Processing Pipeline:** Scripts that process raw captures, extract metadata using an LLM, compute semantic embeddings, and establish relationships.
3. **Knowledge Graph Generation:** A process to convert the linked notes into a graph data structure.
4. **User Interface & Retrieval:** A Streamlit web application that renders the interactive graph and handles natural language queries by searching the embeddings and synthesizing answers via an LLM.

## 3. Component Details

### 3.1. Data Storage Layer
For simplicity and portability, the system relies on the local file system.
*   **`raw/`**: The landing zone for all captures. Files are stored with a timestamp and unique identifier (e.g., `YYYYMMDD_HHMMSS_UUID.txt`).
*   **`wiki/`**: The structured knowledge base. Contains Markdown files processed by the AI, enriched with YAML frontmatter (for PARA category, tags, and summary) and explicit linking.
*   **`graph.json`**: A static JSON file representing the nodes (notes) and edges (relationships) for frontend rendering.
*   **Embeddings Store**: A local vector store or simply serialized numpy arrays (e.g., `.npy` or `.pkl`) holding the vector representations of all notes in the `wiki/` for fast semantic search.

### 3.2. Processing Pipeline

#### A. The Archivist (`capture.py`)
*   **Role**: Ingestion.
*   **Functionality**: A CLI script that takes various inputs (raw text, URLs, file paths). It extracts the core text content and saves it as a new file in the `raw/` directory with a unique timestamped filename.

#### B. The Librarian (`classify.py` & `link.py`)
*   **`classify.py` (Auto-Classify)**:
    *   **Role**: Organization.
    *   **Functionality**: Iterates through unprocessed files in `raw/`. It sends the content to a fast LLM API (e.g., Groq running LLaMA 3) via a structured prompt to determine its PARA category, relevant tags, and a one-line summary. It then moves/saves the content into the `wiki/` folder, appending the LLM's output as YAML frontmatter.
*   **`link.py` (Auto-Link)**:
    *   **Role**: Relationship Discovery.
    *   **Functionality**: Uses a local embedding model (e.g., `sentence-transformers`) to generate vector embeddings for all notes in the `wiki/`. It computes cosine similarity across all note pairs. If the similarity exceeds a defined threshold, an edge/link is established between the two notes.

#### C. The Cartographer (`build_graph.py`)
*   **Role**: Data Modeling for UI.
*   **Functionality**: Scans the `wiki/` directory and the generated links. It constructs a graph data structure where notes are nodes (containing metadata like title/summary) and similarities are edges. This structure is exported to `graph.json`.

### 3.3. Serving Layer

#### D. The Oracle (`ask.py` & `app.py`)
*   **`ask.py` (Search Engine)**:
    *   **Role**: Retrieval-Augmented Generation (RAG).
    *   **Functionality**: Exposes an `ask(query)` function. It embeds the user's query, performs a vector similarity search against the note embeddings to retrieve the most relevant context, and constructs a prompt combining the query and the context. This is sent to the LLM to synthesize a definitive answer.
*   **`app.py` (User Interface)**:
    *   **Role**: Web Application.
    *   **Functionality**: A Streamlit application with two main views/components:
        1.  **Interactive Brain**: Loads `graph.json` and uses a JavaScript graph library (like `vis-network` or `Cytoscape.js` via Streamlit components) to render a force-directed, interactive graph (zoom, drag, hover).
        2.  **Search Bar**: A text input that interfaces with `ask.py`. It displays the synthesized AI answer along with the source notes used for context.

## 4. Technology Stack
*   **Core Language**: Python 3.10+
*   **Web Framework**: Streamlit
*   **LLM Provider**: Groq API (LLaMA 3 model) for fast, structured generation (classification) and synthesis (Q&A).
*   **Embeddings**: `sentence-transformers` (e.g., `all-MiniLM-L6-v2`) running locally for privacy and speed.
*   **Graph Visualization**: `streamlit-agraph` (wrapper for vis.js) or custom HTML/JS component.
*   **Data Handling**: Standard library (JSON, OS, re), PyYAML.

## 5. Deployment Architecture
*   **Hosting**: Streamlit Cloud or Hugging Face Spaces.
*   **Flow**: The codebase, including the generated `wiki/`, `graph.json`, and embeddings, is pushed to a GitHub repository. The deployment platform connects to the repository, installs dependencies from `requirements.txt`, and serves `app.py`. Updates to the knowledge base require running the pipeline locally and pushing the updated data files to the repository.
