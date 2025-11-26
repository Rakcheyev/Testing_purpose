"""
security.py — базові механізми безпеки MCP server
"""
# TODO: Додати авторизацію, secrets management, контроль доступу

def check_access(token: str) -> bool:
    # Плейсхолдер: перевірка токена
    return token == "test-token"
