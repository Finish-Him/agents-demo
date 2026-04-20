"""Chunking strategies for math-heavy text.

Three strategies:

1. ``prose_splitter``: RecursiveCharacterTextSplitter tuned for textbook
   prose (paragraph -> line -> sentence -> word).
2. ``latex_aware_split``: protects LaTeX blocks (``$...$`` and
   ``\\begin{equation}...\\end{equation}``) from being cut mid-formula,
   then delegates to the prose splitter for everything else.
3. ``hierarchical_chunk``: yields parent (~2000 chars section) + child
   (~400 chars) pairs sharing a ``parent_id`` metadata, enabling
   ``ParentDocumentRetriever``-style retrieval.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Iterable

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from arquimedes.rag.config import CHUNK_OVERLAP, CHUNK_SIZE


prose_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)

# LaTeX block pattern — either $$...$$, $...$, or \begin{...}...\end{...}.
_LATEX_RE = re.compile(
    r"(\$\$.+?\$\$|\$[^$]+?\$|\\begin\{[^}]+\}.*?\\end\{[^}]+\})",
    re.DOTALL,
)


def _split_keeping_latex(text: str) -> list[tuple[str, bool]]:
    """Return alternating (chunk, is_latex) pairs without splitting formulas."""
    pieces: list[tuple[str, bool]] = []
    last = 0
    for match in _LATEX_RE.finditer(text):
        if match.start() > last:
            pieces.append((text[last : match.start()], False))
        pieces.append((match.group(0), True))
        last = match.end()
    if last < len(text):
        pieces.append((text[last:], False))
    return pieces


def latex_aware_split(text: str, metadata: dict | None = None) -> list[Document]:
    """Split text into chunks ~CHUNK_SIZE while keeping LaTeX blocks intact."""
    metadata = dict(metadata or {})
    chunks: list[Document] = []
    buf: list[str] = []
    buf_len = 0

    def flush():
        nonlocal buf, buf_len
        if buf:
            doc_text = "".join(buf).strip()
            if doc_text:
                chunks.append(Document(page_content=doc_text, metadata=dict(metadata)))
            buf = []
            buf_len = 0

    for piece, is_latex in _split_keeping_latex(text):
        if is_latex:
            # Formulas go in as a unit, even if bigger than CHUNK_SIZE.
            # Only flush when adding the formula would bust the budget
            # *and* the buffer already has meaningful prose around it.
            if buf_len + len(piece) > CHUNK_SIZE and buf_len > CHUNK_SIZE // 2:
                flush()
            buf.append(piece)
            buf_len += len(piece)
        else:
            for sub in prose_splitter.split_text(piece):
                if buf_len + len(sub) > CHUNK_SIZE and buf:
                    flush()
                buf.append(sub)
                buf_len += len(sub)
                if buf_len >= CHUNK_SIZE:
                    flush()
    flush()
    return chunks


@dataclass
class ParentChildChunks:
    parents: list[Document] = field(default_factory=list)
    children: list[Document] = field(default_factory=list)


def hierarchical_chunk(
    text: str,
    metadata: dict | None = None,
    parent_size: int = 2000,
    child_size: int = 400,
) -> ParentChildChunks:
    """Yield parent (section) + child (retrieval unit) chunks.

    Parents preserve enough surrounding context for the LLM; children are
    small enough for dense retrieval to hit relevant passages. Both share
    a ``parent_id``.
    """
    metadata = dict(metadata or {})
    parent_splitter = RecursiveCharacterTextSplitter(
        chunk_size=parent_size, chunk_overlap=parent_size // 8
    )
    child_splitter = RecursiveCharacterTextSplitter(
        chunk_size=child_size, chunk_overlap=child_size // 8
    )
    parents, children = [], []
    for parent_text in parent_splitter.split_text(text):
        parent_id = str(uuid.uuid4())
        parent_meta = {**metadata, "chunk_type": "parent", "parent_id": parent_id}
        parents.append(Document(page_content=parent_text, metadata=parent_meta))
        for child_text in child_splitter.split_text(parent_text):
            child_meta = {
                **metadata,
                "chunk_type": "child",
                "parent_id": parent_id,
            }
            children.append(Document(page_content=child_text, metadata=child_meta))
    return ParentChildChunks(parents=parents, children=children)


def chunk_documents(
    docs: Iterable[Document],
    strategy: str = "latex_aware",
) -> list[Document]:
    """Top-level entry point used by the ingestion script."""
    chunks: list[Document] = []
    for doc in docs:
        if strategy == "latex_aware":
            chunks.extend(latex_aware_split(doc.page_content, doc.metadata))
        elif strategy == "hierarchical":
            res = hierarchical_chunk(doc.page_content, doc.metadata)
            # Index children; parent text is kept under metadata for retrieval.
            chunks.extend(res.children)
        else:
            chunks.extend(prose_splitter.create_documents([doc.page_content], [doc.metadata]))
    return chunks
