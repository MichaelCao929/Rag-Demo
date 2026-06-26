"""
MCP Server — exposes the RAG knowledge base as MCP tools.

Any MCP-compatible client (Claude Desktop, Cursor, Zed, custom agents) can
connect to this server and call the same tools used by agent.py.

Run:
    python mcp_server.py

Claude Desktop config (~/.claude/claude_desktop_config.json):
    {
      "mcpServers": {
        "rag-demo": {
          "command": "python",
          "args": ["/absolute/path/to/mcp_server.py"]
        }
      }
    }
"""

import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_DIR = "./chroma_db"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

mcp = FastMCP("RAG Knowledge Base")


def _vectorstore() -> Chroma:
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    return Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)


@mcp.tool()
def search_documents(query: str) -> str:
    """Search the knowledge base for information relevant to the query.
    Returns top matching document excerpts with source citations."""
    vs = _vectorstore()
    docs = vs.similarity_search(query, k=4)
    if not docs:
        return "No relevant documents found."
    parts = []
    for i, doc in enumerate(docs, 1):
        source = os.path.basename(doc.metadata.get("source", "unknown"))
        page = doc.metadata.get("page", "?")
        parts.append(f"[{i}] {source} (page {page})\n{doc.page_content.strip()}")
    return "\n\n---\n\n".join(parts)


@mcp.tool()
def list_sources() -> str:
    """List all unique document files indexed in the knowledge base."""
    vs = _vectorstore()
    data = vs.get()
    sources = sorted({
        os.path.basename(m.get("source", "unknown"))
        for m in data["metadatas"]
    })
    if not sources:
        return "Knowledge base is empty. Run ingest.py first."
    return "Indexed documents:\n" + "\n".join(f"  - {s}" for s in sources)


@mcp.tool()
def get_chunk_count() -> str:
    """Return the total number of text chunks stored in the knowledge base."""
    vs = _vectorstore()
    count = len(vs.get()["ids"])
    return f"Knowledge base contains {count} text chunks."


@mcp.tool()
def get_current_date() -> str:
    """Return the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    mcp.run()
