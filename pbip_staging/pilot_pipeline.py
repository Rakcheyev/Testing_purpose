"""Local pipeline for PBIP inspections without relying on predefined business cases.

The workflow processes every discovered PBIP artifact through four stages:

``ingest`` → collect local metadata
``classify`` → infer the business domain and intent using heuristics across metadata and model structure
``standards`` → run naming/formatting checks, display-folder verification, and DAX anti-pattern scanning
``report`` → persist summaries, audit history and optional stub reports

Validation results are written to ``standards.json`` together with safe rename suggestions in
``recommended_renames.tmdl``. When available, PBIP bundle directories (e.g. ``Sales.pbip``) are
handled transparently by reading their ``DataModelSchema.json`` content.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Iterable, List, Optional

from mcp_server.orchestration import SessionManager, AuditTrail
from mcp_server.standards.reader import load_catalog

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT_ROOT = BASE_DIR / "input"
PROFILE_ROOT = BASE_DIR / "profiles"
ARTIFACTS_ROOT = Path("pbip_artifacts") / "reviews"

PIPELINE_STEPS = (
    ("ingest", "Collected PBIP project structure"),
    ("classify", "Detected report domain and intent"),
    ("standards", "Checked naming and formatting standards"),
    ("report", "Generated summary report"),
)

DOMAIN_KEYWORDS = {
    "sales": {"sales", "revenue", "margin", "customer", "crm", "pipeline", "quote", "deal"},
    "finance": {"finance", "financial", "ledger", "pnl", "balance", "cash", "gl", "account"},
    "supply_chain": {"inventory", "warehouse", "logistics", "supply", "demand", "shipment", "stock"},
    "marketing": {"campaign", "marketing", "lead", "click", "impression", "conversion"},
    "hr": {"hr", "employee", "headcount", "attrition", "payroll", "recruit"},
}

SNAKE_CASE_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
PASCAL_CASE_WITH_SPACES_RE = re.compile(r"^[A-Z][A-Za-z0-9]*(?: [A-Z][A-Za-z0-9]*)*$")

STANDARDS_CATALOG = load_catalog()
RULE_LOOKUP: Dict[str, Dict[str, Any]] = {rule["id"]: rule for rule in STANDARDS_CATALOG.get("rules", [])}

PATTERN_STRATEGIES: Dict[str, re.Pattern[str]] = {
    "snake_case": SNAKE_CASE_RE,
    "pascal_case_with_spaces": PASCAL_CASE_WITH_SPACES_RE,
}

MATCHER_PATTERNS: Dict[str, re.Pattern[str]] = {
    "snake_case with semantic prefix": SNAKE_CASE_RE,
    "PascalCase with spaces for user-facing": PASCAL_CASE_WITH_SPACES_RE,
}


def _pattern_for_rule(rule: Optional[Dict[str, Any]]) -> Optional[re.Pattern[str]]:
    if not rule:
        return None
    automation = rule.get("automation", {})
    check = automation.get("check", {})
    matcher = check.get("matcher") or rule.get("details", {}).get("pattern")
    strategy = automation.get("auto_fix", {}).get("strategy") or check.get("strategy")
    if strategy and strategy in PATTERN_STRATEGIES:
        return PATTERN_STRATEGIES[strategy]
    if matcher and matcher in MATCHER_PATTERNS:
        return MATCHER_PATTERNS[matcher]
    return None


def _allowed_values(rule: Optional[Dict[str, Any]]) -> List[str]:
    if not rule:
        return []
    automation = rule.get("automation", {})
    check = automation.get("check", {})
    allowed = check.get("allowed")
    if not allowed:
        allowed = rule.get("details", {}).get("allowed", [])
    return list(allowed or [])


def to_snake_case(name: str) -> str:
    name = re.sub(r"[^0-9A-Za-z]+", "_", name).strip("_")
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return re.sub(r"_{2,}", "_", name).lower()


def to_pascal_case_with_spaces(name: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z]+", " ", name).strip()
    if not cleaned:
        return name
    words = re.split(r"\s+", cleaned)
    return " ".join(word.capitalize() for word in words if word)


def _auto_fix_value(rule: Optional[Dict[str, Any]], current_value: Optional[str] = None) -> Optional[str]:
    if not rule:
        return None
    automation = rule.get("automation", {})
    auto_fix = automation.get("auto_fix", {})
    fix_type = auto_fix.get("type")
    if fix_type == "transform":
        strategy = auto_fix.get("strategy")
        if strategy == "snake_case" and current_value is not None:
            return to_snake_case(current_value)
        if strategy == "pascal_case_with_spaces" and current_value is not None:
            return to_pascal_case_with_spaces(current_value)
    elif fix_type == "assign":
        return auto_fix.get("value")
    return None


MEASURE_NAMING_RULE = RULE_LOOKUP.get("dax.naming.measure.snake_case")
COLUMN_NAMING_RULE = RULE_LOOKUP.get("dax.naming.column.pascal_case")
DISPLAY_FOLDER_RULE = RULE_LOOKUP.get("dax.naming.display_folder.allowed")
FORMAT_STRING_RULE = RULE_LOOKUP.get("dax.formatting.measure.format_string_required")

ALLOWED_MEASURE_FOLDERS = set(_allowed_values(DISPLAY_FOLDER_RULE))
DEFAULT_MEASURE_FOLDER = _auto_fix_value(DISPLAY_FOLDER_RULE) or next(iter(ALLOWED_MEASURE_FOLDERS), "_Final")
DEFAULT_FORMAT_STRING = _auto_fix_value(FORMAT_STRING_RULE) or "#,##0.00;(#,##0.00);-"


def lookup_standards_message(rule_id: Optional[str], fallback: str) -> str:
    if rule_id and rule_id in RULE_LOOKUP:
        return RULE_LOOKUP[rule_id].get("description", fallback)
    return fallback


def isoformat(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_artifact(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))


def inside_pbip_directory(path: Path) -> bool:
    return any(parent.suffix.lower() == ".pbip" for parent in path.parents)


def discover_sources(targets: Iterable[Path]) -> List[Path]:
    sources: List[Path] = []
    seen = set()

    def register(candidate: Path) -> None:
        resolved = candidate.resolve()
        if resolved in seen:
            return
        seen.add(resolved)
        sources.append(candidate)

    for target in targets:
        if target.is_dir():
            if target.suffix.lower() == ".pbip":
                register(target)
                continue

            for item in sorted(target.rglob("*")):
                if item.is_dir() and item.suffix.lower() == ".pbip":
                    register(item)
                elif item.is_file():
                    suffix = item.suffix.lower()
                    if suffix == ".pbip":
                        register(item)
                    elif suffix == ".json" and not inside_pbip_directory(item):
                        register(item)
        elif target.is_file() and target.suffix.lower() in {".pbip", ".json"}:
            register(target)

    return sources


def load_metadata_for_source(source: Path) -> Dict[str, Any]:
    candidates = [
        source.parent / "metadata.json",
        source.with_suffix(".metadata.json"),
        source.parent / f"{source.stem}.metadata.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return json.loads(candidate.read_text())
    return {"source": source.name, "metadata": "missing"}


def load_profile_metadata(profile_key: str) -> Dict[str, Any]:
    """Return metadata for a given domain/profile key if legacy profiles still exist."""

    if not PROFILE_ROOT.exists():
        return {}

    normalized: List[str] = [profile_key]
    normalized.extend(
        [
            profile_key.replace("case_", "", 1),
            profile_key.replace("-", "_"),
            profile_key.replace(" ", "_")
        ]
    )

    seen: set[str] = set()
    for candidate in normalized:
        candidate = candidate.strip().lower()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        profile_path = PROFILE_ROOT / candidate / "metadata.json"
        if profile_path.exists():
            return json.loads(profile_path.read_text())

    default_profile = PROFILE_ROOT / "default" / "metadata.json"
    if default_profile.exists():
        return json.loads(default_profile.read_text())

    return {}


def load_model_structure(source: Path) -> Dict[str, Any]:
    """Extract a minimal structure representation from PBIP JSON or bundle directories."""

    data: Dict[str, Any]

    try:
        if source.is_dir():
            if source.suffix.lower() == ".pbip":
                schema_candidates = [
                    source / "DataModelSchema.json",
                    source / "model.json",
                ] + list(source.rglob("DataModelSchema.json"))
                for candidate in schema_candidates:
                    if candidate.exists():
                        data = json.loads(candidate.read_text())
                        break
                else:
                    return {}
            else:
                return {}
        elif source.suffix.lower() in {".json", ".pbip"}:
            data = json.loads(source.read_text())
        else:
            return {}
    except (OSError, json.JSONDecodeError):
        return {}

    model = data.get("model") or data.get("Model") or {}
    tables_raw = model.get("tables") or model.get("Tables") or []

    tables: List[str] = []
    measures: List[Dict[str, Any]] = []
    columns: List[Dict[str, Any]] = []

    for table in tables_raw:
        table_name = table.get("name") or table.get("Name")
        if table_name:
            tables.append(table_name)
        for measure in table.get("measures", []):
            measure_name = measure.get("name") or measure.get("Name")
            if measure_name:
                measures.append(
                    {
                        "table": table_name,
                        "name": measure_name,
                        "display_folder": measure.get("displayFolder") or measure.get("DisplayFolder"),
                        "format_string": measure.get("formatString") or measure.get("FormatString"),
                        "expression": measure.get("expression") or measure.get("Expression"),
                    }
                )
        for column in table.get("columns", []):
            column_name = column.get("name") or column.get("Name")
            if column_name:
                columns.append(
                    {
                        "table": table_name,
                        "name": column_name,
                        "display_folder": column.get("displayFolder") or column.get("DisplayFolder"),
                    }
                )

    return {
        "tables": tables,
        "measures": measures,
        "columns": columns,
    }


def detect_dax_issues(expression: str) -> List[Dict[str, Any]]:
    if not expression:
        return []

    cleaned = re.sub(r"/\*.*?\*/", "", expression, flags=re.S)
    lines: List[str] = []
    for raw_line in cleaned.splitlines():
        no_line_comment = raw_line.split("//", 1)[0].split("--", 1)[0]
        if no_line_comment.strip():
            lines.append(no_line_comment)

    normalized = "\n".join(lines)
    normalized_upper = normalized.upper()

    issues: List[Dict[str, Any]] = []

    if "/" in normalized and "DIVIDE(" not in normalized_upper:
        rule_id = "dax.coding.division"
        issues.append(
            {
                "rule_id": rule_id,
                "rule": lookup_standards_message(
                    rule_id,
                    "Use DIVIDE() instead of the raw division operator to avoid division-by-zero.",
                ),
            }
        )

    if "COUNT(" in normalized_upper and "COUNTROWS(" not in normalized_upper:
        rule_id = "dax.coding.counting"
        issues.append(
            {
                "rule_id": rule_id,
                "rule": lookup_standards_message(
                    rule_id,
                    "Prefer COUNTROWS() over COUNT(<column>) for row counting.",
                ),
            }
        )

    if len(lines) >= 4 and "VAR " not in normalized_upper:
        rule_id = "dax.anti_pattern.giant_measures_without_var"
        issues.append(
            {
                "rule_id": rule_id,
                "rule": lookup_standards_message(
                    rule_id,
                    "Long DAX measures should declare intermediate VAR blocks for readability.",
                ),
            }
        )

    for match in re.finditer(r"ALL\s*\(([^\)]+)\)", normalized_upper):
        argument = match.group(1)
        if "[" not in argument:
            rule_id = "dax.anti_pattern.all_table_when_all_column_is_enough"
            issues.append(
                {
                    "rule_id": rule_id,
                    "rule": lookup_standards_message(
                        rule_id,
                        "Use ALL(<column>) instead of ALL(<table>) to preserve slicer context when possible.",
                    ),
                }
            )
            break

    if "LOOKUPVALUE(" in normalized_upper:
        rule_id = "dax.anti_pattern.using_strings_instead_of_ids_for_joins_f"
        issues.append(
            {
                "rule_id": rule_id,
                "rule": lookup_standards_message(
                    rule_id,
                    "LOOKUPVALUE detected. Prefer model relationships or TREATAS for relational filtering.",
                ),
            }
        )

    return issues


def infer_domains_from_metadata(metadata: Dict[str, Any]) -> Counter:
    counter: Counter[str] = Counter()
    values: List[str] = []
    for key in ("domain", "business_domain", "domains", "tags", "topics", "business_units"):
        value = metadata.get(key)
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, list):
            values.extend(str(item) for item in value)

    for raw_value in values:
        lowered = raw_value.lower()
        for domain, keywords in DOMAIN_KEYWORDS.items():
            if domain in lowered:
                counter[domain] += 2
            for keyword in keywords:
                if keyword in lowered:
                    counter[domain] += 1
    return counter


def infer_domains_from_structure(structure: Dict[str, Any]) -> Counter:
    counter: Counter[str] = Counter()
    if not structure:
        return counter

    for table in structure.get("tables", []):
        lowered = table.lower()
        for domain, keywords in DOMAIN_KEYWORDS.items():
            if domain in lowered:
                counter[domain] += 3
            for keyword in keywords:
                if keyword in lowered:
                    counter[domain] += 1

    for column in structure.get("columns", []):
        lowered = column.get("name", "").lower()
        for domain, keywords in DOMAIN_KEYWORDS.items():
            if domain in lowered:
                counter[domain] += 2
            for keyword in keywords:
                if keyword in lowered:
                    counter[domain] += 1

    return counter


def determine_primary_domain(metadata: Dict[str, Any], structure: Dict[str, Any], source: Path) -> Tuple[str, List[Tuple[str, int]]]:
    counter: Counter[str] = Counter()
    counter.update(infer_domains_from_metadata(metadata))
    counter.update(infer_domains_from_structure(structure))

    name_hint = source.stem.lower()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if domain in name_hint:
            counter[domain] += 2
        for keyword in keywords:
            if keyword in name_hint:
                counter[domain] += 1

    if not counter:
        return "generic", []

    ranked = counter.most_common()
    top_score = ranked[0][1]
    near_top = [item for item in ranked if item[1] >= max(1, top_score - 1) and item[1] > 0]
    if len(near_top) > 1:
        return "multi-domain", ranked

    return ranked[0][0], ranked


def infer_intent(metadata: Dict[str, Any], structure: Dict[str, Any]) -> str:
    intent = metadata.get("intent") or metadata.get("purpose")
    if isinstance(intent, str):
        return intent

    measure_count = len(structure.get("measures", [])) if structure else 0
    column_count = len(structure.get("columns", [])) if structure else 0
    if measure_count > column_count:
        return "analytics"
    if column_count and column_count > measure_count * 2:
        return "modeling"
    return "review"


def enrich_metadata(metadata: Dict[str, Any], profile_metadata: Dict[str, Any]) -> Dict[str, Any]:
    merged = {**profile_metadata, **metadata}
    if "tags" in profile_metadata and "tags" in metadata:
        merged["tags"] = sorted({*profile_metadata["tags"], *metadata["tags"]}) if isinstance(metadata["tags"], list) else profile_metadata["tags"]
    return merged


def classify_source(source: Path, metadata: Dict[str, Any], structure: Dict[str, Any]) -> Dict[str, Any]:
    primary_domain, ranked_domains = determine_primary_domain(metadata, structure, source)
    profile_key = primary_domain
    if primary_domain == "multi-domain" and ranked_domains:
        profile_key = ranked_domains[0][0]

    profile_meta = load_profile_metadata(profile_key)
    intent = infer_intent(metadata, structure)
    merged_metadata = enrich_metadata(metadata, profile_meta)

    return {
        "domain": primary_domain,
        "intent": intent,
        "metadata": merged_metadata,
        "domain_candidates": ranked_domains,
        "profile_loaded": bool(profile_meta),
    }

def validate_standards(source: Path, structure: Dict[str, Any]) -> Dict[str, Any]:
    if not structure:
        return {
            "status": "skipped",
            "reason": "Structure could not be parsed from the artifact.",
            "issues": [],
            "auto_fixes": [],
            "issue_count": 0,
        }

    issues: List[Dict[str, Any]] = []
    fixes: List[Dict[str, Any]] = []

    for measure in structure.get("measures", []):
        name = measure["name"]
        naming_rule = MEASURE_NAMING_RULE
        pattern = _pattern_for_rule(naming_rule) or SNAKE_CASE_RE
        if pattern and not pattern.match(name):
            suggested = _auto_fix_value(naming_rule, name) or to_snake_case(name)
            issues.append(
                {
                    "entity": "measure",
                    "name": name,
                    "rule_id": naming_rule["id"] if naming_rule else None,
                    "rule": (naming_rule or {}).get(
                        "description",
                        "DAX measures must follow snake_case with a semantic prefix",
                    ),
                    "suggested": suggested,
                }
            )
            fixes.append(
                {
                    "entity": "measure",
                    "table": measure.get("table"),
                    "current": name,
                    "suggested": suggested,
                    "rule_id": naming_rule["id"] if naming_rule else None,
                }
            )

        display_folder = measure.get("display_folder")
        allowed_folders = ALLOWED_MEASURE_FOLDERS or set(_allowed_values(DISPLAY_FOLDER_RULE))
        default_folder = _auto_fix_value(DISPLAY_FOLDER_RULE) or DEFAULT_MEASURE_FOLDER
        if not display_folder:
            issues.append(
                {
                    "entity": "measure",
                    "name": name,
                    "rule_id": DISPLAY_FOLDER_RULE["id"] if DISPLAY_FOLDER_RULE else None,
                    "rule": (DISPLAY_FOLDER_RULE or {}).get(
                        "description",
                        "Measures should define a display folder for report organization",
                    ),
                    "suggested": default_folder,
                }
            )
            table_name = measure.get("table")
            if table_name:
                fixes.append(
                    {
                        "entity": "measure",
                        "table": table_name,
                        "current": name,
                        "action": "set_display_folder",
                        "suggested": default_folder,
                        "rule_id": DISPLAY_FOLDER_RULE["id"] if DISPLAY_FOLDER_RULE else None,
                    }
                )
        elif allowed_folders and display_folder not in allowed_folders:
            issues.append(
                {
                    "entity": "measure",
                    "name": name,
                    "rule_id": DISPLAY_FOLDER_RULE["id"] if DISPLAY_FOLDER_RULE else None,
                    "rule": (DISPLAY_FOLDER_RULE or {}).get(
                        "description",
                        "Display folder should match approved MCP catalog",
                    ),
                    "found": display_folder,
                    "suggested": sorted(allowed_folders),
                }
            )
            table_name = measure.get("table")
            if table_name and allowed_folders:
                fixes.append(
                    {
                        "entity": "measure",
                        "table": table_name,
                        "current": name,
                        "action": "set_display_folder",
                        "suggested": default_folder,
                        "rule_id": DISPLAY_FOLDER_RULE["id"] if DISPLAY_FOLDER_RULE else None,
                    }
                )

        format_string = measure.get("format_string")
        if not format_string:
            suggested_format = _auto_fix_value(FORMAT_STRING_RULE) or DEFAULT_FORMAT_STRING
            issues.append(
                {
                    "entity": "measure",
                    "name": name,
                    "rule_id": FORMAT_STRING_RULE["id"] if FORMAT_STRING_RULE else None,
                    "rule": (FORMAT_STRING_RULE or {}).get(
                        "description",
                        "Measures should specify formatString for consistent presentation",
                    ),
                    "suggested": suggested_format,
                }
            )
            table_name = measure.get("table")
            if table_name:
                fixes.append(
                    {
                        "entity": "measure",
                        "table": table_name,
                        "current": name,
                        "action": "set_format_string",
                        "suggested": suggested_format,
                        "rule_id": FORMAT_STRING_RULE["id"] if FORMAT_STRING_RULE else None,
                    }
                )

        expression = (measure.get("expression") or "").strip()
        for dax_issue in detect_dax_issues(expression):
            issues.append(
                {
                    "entity": "measure",
                    "name": name,
                    **dax_issue,
                }
            )

    for column in structure.get("columns", []):
        name = column["name"]
        naming_rule = COLUMN_NAMING_RULE
        pattern = _pattern_for_rule(naming_rule) or PASCAL_CASE_WITH_SPACES_RE
        if pattern and not pattern.match(name):
            friendly = _auto_fix_value(naming_rule, name) or to_pascal_case_with_spaces(name)
            issues.append(
                {
                    "entity": "column",
                    "name": name,
                    "rule_id": naming_rule["id"] if naming_rule else None,
                    "rule": (naming_rule or {}).get(
                        "description",
                        "Columns should use PascalCase with optional spaces",
                    ),
                    "suggested": friendly,
                }
            )
            fixes.append(
                {
                    "entity": "column",
                    "table": column.get("table"),
                    "current": name,
                    "suggested": friendly,
                    "rule_id": naming_rule["id"] if naming_rule else None,
                }
            )

        display_folder = column.get("display_folder")
        if display_folder:
            allowed_folders = ALLOWED_MEASURE_FOLDERS or set(_allowed_values(DISPLAY_FOLDER_RULE))
            default_folder = _auto_fix_value(DISPLAY_FOLDER_RULE) or DEFAULT_MEASURE_FOLDER
        else:
            allowed_folders = set()
            default_folder = _auto_fix_value(DISPLAY_FOLDER_RULE) or DEFAULT_MEASURE_FOLDER
        if display_folder and allowed_folders and display_folder not in allowed_folders:
            issues.append(
                {
                    "entity": "column",
                    "name": name,
                    "rule_id": DISPLAY_FOLDER_RULE["id"] if DISPLAY_FOLDER_RULE else None,
                    "rule": (DISPLAY_FOLDER_RULE or {}).get(
                        "description",
                        "Column display folders should use approved naming conventions",
                    ),
                    "found": display_folder,
                    "suggested": sorted(allowed_folders),
                }
            )
            table_name = column.get("table")
            if table_name and allowed_folders:
                fixes.append(
                    {
                        "entity": "column",
                        "table": table_name,
                        "current": name,
                        "action": "set_display_folder",
                        "suggested": default_folder,
                        "rule_id": DISPLAY_FOLDER_RULE["id"] if DISPLAY_FOLDER_RULE else None,
                    }
                )

    status = "ok" if not issues else "issues_found"

    return {
        "status": status,
        "source": str(source),
        "issues": issues,
        "auto_fixes": fixes,
        "issue_count": len(issues),
    }


def generate_tmdl_corrections(fixes: List[Dict[str, Any]]) -> str:
    if not fixes:
        return ""

    def escape_single_quotes(value: str) -> str:
        return value.replace("'", "''")

    def escape_brackets(value: str) -> str:
        return value.replace("]", "]]")

    def qualify(entity: str, table: str, name: str) -> str:
        table_ref = f"'{escape_single_quotes(table)}'" if table else ""
        identifier = f"[{escape_brackets(name)}]"
        prefix = "MEASURE" if entity == "measure" else "COLUMN"
        return f"{prefix} {table_ref}{identifier}"

    lines = ["// Suggested safe statements (review before applying)"]
    for fix in fixes:
        entity = fix.get("entity")
        table = fix.get("table")
        name = fix.get("current")
        suggested = fix.get("suggested")
        action = fix.get("action", "rename")

        if not table or not name or suggested is None:
            continue

        qualified = qualify(entity, table, name)

        if action == "rename":
            lines.append(
                f"ALTER {qualified} RENAME TO [{escape_brackets(str(suggested))}];"
            )
        elif action == "set_display_folder":
            lines.append(
                f"ALTER {qualified} SET DISPLAYFOLDER = '{escape_single_quotes(str(suggested))}';"
            )
        elif action == "set_format_string":
            lines.append(
                f'ALTER {qualified} SET FORMAT_STRING = "{str(suggested).replace("\"", "\"\"")}";'
            )
        else:
            lines.append(
                f"// Pending support for action '{action}' on {entity} {table}.{name} -> {suggested}"
            )

    return "\n".join(lines) + "\n"


def build_artifact_dir(source: Path, classification: Dict[str, Any]) -> Path:
    digest = hashlib.sha1(str(source.resolve()).encode("utf-8")).hexdigest()[:8]
    domain = classification.get("domain", "generic")
    directory_name = f"{domain}__{source.stem}_{digest}" if domain != "generic" else f"{source.stem}_{digest}"
    return ARTIFACTS_ROOT / directory_name


def run_source(source: Path, dry_run: bool = False) -> Dict[str, Any]:
    metadata = load_metadata_for_source(source)
    structure = load_model_structure(source)
    classification = classify_source(source, metadata, structure)

    audit = AuditTrail()
    manager = SessionManager(audit=audit)
    session_id = manager.start_session(
        user="pilot_cli",
        metadata={
            "source": str(source),
            "domain": classification["domain"],
            "intent": classification["intent"],
        },
    )

    summary: Dict[str, Any] = {
        "source": str(source),
        "session_id": session_id,
        "classification": classification,
        "dry_run": dry_run,
        "steps": [],
        "structure_summary": {
            "tables": len(structure.get("tables", [])) if structure else 0,
            "measures": len(structure.get("measures", [])) if structure else 0,
            "columns": len(structure.get("columns", [])) if structure else 0,
        },
    }

    artifacts_dir = build_artifact_dir(source, classification)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    for action, description in PIPELINE_STEPS:
        payload: Dict[str, Any] = {
            "source": source.name,
            "description": description,
            "domain": classification["domain"],
        }
        entry = manager.process_session(
            session_id,
            action=action,
            user="pilot_cli",
            payload=payload,
        )
        step_result: Dict[str, Any] = {
            "action": action,
            "status": entry["status"],
            "timestamp": isoformat(entry["timestamp"]),
            "description": description,
        }

        if action == "standards":
            validation = validate_standards(source, structure)
            step_result["validation"] = validation
            summary["standards"] = validation
            summary["standards_issue_count"] = validation.get("issue_count", 0)
            if not dry_run:
                write_artifact(artifacts_dir / "standards.json", validation)
                if validation.get("auto_fixes"):
                    tmdl_patch = generate_tmdl_corrections(validation["auto_fixes"])
                    if tmdl_patch:
                        (artifacts_dir / "recommended_renames.tmdl").write_text(tmdl_patch)

        summary["steps"].append(step_result)

        if action == "report" and not dry_run:
            report_payload = {
                "source": str(source),
                "domain": classification["domain"],
                "intent": classification["intent"],
                "generated_at": isoformat(datetime.now(timezone.utc).timestamp()),
                "notes": "Stub report generated by pilot pipeline",
            }
            report_file = artifacts_dir / f"{source.stem}_report.json"
            write_artifact(report_file, report_payload)

    manager.close_session(session_id, user="pilot_cli")

    session_history = manager.sessions[session_id]["history"]
    history_payload = [
        {**record, "timestamp": isoformat(record["timestamp"])}
        for record in session_history
    ]
    audit_payload = [
        {**record, "timestamp": isoformat(record["timestamp"])}
        for record in audit.get_session_records(session_id)
    ]

    write_artifact(artifacts_dir / "session_history.json", {"history": history_payload})
    write_artifact(artifacts_dir / "audit.json", {"audit": audit_payload})
    write_artifact(artifacts_dir / "summary.json", summary)

    return summary


def resolve_targets(paths: List[str]) -> List[Path]:
    if paths:
        return [Path(item).expanduser() for item in paths]
    default_root = DEFAULT_INPUT_ROOT
    default_root.mkdir(parents=True, exist_ok=True)
    return [default_root]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local PBIP review workflow without predefined cases")
    parser.add_argument(
        "targets",
        nargs="*",
        help="PBIP files or directories to process (defaults to pbip_staging/input)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip artifact generation, keep logging only",
    )
    args = parser.parse_args()

    targets = resolve_targets(args.targets)
    sources = discover_sources(targets)

    if not sources:
        print(json.dumps({"status": "no_sources", "processed": 0, "note": "No PBIP sources discovered."}))
        return

    summaries = [run_source(source, dry_run=args.dry_run) for source in sources]
    output = {
        "status": "completed",
        "processed": len(summaries),
        "dry_run": args.dry_run,
        "sources": [summary["source"] for summary in summaries],
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
