"""
Query the indexed documents using Claude via a RAG chain.
Usage: python query.py
"""

import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

load_dotenv()

CHROMA_DIR = "./chroma_db"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CLAUDE_MODEL = "claude-haiku-4-5-20251001"
TOP_K = 4

PROMPT_TEMPLATE = """\
You are a helpful assistant answering questions based strictly on the provided documents.
If the answer is not in the context, say "I couldn't find that in the documents."
Always reference the source when drawing information from it.

Context:
{context}

Question: {question}

Answer:"""


def format_docs(docs: list) -> str:
    return "\n\n---\n\n".join(
        f"[Source: {d.metadata.get('source', 'unknown')}, page {d.metadata.get('page', '?')}]\n{d.page_content}"
        for d in docs
    )


def build_chain():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not set. Add it to your .env file."
        )

    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})

    llm = ChatAnthropic(
        model=CLAUDE_MODEL,
        api_key=api_key,
        max_tokens=1024,
    )

    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    # LCEL chain: retrieve → format → prompt → LLM → parse
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # Keep retriever accessible for source citation
    return chain, retriever


def run_repl(chain, retriever) -> None:
    print("Document Q&A ready. Type 'exit' to quit.\n")
    while True:
        try:
            question = input("Question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if question.lower() in ("exit", "quit", "q"):
            print("Goodbye.")
            break
        if not question:
            continue

        answer = chain.invoke(question)
        print(f"\nAnswer:\n{answer}")

        # Show sources separately
        source_docs = retriever.invoke(question)
        seen = set()
        sources = []
        for doc in source_docs:
            key = f"{doc.metadata.get('source', '?')}::{doc.metadata.get('page', '?')}"
            if key not in seen:
                sources.append(f"  - {doc.metadata.get('source', 'unknown')} (page {doc.metadata.get('page', '?')})")
                seen.add(key)
        print(f"\nSources:\n" + "\n".join(sources) + "\n")


if __name__ == "__main__":
    chain, retriever = build_chain()
    run_repl(chain, retriever)
