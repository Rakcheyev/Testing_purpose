"""Ingestion helpers that push MCP knowledge bases into the vector store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..vectorstore import VectorStore

DEFAULT_CHUNK_SIZE = 420
DEFAULT_CHUNK_OVERLAP = 60


def ingest_standards(
    store: Optional[VectorStore],
    catalog_path: Path = Path("external/standards_catalog.json"),
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> int:
    """Load ``standards_catalog.json`` into the configured vector store."""

    if store is None:
        return 0
    if not catalog_path.exists():
        return 0
    data = json.loads(catalog_path.read_text(encoding="utf-8"))
    rules = data.get("rules", [])
    documents: List[str] = []
    metadatas: List[Dict[str, str]] = []
    identifiers: List[str] = []
    for rule in rules:
        text_blob = _format_rule(rule)
        for idx, chunk in enumerate(_chunk_text(text_blob, chunk_size, chunk_overlap)):
            documents.append(chunk)
            metadatas.append(_rule_metadata(rule))
            identifiers.append(f"{rule.get('id', 'rule')}::{idx}")
    store.delete_collection("standards")
    if documents:
        store.index_documents("standards", documents, metadatas, identifiers)
    return len(documents)


def ingest_pbip_reviews(
    store: Optional[VectorStore],
    reviews_root: Path = Path("pbip_artifacts/reviews"),
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> int:
    """Push PBIP review artefacts into the vector store."""

    if store is None:
        return 0
    if not reviews_root.exists():
        return 0
    documents: List[str] = []
    metadatas: List[Dict[str, str]] = []
    identifiers: List[str] = []
    for review_dir in sorted(reviews_root.iterdir()):
        if not review_dir.is_dir():
            continue
        doc, metadata = _build_review_payload(review_dir)
        if not doc:
            continue
        for idx, chunk in enumerate(_chunk_text(doc, chunk_size, chunk_overlap)):
            documents.append(chunk)
            metadatas.append(metadata)
            identifiers.append(f"{review_dir.name}::{idx}")
    store.delete_collection("pbip_reviews")
    if documents:
        store.index_documents("pbip_reviews", documents, metadatas, identifiers)
    return len(documents)


def _chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    words = text.split()
    if not words:
        return []
    chunks: List[str] = []
    start = 0
    length = len(words)
    while start < length:
        end = min(length, start + chunk_size)
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == length:
            break
        start = max(0, end - overlap)
    return chunks


def _format_rule(rule: Dict[str, object]) -> str:
    references = "\n".join(str(ref) for ref in rule.get("references", []) or [])
    details = json.dumps(rule.get("details", {}), ensure_ascii=False)
    automation = json.dumps(rule.get("automation", {}), ensure_ascii=False)
    description = rule.get("description") or ""
    title = rule.get("title") or rule.get("id") or "Unnamed rule"
    body_parts = [
        f"Rule: {title}",
        f"ID: {rule.get('id', 'n/a')}",
        f"Resource: {rule.get('resource', 'unknown')} (scope: {rule.get('scope', 'n/a')})",
        f"Category: {rule.get('category', 'n/a')} — Severity: {rule.get('severity', 'n/a')}",
        f"Description: {description}",
    ]
    if references:
        body_parts.append(f"References:\n{references}")
    if details and details != "{}":
        body_parts.append(f"Details: {details}")
    if automation and automation != "{}":
        body_parts.append(f"Automation: {automation}")
    tags = ", ".join(rule.get("tags", []) or [])
    if tags:
        body_parts.append(f"Tags: {tags}")
    applies_to = ", ".join(rule.get("applies_to", []) or [])
    if applies_to:
        body_parts.append(f"Applies to: {applies_to}")
    return "\n".join(body_parts)


def _rule_metadata(rule: Dict[str, object]) -> Dict[str, str]:
    return {
        "rule_id": str(rule.get("id", "")),
        "resource": str(rule.get("resource", "standards")).lower(),
        "domain": str(rule.get("domain", rule.get("resource", "standards"))).lower(),
        "subdomain": str(rule.get("scope", "")) or "",
        "category": str(rule.get("category", "")) or "",
        "tags": ",".join(rule.get("tags", []) or []),
        "source": "standards_catalog",
    }


def _build_review_payload(review_dir: Path) -> Tuple[str, Dict[str, str]]:
    summary_data = _read_json(review_dir / "summary.json")
    standards_data = _read_json(review_dir / "standards.json")
    audit_data = _read_json(review_dir / "audit.json")
    session_data = _read_json(review_dir / "session_history.json")

    parts: List[str] = [f"PBIP review: {review_dir.name}"]

    classification = summary_data.get("classification", {}) if isinstance(summary_data, dict) else {}
    domain = str(classification.get("domain", "pbip")).lower()
    subdomain = str(classification.get("intent", "review"))
    if classification:
        parts.append(
            "Classification: "
            f"domain={classification.get('domain', 'n/a')}, "
            f"intent={classification.get('intent', 'n/a')}"
        )
    if summary_data.get("structure_summary"):
        structure = summary_data["structure_summary"]
        parts.append(
            "Structure summary: "
            f"tables={structure.get('tables', 0)}, "
            f"measures={structure.get('measures', 0)}, "
            f"columns={structure.get('columns', 0)}"
        )
    if summary_data.get("steps"):
        step_lines = [
            f"- {step.get('action', 'step')}: {step.get('description', '')} (status={step.get('status', 'n/a')})"
            for step in summary_data["steps"]
        ]
        parts.append("Pipeline steps:\n" + "\n".join(step_lines))

    issue_tags = set()
    issues = standards_data.get("issues", []) if isinstance(standards_data, dict) else []
    if issues:
        issue_lines = []
        for issue in issues:
            rule_id = issue.get("rule_id", "unknown")
            issue_tags.add(rule_id)
            issue_lines.append(
                f"Rule {rule_id} on {issue.get('entity', 'entity')} "
                f"{issue.get('name', '')}: {issue.get('rule', '')}. "
                f"Suggested: {issue.get('suggested', issue.get('action', ''))}"
            )
        parts.append("Standards issues:\n" + "\n".join(issue_lines))

    if audit_data:
        audit_lines = [
            f"{entry.get('timestamp', 'n/a')} — {entry.get('action', 'action')} ({entry.get('status', 'n/a')})"
            for entry in audit_data if isinstance(entry, dict)
        ]
        if audit_lines:
            parts.append("Audit trail:\n" + "\n".join(audit_lines))

    if session_data:
        history_lines = [
            f"{entry.get('timestamp', 'n/a')} — {entry.get('action', 'action')}" for entry in session_data if isinstance(entry, dict)
        ]
        if history_lines:
            parts.append("Session history:\n" + "\n".join(history_lines))

    doc_text = "\n\n".join(parts)
    metadata = {
        "review_id": review_dir.name,
        "source": "pbip_review",
        "resource": "pbip",
        "domain": domain,
        "subdomain": subdomain,
        "tags": ",".join(sorted(issue_tags)),
    }
    return doc_text, metadata


def _read_json(path: Path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
