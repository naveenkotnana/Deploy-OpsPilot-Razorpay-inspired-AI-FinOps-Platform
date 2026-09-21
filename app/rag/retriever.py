"""Retriever service wrapper."""
from app.rag.store import get_store


def get_retriever():
    """Retrieve and initialize the RAG knowledge index store."""
    return get_store()
