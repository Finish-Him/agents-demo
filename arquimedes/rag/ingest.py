"""Ingest math-for-ML corpus into the Chroma vector store.

Usage::

    python -m arquimedes.rag.ingest                 # ingest seed corpus
    python -m arquimedes.rag.ingest --source docs/  # custom folder
    python -m arquimedes.rag.ingest --reset         # clear before ingest
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from langchain_core.documents import Document

from arquimedes.rag.chunking import chunk_documents
from arquimedes.rag.vector_store import get_vector_store, reset_vector_store_singleton


DEFAULT_SEED_DIR = Path("data/corpus")


def _load_markdown(path: Path) -> list[Document]:
    text = path.read_text(encoding="utf-8")
    topic = path.stem.replace("_primer", "")
    return [
        Document(
            page_content=text,
            metadata={
                "source": path.name,
                "topic": topic,
                "format": "markdown",
            },
        )
    ]


def _load_pdf(path: Path) -> list[Document]:
    from langchain_community.document_loaders import PyPDFLoader

    loader = PyPDFLoader(str(path))
    docs = loader.load()
    topic = path.stem
    for d in docs:
        d.metadata.setdefault("source", path.name)
        d.metadata.setdefault("topic", topic)
        d.metadata.setdefault("format", "pdf")
    return docs


def _load_dir(source_dir: Path) -> list[Document]:
    all_docs: list[Document] = []
    if not source_dir.exists():
        return all_docs
    for p in sorted(source_dir.rglob("*")):
        if p.suffix.lower() == ".md":
            all_docs.extend(_load_markdown(p))
        elif p.suffix.lower() == ".pdf":
            try:
                all_docs.extend(_load_pdf(p))
            except Exception as e:
                print(f"[skip] {p}: {e}")
    return all_docs


def ingest(source: str | os.PathLike = DEFAULT_SEED_DIR, reset: bool = False) -> int:
    """Ingest a source directory into Chroma. Returns the number of chunks."""
    if reset:
        # Nuke the whole vector store collection.
        from arquimedes.rag.config import CHROMA_PATH, COLLECTION
        vs = get_vector_store()
        try:
            vs.delete_collection()
        except Exception:
            pass
        reset_vector_store_singleton()

    docs = _load_dir(Path(source))
    if not docs:
        print(f"[ingest] no documents found in {source}")
        return 0

    chunks = chunk_documents(docs, strategy="latex_aware")
    vs = get_vector_store()
    vs.add_documents(chunks)
    print(f"[ingest] indexed {len(chunks)} chunks from {len(docs)} documents")
    return len(chunks)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(DEFAULT_SEED_DIR), help="File or folder")
    parser.add_argument("--reset", action="store_true", help="Wipe collection before ingest")
    args = parser.parse_args()
    ingest(args.source, reset=args.reset)


if __name__ == "__main__":
    main()
