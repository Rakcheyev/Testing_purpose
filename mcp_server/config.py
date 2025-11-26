"""
config.py — конфігурація MCP server
"""
import os

class MCPConfig:
    SERVER_HOST = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8080"))
    DEBUG = bool(int(os.getenv("MCP_DEBUG", "1")))
    # Параметри безпеки (можуть бути винесені у secrets manager)
    API_TOKENS = {"demo-token": "user1"}
    RATE_LIMIT = int(os.getenv("MCP_RATE_LIMIT", "5"))          # запитів
    RATE_PERIOD = int(os.getenv("MCP_RATE_PERIOD", "10"))       # секунд
    AUDIT_SAMPLE_RATE = float(os.getenv("MCP_AUDIT_SAMPLE", "0.3"))  # частка запитів

    # TODO: Додати secrets management (vault, encrypted storage)
