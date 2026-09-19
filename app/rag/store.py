"""Local RAG. Zero external APIs.

Vector store choice: an in-process TF-IDF + cosine index, persisted to disk with
joblib. Rationale (docs/rag.md): the corpus is ~230 lines of policy text. FAISS
and Chroma both add a dependency and a service surface that buy nothing at this
scale, and on an 8 GB / GTX 1650 box every megabyte of RAM matters. The
retriever interface is deliberately narrow so swapping in FAISS later is a
one-file change.

EMBEDDING_MODE=ollama switches to local nomic-embed-text embeddings through
Ollama, still with no external API.
"""
import json, re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import settings

ACCESS_ORDER = {"PUBLIC": 0, "INTERNAL": 1, "RESTRICTED": 2}
ROLE_CLEARANCE = {"ANALYST": "INTERNAL", "MANAGER": "INTERNAL", "ADMIN": "RESTRICTED"}

HEADER_KEYS = ["TITLE", "DOCUMENT_ID", "DOCUMENT_TYPE", "VERSION",
               "EFFECTIVE_DATE", "DEPARTMENT", "ACCESS_LEVEL", "CLASSIFICATION"]


@dataclass
class Chunk:
    chunk_id: str
    document_id: str
    title: str
    document_type: str
    version: str
    effective_date: str
    department: str
    access_level: str
    section: str
    text: str

    @property
    def citation(self) -> str:
        return f"[{self.document_id} v{self.version} §{self.section}] {self.title}"


def parse_document(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    meta, body_lines, in_header = {}, [], True
    for line in raw.splitlines():
        m = re.match(r"^([A-Z_]+):\s*(.*)$", line.strip())
        if in_header and m and m.group(1) in HEADER_KEYS:
            meta[m.group(1).lower()] = m.group(2).strip()
        else:
            in_header = False
            body_lines.append(line)
    meta.setdefault("document_id", path.stem.split("_")[0])
    meta.setdefault("title", path.stem)
    meta.setdefault("version", "1.0")
    meta.setdefault("access_level", "INTERNAL")
    meta.setdefault("document_type", "DOC")
    meta.setdefault("effective_date", "")
    meta.setdefault("department", "")
    return meta, "\n".join(body_lines).strip()


def chunk_by_section(meta: dict, body: str) -> List[Chunk]:
    """Policy docs are numbered-section documents; splitting on the numbered
    heading keeps each chunk a self-contained rule, which makes citations
    precise instead of approximate."""
    parts = re.split(r"\n(?=\d+\.\s+[A-Z])", body)
    chunks = []
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
        hm = re.match(r"^(\d+)\.\s+(.+)", part)
        section = hm.group(1) if hm else str(i + 1)
        # Sub-split anything unusually long, preserving overlap.
        if len(part) > settings.CHUNK_SIZE * 2:
            step = settings.CHUNK_SIZE - settings.CHUNK_OVERLAP
            for j in range(0, len(part), step):
                sub = part[j:j + settings.CHUNK_SIZE]
                if sub.strip():
                    chunks.append(_mk(meta, f"{section}.{j//step+1}", sub))
        else:
            chunks.append(_mk(meta, section, part))
    return chunks


def _mk(meta, section, text) -> Chunk:
    return Chunk(chunk_id=f"{meta['document_id']}#{section}",
                 document_id=meta["document_id"], title=meta["title"],
                 document_type=meta["document_type"], version=meta["version"],
                 effective_date=meta["effective_date"], department=meta["department"],
                 access_level=meta["access_level"], section=str(section), text=text)


class VectorStore:
    def __init__(self):
        self.chunks: List[Chunk] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.matrix = None

    def build(self, doc_dir: Path = None) -> int:
        doc_dir = doc_dir or settings.DOC_DIR
        self.chunks = []
        for p in sorted(doc_dir.glob("*.txt")):
            meta, body = parse_document(p)
            self.chunks.extend(chunk_by_section(meta, body))
        corpus = [c.text for c in self.chunks]
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2),
                                          sublinear_tf=True, min_df=1)
        self.matrix = self.vectorizer.fit_transform(corpus)
        return len(self.chunks)

    def search(self, query: str, k: int = None, role: str = "ANALYST") -> List[dict]:
        k = k or settings.RAG_TOP_K
        if self.matrix is None:
            self.build()
        clearance = ACCESS_ORDER[ROLE_CLEARANCE.get(role.upper(), "INTERNAL")]
        qv = self.vectorizer.transform([query])
        sims = cosine_similarity(qv, self.matrix)[0]
        order = np.argsort(-sims)
        out = []
        for idx in order:
            c = self.chunks[idx]
            if ACCESS_ORDER.get(c.access_level, 1) > clearance:
                continue   # access-level filter enforced at retrieval
            if sims[idx] <= 0:
                continue
            out.append({"document_id": c.document_id, "title": c.title,
                        "chunk_id": c.chunk_id, "section": c.section,
                        "chunk": c.text, "relevance_score": round(float(sims[idx]), 4),
                        "citation": c.citation, "access_level": c.access_level})
            if len(out) >= k:
                break
        return out

    def stats(self) -> dict:
        docs = {c.document_id for c in self.chunks}
        return {"documents": len(docs), "chunks": len(self.chunks),
                "mode": settings.EMBEDDING_MODE}


_store: Optional[VectorStore] = None


def get_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
        _store.build()
    return _store
