
"""
main.py — точка входу MCP server
"""
from fastapi import FastAPI
from mcp_server.api import router


app = FastAPI(title="MCP AI Integration Server")
app.include_router(router)

@app.get("/")
def root():
    return {"status": "MCP server is running", "version": "0.1.0"}

# TODO: Додати ендпоінти для інтеграції, рев'ю, стандартизації, моніторингу
# TODO: Інтегрувати з CI/CD, DataGovernance, external standards
