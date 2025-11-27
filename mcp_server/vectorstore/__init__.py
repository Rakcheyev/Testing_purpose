"""Vector store factory helpers for the MCP server."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from ..config import MCPConfig
from .base import VectorStore


@lru_cache(maxsize=1)
def _initialise_store() -> Optional[VectorStore]:
    if not getattr(MCPConfig, "RAG_ENABLED", False):
        return None
    backend = (getattr(MCPConfig, "VECTOR_BACKEND", "none") or "none").lower()
    if backend == "none":
        return None
    if backend == "chroma":
        from .chroma_backend import ChromaVectorStore

        return ChromaVectorStore(persist_path=getattr(MCPConfig, "CHROMA_PERSIST_PATH", None))
    raise ValueError(f"Unsupported vector backend: {backend}")


def get_vector_store() -> Optional[VectorStore]:
    """Return the configured vector store instance (or ``None`` if disabled)."""

    return _initialise_store()


def reset_vector_store_cache() -> None:
    """Clear the vector store cache — primarily useful in tests."""

    _initialise_store.cache_clear()


__all__ = ["get_vector_store", "reset_vector_store_cache", "VectorStore"]
