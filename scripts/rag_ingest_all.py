"""CLI to ingest MCP artefacts into the configured vector store."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp_server.config import MCPConfig
from mcp_server.rag.ingest import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    ingest_pbip_reviews,
    ingest_standards,
)
from mcp_server.vectorstore import get_vector_store, reset_vector_store_cache


@dataclass
class DryRunVectorStore:
    """Lightweight VectorStore implementation that only tracks counts."""

    collections: Dict[str, int] = field(default_factory=dict)

    def index_documents(
        self,
        collection: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> None:
        self.collections[collection] = self.collections.get(collection, 0) + len(documents)

    def delete_collection(self, collection: str) -> None:
        self.collections[collection] = 0

    def query(
        self,
        collection: str,
        text: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:  # pragma: no cover - not used during ingestion
        raise NotImplementedError("Dry run store does not support querying")

    def ping(self) -> bool:
        return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest MCP artefacts into the RAG vector store")
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path("external/standards_catalog.json"),
        help="Path to standards_catalog.json",
    )
    parser.add_argument(
        "--reviews-root",
        type=Path,
        default=Path("pbip_artifacts/reviews"),
        help="Root directory containing PBIP review artefacts",
    )
    parser.add_argument(
        "--skip-standards",
        action="store_true",
        help="Skip ingesting the standards catalog",
    )
    parser.add_argument(
        "--skip-reviews",
        action="store_true",
        help="Skip ingesting PBIP review artefacts",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Chunk size for splitting documents (default: {DEFAULT_CHUNK_SIZE})",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP,
        help=f"Token overlap between chunks (default: {DEFAULT_CHUNK_OVERLAP})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not persist to the backend; report chunk counts only",
    )
    parser.add_argument(
        "--reset-cache",
        action="store_true",
        help="Reset the cached vector store instance before ingestion",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the resulting JSON payload",
    )
    parser.add_argument(
        "--require-backend",
        action="store_true",
        help="Fail with non-zero exit code if the vector store is disabled",
    )
    return parser


def _prepare_store(args: argparse.Namespace):
    if args.dry_run:
        return DryRunVectorStore()
    if args.reset_cache:
        reset_vector_store_cache()
    store = get_vector_store()
    if store is None and args.require_backend:
        raise RuntimeError("Vector store backend is not configured; set MCP_RAG_* variables")
    return store


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    store = _prepare_store(args)
    if store is None:
        payload = {
            "status": "skipped",
            "reason": "vector_store_disabled",
            "rag_enabled": getattr(MCPConfig, "RAG_ENABLED", False),
        }
        print(json.dumps(payload, indent=2 if args.pretty else None))
        return 0

    results: Dict[str, Any] = {
        "status": "ok",
        "dry_run": args.dry_run,
        "rag_enabled": getattr(MCPConfig, "RAG_ENABLED", False),
        "vector_backend": getattr(MCPConfig, "VECTOR_BACKEND", "none"),
    }

    if not args.skip_standards:
        count = ingest_standards(
            store,
            catalog_path=args.catalog,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
        results["standards_chunks"] = count

    if not args.skip_reviews:
        count = ingest_pbip_reviews(
            store,
            reviews_root=args.reviews_root,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
        results["review_chunks"] = count

    if isinstance(store, DryRunVectorStore):
        results["collections"] = store.collections

    print(json.dumps(results, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
