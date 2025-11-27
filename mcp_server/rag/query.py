"""Query helpers that retrieve contextual snippets from the vector store."""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence

from ..config import MCPConfig
from ..vectorstore import VectorStore


def retrieve_context(
    store: Optional[VectorStore],
    query: str,
    domain: Optional[str] = None,
    subdomain: Optional[str] = None,
    tags: Optional[Sequence[str]] = None,
    n: Optional[int] = None,
) -> List[Dict[str, object]]:
    """Generic retrieval helper that spans the configured collections."""

    if store is None or not query:
        return []
    top_k = n or getattr(MCPConfig, "RAG_TOP_K", 5)
    resource_filter = _canonical_resource(domain)
    filters: Dict[str, str] = {}
    if resource_filter:
        filters["resource"] = resource_filter
    if subdomain:
        filters["subdomain"] = subdomain.lower()
    collections = _collections_for_resource(resource_filter)
    aggregated: List[Dict[str, object]] = []
    for collection in collections:
        try:
            results = store.query(collection, query, top_k=top_k, filters=filters or None)
        except Exception:
            continue
        for item in results:
            if tags and not _metadata_has_tags(item.get("metadata"), tags):
                continue
            enriched = {
                "collection": collection,
                "id": item.get("id"),
                "document": item.get("document"),
                "metadata": item.get("metadata", {}),
                "score": item.get("score"),
            }
            aggregated.append(enriched)
    aggregated.sort(key=lambda entry: entry.get("score") or 0.0, reverse=True)
    return aggregated[:top_k]


def retrieve_pbi_context(
    store: Optional[VectorStore], query: str, domain: Optional[str] = None, **kwargs
) -> List[Dict[str, object]]:
    return retrieve_context(store, query, domain or "pbip", **kwargs)


def retrieve_pbip_context(
    store: Optional[VectorStore], query: str, domain: Optional[str] = None, **kwargs
) -> List[Dict[str, object]]:
    return retrieve_context(store, query, domain or "pbip", **kwargs)


def retrieve_sql_context(
    store: Optional[VectorStore], query: str, domain: Optional[str] = None, **kwargs
) -> List[Dict[str, object]]:
    return retrieve_context(store, query, domain or "sql", **kwargs)


def retrieve_pyspark_context(
    store: Optional[VectorStore], query: str, domain: Optional[str] = None, **kwargs
) -> List[Dict[str, object]]:
    return retrieve_context(store, query, domain or "pyspark", **kwargs)


def _metadata_has_tags(metadata: Optional[Dict[str, object]], tags: Sequence[str]) -> bool:
    if not metadata:
        return False
    raw_tags = metadata.get("tags")
    if not raw_tags:
        return False
    if isinstance(raw_tags, str):
        candidate_tags = {tag.strip() for tag in raw_tags.split(",") if tag.strip()}
    elif isinstance(raw_tags, Iterable):
        candidate_tags = {str(tag).strip() for tag in raw_tags if str(tag).strip()}
    else:
        candidate_tags = set()
    return any(tag in candidate_tags for tag in tags)


def _canonical_resource(domain: Optional[str]) -> Optional[str]:
    if not domain:
        return None
    lowered = domain.lower()
    if lowered in {"pbip", "pbi", "powerbi", "power_bi"}:
        return "pbip"
    if lowered in {"sql", "tsql"}:
        return "sql"
    if lowered in {"spark", "pyspark"}:
        return "pyspark"
    return lowered


def _collections_for_resource(resource: Optional[str]) -> Sequence[str]:
    base = ["standards"]
    if resource == "pbip":
        base.append("pbip_reviews")
    return base
