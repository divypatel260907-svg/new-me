# SecondSelf 🧠

SecondSelf is a personal knowledge management system designed to act as your extended brain. It allows you to effortlessly capture notes, automatically organize and link them using LLMs and embeddings, visualize connections in an interactive graph, and chat with your brain using Retrieval-Augmented Generation (RAG).

## Features

- **The Archivist (Capture)**: Quickly capture text notes, URLs, and files from the command line into your raw archive.
- **The Librarian (Process)**: Auto-classify unstructured notes into the P.A.R.A method (Projects, Areas, Resources, Archives), generate summaries and tags, and automatically link related concepts using dense text embeddings.
- **The Cartographer (Visualize)**: Generates a beautiful force-directed interactive knowledge graph of your connected thoughts.
- **The Oracle (Query)**: A local Streamlit application that allows you to ask questions in plain English and retrieve synthesized answers properly cited with sources from your own brain.

## Setup

1. **Clone the repository and prepare virtual environment:**
```bash
python -m venv .venv
source .venv/bin/activate  # Or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

2. **Configure Environment Variables:**
Copy `.env.example` to `.env` and add your Groq API key (used for classification and answer synthesis):
```env
GROQ_API_KEY="your-groq-api-key"
```

## Usage

### 1. Capture Knowledge

Use the `capture.py` CLI to ingest information:
```bash
python capture.py note "I want to transition to Machine Learning engineering by Q4."
python capture.py link "https://arxiv.org/abs/1706.03762"
python capture.py file ./documents/my_resume.pdf
```

### 2. Auto-Process and Link

Run the pipeline to organize and link all un-processed captures into your wiki:
```bash
python pipeline.py process
```
*(This triggers classification, embedding generation, linking, and graph rebuilding).*

### 3. Ask Your Brain

Run the Streamlit application to visually explore your graph and ask questions:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`. 

## Architecture

- **Backend / LLMs**: Uses `llama-3.1-8b-instant` via the Groq API for lightning-fast tagging, summarization, and RAG synthesis.
- **Embeddings**: Uses `sentence-transformers/all-MiniLM-L6-v2` to process local embeddings and discover non-obvious relationships.
- **Frontend**: Streamlit + `vis-network` for the interactive graph.
