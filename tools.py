"""
Tool definitions for the RAG agent.

Each public function is also wrapped with @tool for LangChain / MCP compatibility.
The underlying _*_raw functions can be imported directly by agent.py.
"""

import os
from datetime import datetime
from langchain_core.tools import tool
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_DIR = "./chroma_db"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _vectorstore() -> Chroma:
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    return Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)


# ── Raw implementations (importable without LangChain overhead) ────────────

def search_documents_raw(query: str) -> str:
    vs = _vectorstore()
    docs = vs.similarity_search(query, k=4)
    if not docs:
        return "No relevant documents found in the knowledge base."
    parts = []
    for i, doc in enumerate(docs, 1):
        source = os.path.basename(doc.metadata.get("source", "unknown"))
        page = doc.metadata.get("page", "?")
        parts.append(f"[{i}] {source} (page {page})\n{doc.page_content.strip()}")
    return "\n\n---\n\n".join(parts)


def list_sources_raw() -> str:
    vs = _vectorstore()
    data = vs.get()
    sources = sorted({
        os.path.basename(m.get("source", "unknown"))
        for m in data["metadatas"]
    })
    if not sources:
        return "The knowledge base is empty. Run ingest.py first."
    return "Indexed documents:\n" + "\n".join(f"  - {s}" for s in sources)


def get_chunk_count_raw() -> str:
    vs = _vectorstore()
    count = len(vs.get()["ids"])
    return f"The knowledge base contains {count} text chunks."


def get_current_date_raw() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ── LangChain @tool wrappers (used by mcp_server.py and LangChain chains) ──

@tool
def search_documents(query: str) -> str:
    """Search the knowledge base for information relevant to the query.
    Returns the top matching document excerpts with source file citations.
    Use this tool whenever you need to answer a factual question from the documents."""
    return search_documents_raw(query)


@tool
def list_sources() -> str:
    """List all unique document files currently indexed in the knowledge base.
    Use this to understand what documents are available before searching."""
    return list_sources_raw()


@tool
def get_chunk_count() -> str:
    """Return the total number of text chunks stored in the knowledge base."""
    return get_chunk_count_raw()


@tool
def get_current_date() -> str:
    """Return the current date and time."""
    return get_current_date_raw()


# ── Tool dispatch map (used by agent.py's native Anthropic loop) ───────────

TOOL_MAP = {
    "search_documents": lambda args: search_documents_raw(args["query"]),
    "list_sources":     lambda args: list_sources_raw(),
    "get_chunk_count":  lambda args: get_chunk_count_raw(),
    "get_current_date": lambda args: get_current_date_raw(),
}

# ── Anthropic tool schemas (JSON Schema format for tool_use API) ───────────

TOOL_SCHEMAS = [
    {
        "name": "search_documents",
        "description": (
            "Search the knowledge base for information relevant to a query. "
            "Returns top matching document excerpts with source citations."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up in the knowledge base.",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "list_sources",
        "description": "List all unique document files currently indexed in the knowledge base.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_chunk_count",
        "description": "Return the total number of text chunks stored in the knowledge base.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_current_date",
        "description": "Return the current date and time.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]
