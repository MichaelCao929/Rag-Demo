# Healthcare Document Q&A — RAG Pipeline

A Retrieval-Augmented Generation (RAG) pipeline for querying healthcare and compliance documents using natural language. Built with LangChain, ChromaDB, and Claude (Anthropic).

Four runnable entry points, from simple to advanced:

| Entry point | What it does |
|-------------|-------------|
| `query.py` | Simple RAG chain — LCEL retriever → Claude |
| `agent.py` | ReAct agent — native Anthropic tool_use loop |
| `mcp_server.py` | MCP Server — exposes tools to any MCP client |
| `backend/` + `frontend/` | **Full-stack web app** — React + FastAPI with streaming UI |
| `mcp_server.py` | MCP Server — exposes tools to any MCP-compatible client |

---

## Architecture

### Layer 1 — Simple RAG chain (`query.py`)

```
PDF documents
    ↓ PyPDFLoader
Raw text
    ↓ RecursiveCharacterTextSplitter (1000 tokens, 200 overlap)
Chunks
    ↓ HuggingFace all-MiniLM-L6-v2
Embeddings → ChromaDB (local)
    ↓ Similarity search (top-4)
Retrieved context
    ↓ Claude Haiku via LangChain LCEL chain
Cited answer
```

### Layer 2 — ReAct Tool-calling Agent (`agent.py`)

Uses Anthropic's native `tool_use` API directly (no LangChain agent abstraction). The reasoning loop is fully explicit:

```
User question
    ↓
Claude + tool schemas (TOOL_SCHEMAS from tools.py)
    ↓ stop_reason = "tool_use"
Execute tool(s) via TOOL_MAP
    ↓ tool_result blocks fed back
Claude reasons with new observations
    ↓ stop_reason = "end_turn"
Final cited answer
```

Tools available to the agent:

| Tool | Description |
|------|-------------|
| `search_documents(query)` | Similarity search, returns top-4 chunks with citations |
| `list_sources()` | Lists all indexed PDF files |
| `get_chunk_count()` | Returns total chunk count |
| `get_current_date()` | Returns current datetime |

Claude can call multiple tools in a single step (e.g., `list_sources` + `get_chunk_count` in parallel reasoning).

### Layer 3 — MCP Server (`mcp_server.py`)

Exposes the same four tools via the [Model Context Protocol](https://modelcontextprotocol.io) using [FastMCP](https://github.com/jlowin/fastmcp). Any MCP-compatible client (Claude Desktop, Cursor, Zed, custom agents) can connect and query the knowledge base without running any Python code directly.

```
MCP client (Claude Desktop / Cursor / custom agent)
    ↓ stdio transport
mcp_server.py (FastMCP)
    ↓
ChromaDB + Claude API
    ↓
Tool result → client
```

### Layer 4 — Full-stack Web App (`backend/` + `frontend/`)

A React + FastAPI web interface for the same RAG pipeline, with streaming responses and drag-and-drop PDF upload.

```
React + TypeScript (Vite)       ← frontend/
    ↕ HTTP + SSE (streaming)
FastAPI                          ← backend/main.py
    ↕
ChromaDB + AsyncAnthropic
    ↓
Streaming answer with citations → UI in real time
```

Features:
- **PDF upload** — drag & drop or click to index new documents
- **Streaming chat** — tokens stream to the UI in real time via Server-Sent Events
- **Source citations** — every answer shows which file and page it came from
- **Auto-suggestions** — empty state shows quick-start questions

---

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
# Edit .env and add: ANTHROPIC_API_KEY=sk-ant-...
```

---

## Usage

### Ingest documents

```bash
python ingest.py docs/clinical_guidelines.pdf docs/policy.pdf
```

### Simple RAG chain

```bash
python query.py
```

```
Question: What are the eligibility criteria for stem cell donation?
Answer: According to the guidelines (page 4), donors must be...
Sources:
  - clinical_guidelines.pdf (page 4)
```

### ReAct Agent

```bash
python agent.py
```

The agent runs three demo questions showing multi-tool reasoning:

```
Q: What documents are indexed and how many chunks total?
[Step 1] stop_reason=tool_use
  -> Tool: list_sources   Input: {}
  -> Tool: get_chunk_count   Input: {}
  <- Result: Indexed documents: ...

Final answer: The knowledge base contains 2 documents (87 chunks total)...
```

### MCP Server

```bash
python mcp_server.py
```

**Claude Desktop config** (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "rag-demo": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_server.py"]
    }
  }
}
```

Once connected, Claude Desktop can call `search_documents`, `list_sources`, `get_chunk_count`, and `get_current_date` directly.

### Web App

**Development (two terminals):**

```bash
# Terminal 1 — backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn backend.main:app --reload

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Upload a PDF from the sidebar, then ask questions.

**Production (Docker Compose):**

```bash
docker compose up --build
```

Open [http://localhost:5173](http://localhost:5173).

---

## File structure

```
rag-demo/
├── backend/
│   └── main.py            # FastAPI: /api/upload, /api/chat (SSE), /api/sources
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   └── components/
│   │       ├── Sidebar.tsx       # Document list + drag-and-drop upload
│   │       ├── ChatWindow.tsx    # Input + message feed
│   │       └── MessageBubble.tsx # User/assistant bubbles + source citations
│   └── ...
├── ingest.py              # CLI: PDF → ChromaDB ingestion
├── query.py               # CLI: simple LCEL RAG chain
├── tools.py               # Tool definitions (raw fns + @tool wrappers + TOOL_SCHEMAS)
├── agent.py               # CLI: Anthropic native ReAct tool_use loop
├── mcp_server.py          # MCP Server via FastMCP
├── docker-compose.yml
├── chroma_db/             # Persisted vector store (git-ignored)
├── docs/                  # Source PDFs
├── requirements.txt
└── .env                   # ANTHROPIC_API_KEY (git-ignored)
```

---

## Design decisions

- **Chunking:** `RecursiveCharacterTextSplitter` (1000 tokens, 200 overlap) preserves sentence boundaries while keeping context manageable.
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` runs locally — zero API cost at retrieval time.
- **Vector store:** ChromaDB persists to disk; no re-embedding needed across sessions.
- **Agent layer:** Anthropic SDK directly rather than LangChain agents — the `tool_use` loop is 30 lines and fully transparent. Easier to debug, extend, and reason about than framework abstractions.
- **MCP layer:** FastMCP adds one `@mcp.tool()` decorator per function — zero boilerplate. The server runs over stdio so any MCP client connects without network config.
- **Streaming:** FastAPI `StreamingResponse` with SSE + `AsyncAnthropic` client; the frontend reads chunks via `fetch` + `ReadableStream` — no WebSocket needed.
- **LLM:** Claude Haiku for cost-efficient answers; swap to `claude-sonnet-4-6` in `agent.py` / `backend/main.py` for harder reasoning tasks.

## Potential extensions

- Multi-tenant support (separate ChromaDB collections per user/project)
- Reranking with a cross-encoder for higher retrieval precision
- Evaluation framework (RAGAS) to measure retrieval and answer quality
- Auth layer (JWT) to protect the `/api/upload` endpoint
