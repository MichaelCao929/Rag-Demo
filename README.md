# Healthcare Document Q&A — RAG Pipeline

A Retrieval-Augmented Generation (RAG) pipeline for querying healthcare and compliance documents using natural language. Built with LangChain, ChromaDB, and Claude (Anthropic).

## Architecture

```
PDF documents
    ↓ PyPDFLoader
Raw text (pages)
    ↓ RecursiveCharacterTextSplitter (1000 tokens, 200 overlap)
Chunks
    ↓ HuggingFace sentence-transformers/all-MiniLM-L6-v2
Embeddings
    ↓ ChromaDB (local vector store)
Indexed store
    ↓ Similarity search (top-4 chunks)
Retrieved context
    ↓ Claude Haiku (claude-haiku-4-5) via LangChain RetrievalQA
Cited answer
```

## Setup

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your Anthropic API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Usage

```bash
# Ingest one or more PDFs into the vector store
python ingest.py docs/clinical_guidelines.pdf docs/policy.pdf

# Start the interactive Q&A REPL
python query.py
```

### Example session

```
Question: What are the eligibility criteria for stem cell donation?
Answer: According to the guidelines (page 4), donors must be...
Sources:
  - docs/clinical_guidelines.pdf (page 4)
```

## Design decisions

- **Chunking strategy:** `RecursiveCharacterTextSplitter` with 1000-token chunks and 200-token overlap preserves sentence boundaries while keeping context windows manageable.
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` runs locally with no API cost. Balances speed and retrieval quality for English documents.
- **Vector store:** ChromaDB persists to disk, making the indexed store reusable across sessions without re-embedding.
- **LLM:** Claude Haiku for cost-efficient answer generation; swap to `claude-sonnet-4-6` in `query.py` for higher-quality responses on complex documents.
- **Prompt:** Instructs the model to cite sources and acknowledge when the answer is not in context — critical for compliance-sensitive use cases.

## Potential extensions

- Flask/FastAPI REST endpoint for integration into web applications
- Multi-tenant support (separate ChromaDB collections per user/project)
- Streaming responses for real-time UI feedback
- Reranking with a cross-encoder to improve retrieval precision
- Evaluation framework (RAGAS) to measure retrieval and answer quality
