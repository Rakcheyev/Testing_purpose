"""
standards/ — модулі для роботи зі стандартами MCP.

Використовуйте `mcp_server.standards.reader` для завантаження та перетворення
легасі-конфігурацій у єдиний каталог правил, а `mcp_server.standards.sync`
для генерації (оновлення) JSON-схеми стандартів у `external/standards_catalog.json`.
"""

from .reader import (
	CATALOG_PATH,
	LEGACY_STANDARDS_PATH,
	StandardRule,
	build_catalog,
	iter_rules,
	load_catalog,
	write_catalog,
)

__all__ = [
	"CATALOG_PATH",
	"LEGACY_STANDARDS_PATH",
	"StandardRule",
	"build_catalog",
	"iter_rules",
	"load_catalog",
	"write_catalog",
]
