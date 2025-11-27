"""Chroma-backed implementation of the :mod:`mcp_server.vectorstore` protocol."""

from __future__ import annotations

import uuid
from typing import Any, Dict, Iterable, List, Optional, Sequence


class ChromaVectorStore:
    """Adapter that maps the project VectorStore protocol to ChromaDB."""

    def __init__(self, persist_path: Optional[str] = None, client: Optional[Any] = None) -> None:
        if client is not None:
            self._client = client
        else:
            try:
                import chromadb
            except ImportError as exc:  # pragma: no cover - dependency guard
                raise RuntimeError(
                    "ChromaDB is not installed. Install it with 'pip install chromadb'."
                ) from exc
            if persist_path:
                self._client = chromadb.PersistentClient(path=persist_path)
            else:
                self._client = chromadb.Client()
        self._persist_path = persist_path

    def _get_collection(self, name: str):
        return self._client.get_or_create_collection(name)

    def index_documents(
        self,
        collection: str,
        documents: Sequence[str],
        metadatas: Optional[Sequence[Dict[str, Any]]] = None,
        ids: Optional[Sequence[str]] = None,
    ) -> None:
        if not documents:
            return
        doc_list = list(documents)
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in doc_list]
        id_list = list(ids)
        if metadatas is None:
            metadatas = [{} for _ in doc_list]
        metadata_list = list(metadatas)
        collection_ref = self._get_collection(collection)
        collection_ref.add(
            documents=doc_list,
            metadatas=metadata_list,
            ids=id_list,
        )

    def query(
        self,
        collection: str,
        text: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if top_k <= 0:
            return []
        collection_ref = self._get_collection(collection)
        response = collection_ref.query(
            query_texts=[text],
            n_results=top_k,
            where=filters or None,
        )
        documents = response.get("documents") or [[]]
        metadatas = response.get("metadatas") or [[]]
        ids = response.get("ids") or [[]]
        distances = response.get("distances") or [[]]
        results: List[Dict[str, Any]] = []
        for doc, meta, identifier, dist in zip(
            documents[0], metadatas[0], ids[0], distances[0]
        ):
            score = self._distance_to_score(dist)
            results.append(
                {
                    "id": identifier,
                    "document": doc,
                    "metadata": meta or {},
                    "score": score,
                    "distance": dist,
                }
            )
        return results

    @staticmethod
    def _distance_to_score(distance: Optional[float]) -> float:
        if distance is None:
            return 0.0
        try:
            return 1.0 / (1.0 + float(distance))
        except (TypeError, ValueError):
            return 0.0

    def delete_collection(self, collection: str) -> None:
        try:
            self._client.delete_collection(collection)
        except ValueError:
            # Collection did not exist — nothing to clean up.
            return

    def ping(self) -> bool:
        try:
            self._client.list_collections()
            return True
        except Exception:  # pragma: no cover - defensive
            return False


__all__ = ["ChromaVectorStore"]
