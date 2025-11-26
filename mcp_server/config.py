"""
config.py — конфігурація MCP server
"""
import os

class MCPConfig:
    SERVER_HOST = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8080"))
    DEBUG = bool(int(os.getenv("MCP_DEBUG", "1")))
    # TODO: Додати параметри безпеки, інтеграції, secrets management
