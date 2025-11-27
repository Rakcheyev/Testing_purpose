"""CLI to synchronise legacy standards into the canonical catalog schema."""

from __future__ import annotations

import json
from pathlib import Path

from .reader import (
    CATALOG_PATH,
    LEGACY_STANDARDS_PATH,
    build_catalog,
    load_catalog,
    write_catalog,
)


def main() -> None:
    if not LEGACY_STANDARDS_PATH.exists():
        catalog = load_catalog()
    else:
        catalog = build_catalog()
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
