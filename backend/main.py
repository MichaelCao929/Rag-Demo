import json
import os
import shutil
import tempfile
from functools import lru_cache

from anthropic import AsyncAnthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel

load_dotenv()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DIR = os.path.join(ROOT, "chroma_db")
DOCS_DIR = os.path.join(ROOT, "docs")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

SYSTEM_PROMPT = (
    "You are a research assistant answering questions from a private document knowledge base. "
    "Base your answer only on the provided context. "
    "Cite sources using [1], [2], etc. "
    "If the answer isn't in the context, clearly say so — do not guess."
)

app = FastAPI(title="RAG Knowledge Base API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = AsyncAnthropic()


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBED_MODEL)


def get_vectorstore() -> Chroma:
    return Chroma(persist_directory=CHROMA_DIR, embedding_function=get_embeddings())


def list_indexed_docs() -> list[str]:
    try:
        data = get_vectorstore().get()
        return sorted({
            os.path.basename(m.get("source", "unknown"))
            for m in data["metadatas"]
            if m
        })
    except Exception:
        return []


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/api/sources")
async def sources():
    try:
        data = get_vectorstore().get()
        docs = sorted({
            os.path.basename(m.get("source", "unknown"))
            for m in data["metadatas"] if m
        })
        chunk_count = len(data["ids"])
    except Exception:
        docs, chunk_count = [], 0
    return {"documents": docs, "count": len(docs), "chunk_count": chunk_count}


@app.delete("/api/sources/{filename}")
async def delete_source(filename: str):
    vs = get_vectorstore()
    result = vs.get(where={"source": {"$contains": filename}})
    if not result["ids"]:
        raise HTTPException(status_code=404, detail=f"No chunks found for '{filename}'.")
    vs.delete(ids=result["ids"])
    return {"filename": filename, "deleted_chunks": len(result["ids"])}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    os.makedirs(DOCS_DIR, exist_ok=True)
    dest = os.path.join(DOCS_DIR, file.filename)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        shutil.move(tmp_path, dest)
        loader = PyPDFLoader(dest)
        pages = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(pages)
        vs = get_vectorstore()
        vs.add_documents(chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"filename": file.filename, "pages": len(pages), "chunks": len(chunks)}


class ChatRequest(BaseModel):
    question: str


@app.post("/api/chat")
async def chat(body: ChatRequest):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    vs = get_vectorstore()
    docs = vs.similarity_search(question, k=4)

    sources = []
    context_parts = []
    for i, doc in enumerate(docs, 1):
        fname = os.path.basename(doc.metadata.get("source", "unknown"))
        page = doc.metadata.get("page", "?")
        chunk_text = doc.page_content.strip()
        sources.append({"file": fname, "page": page, "text": chunk_text[:400]})
        context_parts.append(f"[{i}] {fname} (page {page})\n{chunk_text}")

    context = "\n\n---\n\n".join(context_parts) if context_parts else "No documents are indexed yet."

    async def generate():
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"

        async with client.messages.stream(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}",
            }],
        ) as stream:
            async for text in stream.text_stream:
                yield f"data: {json.dumps({'type': 'text', 'text': text})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Serve built frontend in production ────────────────────────────────────────
frontend_dist = os.path.join(ROOT, "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
