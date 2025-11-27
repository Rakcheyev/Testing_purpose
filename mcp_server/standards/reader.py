"""Utilities for loading and normalising MCP standards configurations."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXTERNAL_DIR = PROJECT_ROOT / "external"
LEGACY_STANDARDS_PATH = EXTERNAL_DIR / "standards_mcp.json"
CATALOG_PATH = EXTERNAL_DIR / "standards_catalog.json"


@dataclass
class StandardRule:
    """Canonical representation of a single standard or best-practice rule."""

    id: str
    title: str
    resource: str
    scope: str
    category: str
    severity: str
    description: str
    details: Dict[str, Any]
    references: List[str]
    tags: List[str]
    applies_to: List[str] = field(default_factory=list)
    automation: Dict[str, Any] = field(default_factory=dict)
    rationale: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["details"] = self.details or {}
        payload["references"] = self.references or []
        payload["tags"] = sorted(set(self.tags or []))
        payload["applies_to"] = self.applies_to or []
        payload["automation"] = self.automation or {}
        if not self.rationale:
            payload.pop("rationale", None)
        return payload


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    return cleaned or "rule"


def _legacy_config() -> Dict[str, Any]:
    if not LEGACY_STANDARDS_PATH.exists():
        return {}
    return json.loads(LEGACY_STANDARDS_PATH.read_text())


def _build_dax_rules(config: Dict[str, Any]) -> List[StandardRule]:
    dax = config.get("DAX_Templates", {})
    source = dax.get("source", "external/DAX_Templates/Standards/02_DAX_Standards_and_Naming.md")
    naming = dax.get("naming", {})
    coding = dax.get("coding", {})
    anti_patterns = dax.get("anti_patterns", [])

    rules: List[StandardRule] = []

    measure_pattern = naming.get("measures", "snake_case")
    rules.append(
        StandardRule(
            id="dax.naming.measure.snake_case",
            title="Measures follow snake_case with semantic prefix",
            resource="DAX",
            scope="measure",
            category="naming",
            severity="warning",
            description=f"Measures must follow: {measure_pattern}",
            details={"pattern": measure_pattern},
            references=[source],
            tags=["dax", "measure", "naming"],
            applies_to=["measure"],
            automation={
                "check": {
                    "type": "pattern",
                    "field": "name",
                    "matcher": measure_pattern,
                },
                "auto_fix": {
                    "type": "transform",
                    "strategy": "snake_case",
                },
            },
        )
    )

    column_pattern = naming.get("columns", "PascalCase")
    rules.append(
        StandardRule(
            id="dax.naming.column.pascal_case",
            title="Columns use PascalCase with optional spaces",
            resource="DAX",
            scope="column",
            category="naming",
            severity="info",
            description=f"Columns should follow: {column_pattern}",
            details={"pattern": column_pattern},
            references=[source],
            tags=["dax", "column", "naming"],
            applies_to=["column"],
            automation={
                "check": {
                    "type": "pattern",
                    "field": "name",
                    "matcher": column_pattern,
                },
                "auto_fix": {
                    "type": "transform",
                    "strategy": "pascal_case_with_spaces",
                },
            },
        )
    )

    folders = naming.get("folders", [])
    if folders:
        rules.append(
            StandardRule(
                id="dax.naming.display_folder.allowed",
                title="Approved display folders",
                resource="DAX",
                scope="measure",
                category="organisation",
                severity="info",
                description="Measures and columns should reside in the curated display folders.",
                details={"allowed": folders, "default": folders[0]},
                references=[source],
                tags=["display_folder", "organisation"],
                applies_to=["measure", "column"],
                automation={
                    "check": {
                        "type": "membership",
                        "field": "display_folder",
                        "allowed": folders,
                    },
                    "auto_fix": {
                        "type": "assign",
                        "field": "display_folder",
                        "value": folders[0],
                    },
                },
            )
        )

    if coding:
        for key, guidance in coding.items():
            rule_id = f"dax.coding.{_slug(key)}"
            rules.append(
                StandardRule(
                    id=rule_id,
                    title=f"DAX coding guideline: {key}",
                    resource="DAX",
                    scope="measure",
                    category="coding",
                    severity="info",
                    description=str(guidance),
                    details={},
                    references=[source],
                    tags=["coding", key],
                    applies_to=["measure"],
                    automation={
                        "check": {
                            "type": "lint",
                            "rule": key,
                        }
                    },
                )
            )

    performance = dax.get("performance", {})
    if performance:
        performance_scope = {
            "iterators": ["measure"],
            "measures": ["measure"],
            "relationships": ["model"],
        }
        for key, guidance in performance.items():
            rule_id = f"dax.performance.{_slug(key)}"
            applies_to = performance_scope.get(key, ["model"])
            rules.append(
                StandardRule(
                    id=rule_id,
                    title=f"DAX performance guideline: {key}",
                    resource="DAX",
                    scope=applies_to[0],
                    category="performance",
                    severity="info",
                    description=str(guidance),
                    details={},
                    references=[source],
                    tags=["performance", key],
                    applies_to=applies_to,
                    automation={
                        "check": {
                            "type": "performance",
                            "rule": key,
                        }
                    },
                )
            )

    if anti_patterns:
        for entry in anti_patterns:
            rule_id = f"dax.anti_pattern.{_slug(entry)[:40]}"
            rules.append(
                StandardRule(
                    id=rule_id,
                    title="DAX anti-pattern",
                    resource="DAX",
                    scope="measure",
                    category="anti_pattern",
                    severity="warning",
                    description=entry,
                    details={},
                    references=[source],
                    tags=["anti_pattern", "dax"],
                    applies_to=["measure"],
                    automation={
                        "check": {
                            "type": "lint",
                            "rule_id": rule_id,
                        }
                    },
                )
            )

    recommended_format = "#,##0.00;(#,##0.00);-"

    rules.append(
        StandardRule(
            id="dax.formatting.measure.format_string_required",
            title="Measures define formatString",
            resource="DAX",
            scope="measure",
            category="formatting",
            severity="warning",
            description="Measures should specify formatString for consistent reporting.",
            details={"recommended": recommended_format},
            references=[source],
            tags=["formatting"],
            applies_to=["measure"],
            automation={
                "check": {
                    "type": "presence",
                    "field": "format_string",
                },
                "auto_fix": {
                    "type": "assign",
                    "field": "format_string",
                    "value": recommended_format,
                },
            },
        )
    )

    return rules


def _build_power_query_rules(config: Dict[str, Any]) -> List[StandardRule]:
    pq = config.get("Power_Query_guide", {})
    source = pq.get("source", "external/Power_Query_guide/Standards/FORMATTER.md")
    formatting = pq.get("formatting", {})

    rules: List[StandardRule] = []

    if formatting:
        for key, guidance in formatting.items():
            rule_id = f"power_query.formatting.{_slug(key)}"
            rules.append(
                StandardRule(
                    id=rule_id,
                    title=f"Power Query formatting: {key}",
                    resource="PowerQuery",
                    scope="query",
                    category="formatting",
                    severity="info",
                    description=str(guidance),
                    details={},
                    references=[source],
                    tags=["power_query", key],
                    applies_to=["query"],
                    automation={
                        "check": {
                            "type": "formatter",
                            "rule": key,
                        }
                    },
                )
            )

    doc_block = pq.get("doc_block", {})
    if doc_block:
        rules.append(
            StandardRule(
                id="power_query.documentation.doc_block_required",
                title="Power Query documentation block",
                resource="PowerQuery",
                scope="query",
                category="documentation",
                severity="warning",
                description="Power Query scripts require a documentation block with the specified fields.",
                details={"required_fields": doc_block.get("required", [])},
                references=[source],
                tags=["documentation", "power_query"],
                applies_to=["query"],
                automation={
                    "check": {
                        "type": "required_fields",
                        "fields": doc_block.get("required", []),
                        "path": "documentation",
                    }
                },
            )
        )

    return rules


def build_catalog(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    config = config or _legacy_config()
    rules: List[StandardRule] = []

    rules.extend(_build_dax_rules(config))
    rules.extend(_build_power_query_rules(config))

    catalog = {
        "version": datetime.now(timezone.utc).isoformat(),
        "rule_count": len(rules),
        "sources": {
            "legacy_config": str(LEGACY_STANDARDS_PATH.relative_to(PROJECT_ROOT))
            if LEGACY_STANDARDS_PATH.exists()
            else None,
        },
        "rules": [rule.to_dict() for rule in rules],
    }
    return catalog


def write_catalog(catalog: Dict[str, Any], path: Path = CATALOG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")


def load_catalog() -> Dict[str, Any]:
    if CATALOG_PATH.exists():
        return json.loads(CATALOG_PATH.read_text())
    if LEGACY_STANDARDS_PATH.exists():
        return build_catalog(_legacy_config())
    return {"version": None, "rule_count": 0, "rules": []}


def iter_rules(catalog: Dict[str, Any], *, resource: Optional[str] = None) -> Iterable[Dict[str, Any]]:
    for rule in catalog.get("rules", []):
        if resource and rule.get("resource") != resource:
            continue
        yield rule


__all__ = [
    "CATALOG_PATH",
    "LEGACY_STANDARDS_PATH",
    "StandardRule",
    "build_catalog",
    "load_catalog",
    "write_catalog",
    "iter_rules",
]
