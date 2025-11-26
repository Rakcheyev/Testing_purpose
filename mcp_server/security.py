"""security.py — базові механізми безпеки MCP server.

Єдиний шар для:
- auth (tokens, API keys, future OAuth)
- sandbox-політик
- rate limiting
- audit sampling
- secrets management (через config/env)
"""

from collections import defaultdict
import time
import random
from typing import Callable, Awaitable

from fastapi import HTTPException, Request, status

from .config import MCPConfig


# === Auth ===

API_TOKENS = MCPConfig.API_TOKENS


def get_current_user(request: Request) -> str:
    """Перевірка токена з заголовка X-API-Token."""
    token = request.headers.get("X-API-Token")
    if not token or token not in API_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token",
        )
    return API_TOKENS[token]


# === Sandbox ===

def sandboxed(func: Callable) -> Callable:
    """Декоратор для ізоляції виконання (плейсхолдер політик sandbox)."""

    def wrapper(*args, **kwargs):
        # TODO: додати реальну sandbox-логіку (обмеження ресурсів, політики)
        return func(*args, **kwargs)

    return wrapper


# === Rate limiting ===

RATE_LIMIT = MCPConfig.RATE_LIMIT
RATE_PERIOD = MCPConfig.RATE_PERIOD
rate_limit_store = defaultdict(list)


async def rate_limiter(request: Request) -> None:
    """Простий rate limiting: N запитів на IP за T секунд."""
    ip = request.client.host
    now = time.time()
    rate_limit_store[ip] = [t for t in rate_limit_store[ip] if now - t < RATE_PERIOD]
    if len(rate_limit_store[ip]) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    rate_limit_store[ip].append(now)


# === Audit sampling ===

AUDIT_SAMPLE_RATE = MCPConfig.AUDIT_SAMPLE_RATE
audited_requests = []


async def audit_sampler(request: Request) -> None:
    """Вибіркове логування частини запитів."""
    if random.random() < AUDIT_SAMPLE_RATE:
        audited_requests.append(
            {
                "timestamp": time.time(),
                "ip": request.client.host,
                "path": request.url.path,
                "headers": dict(request.headers),
            }
        )


def get_audit_sample():
    """Повертає поточний список sampled-запитів."""
    return {"sampled_requests": audited_requests}


# TODO: Інтегрувати secrets management (vault/encrypted storage)
