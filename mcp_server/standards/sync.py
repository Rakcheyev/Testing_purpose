"""CLI to synchronise legacy standards into the canonical catalog schema."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path

from .reader import (
    CATALOG_PATH,
    LEGACY_STANDARDS_PATH,
    build_catalog,
    load_catalog,
    write_catalog,
)


def _normalise(payload: dict) -> dict:
    normalised = deepcopy(payload)
    normalised.pop("version", None)
    return normalised


def main() -> None:
    parser = argparse.ArgumentParser(description="Synchronise standards catalog")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate that the existing catalog matches the generated output",
    )
    args = parser.parse_args()

    if not LEGACY_STANDARDS_PATH.exists():
        catalog = load_catalog()
    else:
        catalog = build_catalog()

    if args.check:
        if not CATALOG_PATH.exists():
            print(
                json.dumps(
                    {
                        "status": "error",
                        "reason": "catalog_missing",
                        "message": "external/standards_catalog.json is not present",
                    }
                ),
                file=sys.stderr,
            )
            sys.exit(1)

        existing = json.loads(CATALOG_PATH.read_text())
        if _normalise(existing) != _normalise(catalog):
            print(
                json.dumps(
                    {
                        "status": "error",
                        "reason": "catalog_outdated",
                        "message": "external/standards_catalog.json is not in sync; run without --check and commit the changes.",
                    }
                ),
                file=sys.stderr,
            )
            sys.exit(1)

        print(
            json.dumps(
                {
                    "status": "ok",
                    "catalog": str(Path(CATALOG_PATH).name),
                    "rules": catalog.get("rule_count", len(catalog.get("rules", []))),
                }
            )
        )
        return

    write_catalog(catalog)
    print(
        json.dumps(
            {
                "status": "synced",
                "catalog": str(Path(CATALOG_PATH).name),
                "rules": catalog.get("rule_count", len(catalog.get("rules", []))),
            }
        )
    )


if __name__ == "__main__":
    main()
