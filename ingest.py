"""
Ingest PDFs into ChromaDB vector store.
Usage: python ingest.py <pdf_path> [pdf_path ...]
"""

import sys
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

CHROMA_DIR = "./chroma_db"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def ingest(pdf_paths: list[str]) -> int:
    documents = []
    for path in pdf_paths:
        if not Path(path).exists():
            print(f"File not found: {path}")
            sys.exit(1)
        loader = PyPDFLoader(path)
        docs = loader.load()
        documents.extend(docs)
        print(f"  Loaded {len(docs)} pages from {path}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documents)
    print(f"\nSplit into {len(chunks)} chunks")

    print("Generating embeddings (first run downloads ~90MB model)...")
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
    )
    print(f"Stored in ChromaDB at {CHROMA_DIR}")
    return len(chunks)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <pdf1> [pdf2 ...]")
        sys.exit(1)
    total = ingest(sys.argv[1:])
    print(f"\nDone. {total} chunks indexed and ready to query.")
