from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import zipfile

from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_ROOT = PROJECT_ROOT / "pbip_artifacts" / "reviews"
DEFAULT_INPUT_ROOT = Path(__file__).resolve().parent / "input"


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def _read_text(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    try:
        return path.read_text()
    except OSError:
        return None


def _iso_to_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _build_label(run_dir: Path, summary: Dict[str, Any]) -> str:
    domain = summary.get("classification", {}).get("domain")
    source_name = Path(summary.get("source", run_dir.name)).name
    if domain:
        return f"{domain} · {source_name}"
    return source_name


def _last_step_timestamp(summary: Dict[str, Any]) -> Optional[datetime]:
    steps = summary.get("steps") or []
    if not steps:
        return None
    last_ts = steps[-1].get("timestamp")
    return _iso_to_datetime(last_ts)


def _summarise_rule_counts(standards: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not standards:
        return []

    issues = standards.get("issues", []) or []
    counter: Counter[str] = Counter()
    descriptions: Dict[str, str] = {}

    for issue in issues:
        rule_id = str(issue.get("rule_id") or issue.get("rule") or "unknown")
        counter[rule_id] += 1
        if rule_id not in descriptions and issue.get("rule"):
            descriptions[rule_id] = str(issue.get("rule"))

    return [
        {
            "rule_id": rule_id,
            "count": count,
            "description": descriptions.get(rule_id, ""),
        }
        for rule_id, count in counter.most_common()
    ]


def load_run(run_dir: Path) -> Dict[str, Any]:
    summary = _read_json(run_dir / "summary.json")
    standards = _read_json(run_dir / "standards.json")
    audit = _read_json(run_dir / "audit.json")
    session_history = _read_json(run_dir / "session_history.json")
    recommended_tmdl = _read_text(run_dir / "recommended_renames.tmdl")

    issue_count = (
        standards.get("issue_count")
        if standards
        else summary.get("standards_issue_count")
    )

    return {
        "name": run_dir.name,
        "label": _build_label(run_dir, summary),
        "path": run_dir,
        "summary": summary,
        "standards": standards,
        "issue_count": issue_count,
        "rule_summary": _summarise_rule_counts(standards),
        "audit": audit,
        "session_history": session_history,
        "recommended_tmdl": recommended_tmdl,
        "completed_at": _last_step_timestamp(summary),
    }


def load_runs() -> List[Dict[str, Any]]:
    if not ARTIFACTS_ROOT.exists():
        return []
    runs = [load_run(path) for path in ARTIFACTS_ROOT.iterdir() if path.is_dir()]
    runs.sort(key=lambda item: item.get("completed_at") or datetime.min, reverse=True)
    return runs


def run_pipeline(targets: Optional[Iterable[Path]] = None, *, dry_run: bool = False) -> Dict[str, Any]:
    cmd: List[str] = [sys.executable, "-m", "pbip_staging.pilot_pipeline"]
    if dry_run:
        cmd.append("--dry-run")
    if targets:
        cmd.extend(str(Path(target)) for target in targets)

    completed = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "success": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "command": cmd,
    }


def save_uploaded_artifact(content: bytes, original_name: str) -> Dict[str, Any]:
    """Persist an uploaded artifact into the staging input directory.

    Stores the payload under a unique folder in ``pbip_staging/input``. If the
    upload is a zip-compatible PBIP bundle, it is extracted automatically and
    the resulting path to a ``.pbip`` directory (or extracted contents) is
    returned alongside a short status message.
    """

    if not original_name:
        original_name = "uploaded.pbip"

    DEFAULT_INPUT_ROOT.mkdir(parents=True, exist_ok=True)
    upload_id = uuid4().hex[:8]
    staging_root = DEFAULT_INPUT_ROOT / f"upload_{upload_id}"
    staging_root.mkdir(parents=True, exist_ok=True)

    destination = staging_root / Path(original_name).name
    destination.write_bytes(content)

    artifact_path: Path = destination
    status_notes = [f"Saved upload to {artifact_path.relative_to(PROJECT_ROOT)}"]

    suffix = destination.suffix.lower()
    if suffix in {".zip", ".pbip"}:
        try:
            extract_dir = staging_root / destination.stem
            with zipfile.ZipFile(destination) as archive:
                archive.extractall(extract_dir)
            destination.unlink(missing_ok=True)

            pbip_dirs = [p for p in extract_dir.iterdir() if p.is_dir() and p.suffix.lower() == ".pbip"]
            if pbip_dirs:
                artifact_path = pbip_dirs[0]
            else:
                inner_items = list(extract_dir.iterdir())
                if len(inner_items) == 1 and inner_items[0].is_dir():
                    candidate = inner_items[0]
                    if candidate.suffix.lower() != ".pbip":
                        renamed = candidate.with_suffix(".pbip")
                        candidate.rename(renamed)
                        candidate = renamed
                    artifact_path = candidate
                else:
                    artifact_path = extract_dir
            status_notes.append("Extracted PBIP bundle")
        except zipfile.BadZipFile:
            status_notes.append("Upload is not a valid zip archive; kept original file")

    return {
        "artifact_path": artifact_path,
        "staging_root": staging_root,
        "message": ". ".join(status_notes),
    }


__all__ = [
    "ARTIFACTS_ROOT",
    "DEFAULT_INPUT_ROOT",
    "load_run",
    "load_runs",
    "run_pipeline",
    "save_uploaded_artifact",
]
