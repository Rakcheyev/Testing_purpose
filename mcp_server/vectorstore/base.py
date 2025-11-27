"""Vector store abstraction used by the MCP RAG helpers."""

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, Sequence, List


class VectorStore(Protocol):
    """Protocol describing the minimal vector store contract we rely on."""

    def index_documents(
        self,
        collection: str,
        documents: Sequence[str],
        metadatas: Optional[Sequence[Dict[str, Any]]] = None,
        ids: Optional[Sequence[str]] = None,
    ) -> None:
        """Persist a batch of documents inside ``collection``."""

    def query(
        self,
        collection: str,
        text: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Return the most relevant documents for ``text`` from ``collection``."""

    def delete_collection(self, collection: str) -> None:
        """Remove all records from ``collection`` (drop or truncate)."""

    def ping(self) -> bool:
        """Health-check hook used by the API before serving queries."""
