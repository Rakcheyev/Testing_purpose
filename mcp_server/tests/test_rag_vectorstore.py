from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from mcp_server.rag.query import retrieve_context
from mcp_server.rag.ingest import ingest_pbip_reviews, ingest_standards
from mcp_server.vectorstore.chroma_backend import ChromaVectorStore


class DummyVectorStore:
    def __init__(self, responses: Dict[str, List[Dict[str, Any]]]) -> None:
        self.responses = responses
        self.calls: List[Dict[str, Any]] = []

    def query(
        self,
        collection: str,
        text: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        self.calls.append({"collection": collection, "text": text, "top_k": top_k, "filters": filters})
        return self.responses.get(collection, [])


def test_retrieve_context_filters_by_tags_and_resource():
    store = DummyVectorStore(
        {
            "standards": [
                {
                    "id": "std-1",
                    "document": "naming convention",
                    "metadata": {"tags": "naming,format", "resource": "pbip"},
                    "score": 0.6,
                },
                {
                    "id": "std-2",
                    "document": "formatting guidance",
                    "metadata": {"tags": "format", "resource": "pbip"},
                    "score": 0.7,
                },
            ],
            "pbip_reviews": [
                {
                    "id": "rev-1",
                    "document": "naming issue",
                    "metadata": {"tags": "naming", "resource": "pbip"},
                    "score": 0.8,
                }
            ],
        }
    )

    results = retrieve_context(store, "naming", domain="pbip", tags=["naming"], n=2)

    assert len(results) == 2
    assert all("naming" in (res["metadata"].get("tags") or "") for res in results)
    assert results[0]["score"] >= results[1]["score"]
    assert all(call["filters"]["resource"] == "pbip" for call in store.calls)


def test_retrieve_context_handles_disabled_store():
    assert retrieve_context(None, "query") == []
    assert retrieve_context(DummyVectorStore({}), "", domain="pbip") == []


class _TrackingStore:
    def __init__(self) -> None:
        self.deletions: List[str] = []
        self.index_log: Dict[str, Dict[str, Any]] = {}

    def index_documents(
        self,
        collection: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> None:
        self.index_log[collection] = {
            "documents": list(documents),
            "metadatas": list(metadatas or [{} for _ in documents]),
            "ids": list(ids or []),
        }

    def delete_collection(self, collection: str) -> None:
        self.deletions.append(collection)

    def query(self, *args, **kwargs):  # pragma: no cover - unused
        raise NotImplementedError

    def ping(self) -> bool:  # pragma: no cover - unused
        return True


@pytest.fixture
def sample_catalog(tmp_path: Path) -> Path:
    payload = {
        "rules": [
            {
                "id": "STD_RULE_1",
                "title": "Ensure naming",
                "resource": "pbip",
                "scope": "naming",
                "category": "style",
                "severity": "medium",
                "description": "Names should follow pattern",
                "tags": ["naming", "format"],
                "references": ["https://example.com/naming"],
                "automation": {"check": "pattern", "auto_fix": False},
            },
            {
                "id": "STD_RULE_2",
                "title": "Require format string",
                "resource": "pbip",
                "scope": "format",
                "category": "quality",
                "severity": "low",
                "description": "Measures should expose format",  # keep short chunk
            },
        ]
    }
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return catalog_path


def test_ingest_standards_indexes_rules(sample_catalog: Path):
    store = _TrackingStore()

    chunk_count = ingest_standards(store, catalog_path=sample_catalog, chunk_size=256, chunk_overlap=0)

    assert store.deletions == ["standards"]
    assert chunk_count == 2
    recorded = store.index_log["standards"]
    assert len(recorded["documents"]) == 2
    first_meta = recorded["metadatas"][0]
    assert first_meta["rule_id"] == "STD_RULE_1"
    assert first_meta["resource"] == "pbip"
    assert "naming" in first_meta["tags"].split(",")


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_ingest_pbip_reviews_collects_metadata(tmp_path: Path):
    reviews_root = tmp_path / "reviews"
    review_dir = reviews_root / "sales__sample"
    review_dir.mkdir(parents=True)

    _write_json(
        review_dir / "summary.json",
        {
            "source": "pbip_staging/input/demo.pbip",
            "classification": {"domain": "Sales", "intent": "standard_review"},
            "structure_summary": {"tables": 2, "measures": 3, "columns": 5},
            "steps": [
                {"action": "ingest", "status": "ok", "timestamp": "2025-11-27T08:00:00Z"},
                {"action": "standards", "status": "ok", "timestamp": "2025-11-27T08:05:00Z"},
            ],
        },
    )
    _write_json(
        review_dir / "standards.json",
        {
            "issues": [
                {"rule_id": "STD_RULE_1", "entity": "measure", "name": "[Metric]", "rule": "Use naming", "suggested": "metric"},
                {"rule_id": "STD_RULE_2", "entity": "measure", "name": "[Another]", "rule": "Provide format", "suggested": "0.0"},
            ]
        },
    )
    _write_json(review_dir / "audit.json", [{"timestamp": "2025-11-27T08:00:00Z", "action": "start", "status": "ok"}])
    _write_json(review_dir / "session_history.json", [{"timestamp": "2025-11-27T08:05:00Z", "action": "standards"}])

    store = _TrackingStore()

    chunk_count = ingest_pbip_reviews(store, reviews_root=reviews_root, chunk_size=256, chunk_overlap=0)

    assert store.deletions == ["pbip_reviews"]
    assert chunk_count == 1  # single review, single chunk with generous size

    recorded = store.index_log["pbip_reviews"]
    assert recorded["metadatas"][0]["domain"] == "sales"
    assert recorded["metadatas"][0]["subdomain"] == "standard_review"
    tag_tokens = {token for token in recorded["metadatas"][0]["tags"].split(",") if token}
    assert tag_tokens == {"STD_RULE_1", "STD_RULE_2"}


class _StubCollection:
    def __init__(self) -> None:
        self.add_calls: List[Dict[str, Any]] = []
        self.deleted = False

    def add(self, *, documents, metadatas, ids) -> None:
        self.add_calls.append({
            "documents": list(documents),
            "metadatas": list(metadatas),
            "ids": list(ids),
        })

    def query(self, *, query_texts, n_results, where=None):
        return {
            "documents": [["doc-1"]],
            "metadatas": [[{"resource": "pbip"}]],
            "ids": [["id-1"]],
            "distances": [[0.25]],
        }


class _StubChromaClient:
    def __init__(self) -> None:
        self.collections: Dict[str, _StubCollection] = {}
        self.deleted: List[str] = []

    def get_or_create_collection(self, name: str) -> _StubCollection:
        self.collections.setdefault(name, _StubCollection())
        return self.collections[name]

    def delete_collection(self, name: str) -> None:
        if name not in self.collections:
            raise ValueError("missing")
        self.deleted.append(name)
        del self.collections[name]

    def list_collections(self) -> List[str]:
        return list(self.collections.keys())


def test_chroma_vector_store_adapts_client_methods():
    client = _StubChromaClient()
    store = ChromaVectorStore(client=client)

    store.index_documents("standards", ["doc-1"], metadatas=[{"resource": "pbip"}], ids=["id-1"])
    assert client.collections["standards"].add_calls[0]["documents"] == ["doc-1"]

    results = store.query("standards", "test", top_k=1, filters={"resource": "pbip"})
    assert results[0]["id"] == "id-1"
    assert results[0]["metadata"] == {"resource": "pbip"}
    assert pytest.approx(results[0]["score"], rel=1e-3) == 0.8

    store.delete_collection("standards")
    assert "standards" in client.deleted

    # Deleting a non-existent collection should not raise
    store.delete_collection("unknown")

    assert store.ping() is True