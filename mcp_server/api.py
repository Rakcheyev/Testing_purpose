"""api.py — ендпоінти MCP server для інтеграції, рев'ю, стандартизації."""

from fastapi import FastAPI, APIRouter, Request, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, ValidationError, constr
import asyncio


from .security import (
    sandboxed,
    get_current_user,
    rate_limiter,
    audit_sampler,
    get_audit_sample as fetch_audit_sample,
)
from .orchestration import session_manager


app = FastAPI()
router = APIRouter()

app.include_router(router)

@router.get("/health")
def health(request: Request):
    session_id = request.headers.get("X-Session-ID")
    return {"status": "ok", "session_id": session_id}

# MCP: Старт сесії, генерація session_id
@router.post("/session/start")
def start_session(request: Request):
    user = request.headers.get("X-User-ID", "system")
    metadata = {}
    if request.client and request.client.host:
        metadata["ip"] = request.client.host
    session_id = session_manager.start_session(user=user, metadata=metadata or None)
    return {"session_id": session_id, "status": session_manager.sessions[session_id]["status"]}

# MCP: Приклад ендпоінта, який очікує session_id у запиті
@router.post("/process")
async def process(request: Request):
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    action = payload.get("action", "process")
    data = payload.get("data") or payload.get("payload")
    status = payload.get("status", "ok")
    user = request.headers.get("X-User-ID", "system")
    try:
        entry = session_manager.process_session(
            session_id,
            action=action,
            user=user,
            payload=data,
            status=status,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found") from None
    response = {
        "session_id": session_id,
        "action": action,
        "status": entry["status"],
        "session_state": session_manager.sessions[session_id]["status"],
    }
    return response


@router.post("/session/close")
async def close_session(request: Request):
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    status = payload.get("status", "closed")
    user = request.headers.get("X-User-ID", "system")
    try:
        entry = session_manager.close_session(session_id, user=user, status=status)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found") from None
    return {
        "session_id": session_id,
        "status": entry["status"],
        "session_state": session_manager.sessions[session_id]["status"],
        "closed_at": entry["timestamp"],
    }

# MCP: Async workflow — асинхронний ендпоінт
@router.post("/async-task")
async def async_task(request: Request):
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        return {"error": "Session ID required"}
    # Симуляція асинхронної задачі (наприклад, довгий процес)
    await asyncio.sleep(2)
    return {"session_id": session_id, "result": "async completed"}

# MCP: Async workflow — запуск задачі з callback (webhook)
@router.post("/async-task-callback")
def async_task_callback(request: Request, background_tasks: BackgroundTasks):
    session_id = request.headers.get("X-Session-ID")
    callback_url = request.headers.get("X-Callback-URL")
    if not session_id:
        return {"error": "Session ID required"}
    if not callback_url:
        return {"error": "Callback URL required"}
    # Симуляція асинхронної задачі з callback
    def notify():
        import requests
        # ... тут може бути реальна логіка ...
        requests.post(callback_url, json={"session_id": session_id, "result": "async completed"})
    background_tasks.add_task(notify)
    return {"session_id": session_id, "status": "async started", "callback": callback_url}

# MCP: Async workflow — polling (статус задачі)
async_tasks_status = {}

@router.post("/async-task-polling")
def async_task_polling(request: Request, background_tasks: BackgroundTasks):
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        return {"error": "Session ID required"}
    # Симуляція запуску задачі
    def run_task():
        import time
        time.sleep(2)
        async_tasks_status[session_id] = "completed"
    async_tasks_status[session_id] = "running"
    background_tasks.add_task(run_task)
    return {"session_id": session_id, "status": "async started"}

@router.get("/async-task-status")
def async_task_status(request: Request):
    session_id = request.headers.get("X-Session-ID")
    status = async_tasks_status.get(session_id, "not found")
    return {"session_id": session_id, "status": status}

# MCP: Ендпоінт для отримання списку можливостей (capabilities)
@router.get("/capabilities")
def get_capabilities():
    capabilities = [
        {
            "resource": "PBIP",
            "actions": ["review", "validate", "deploy", "export"],
            "formats": ["TMDL", "JSON", "YAML"]
        },
        {
            "resource": "DAX",
            "actions": ["lint", "validate", "optimize"],
            "formats": [".dax", ".txt"]
        },
        {
            "resource": "M-код",
            "actions": ["lint", "validate", "transform"],
            "formats": [".pq", ".txt"]
        },
        {
            "resource": "SQL",
            "actions": ["validate", "execute"],
            "formats": [".sql", "T-SQL"]
        },
        {
            "resource": "External data",
            "actions": ["parse", "validate", "import"],
            "formats": [".csv", ".xlsx", "API"]
        }
    ]
    return {"capabilities": capabilities}

# MCP: Capability negotiation — узгодження можливостей між клієнтом і сервером
@router.post("/capabilities/negotiate")
async def negotiate_capabilities(request: Request):
    client_caps = (await request.json()) if hasattr(request, 'json') else request.json()
    server_caps = {
        "PBIP": ["review", "validate", "deploy", "export"],
        "DAX": ["lint", "validate", "optimize"],
        "M-код": ["lint", "validate", "transform"],
        "SQL": ["validate", "execute"],
        "External data": ["parse", "validate", "import"]
    }
    negotiated = {}
    for resource, actions in client_caps.items():
        if resource in server_caps:
            negotiated[resource] = list(set(actions) & set(server_caps[resource]))
    return {"negotiated": negotiated}

@router.get("/secure/health")
@sandboxed
async def secure_health(request: Request, user: str = Depends(get_current_user)):
    session_id = request.headers.get("X-Session-ID")
    return {"status": "ok", "session_id": session_id, "user": user}

# Валідація та санітизація для payload
class ProcessPayload(BaseModel):
    data: constr(strip_whitespace=True, min_length=1, max_length=256)

@router.post("/process/validated")
async def process_validated(request: Request):
    session_id = request.headers.get("X-Session-ID")
    try:
        payload = await request.json()
        validated = ProcessPayload(**payload)
    except (ValidationError, Exception) as e:
        return {"error": "Invalid input", "details": str(e)}
    # ... тут логіка обробки ...
    return {"session_id": session_id, "result": "validated", "data": validated.data}

@router.get("/limited/health")
async def limited_health(request: Request):
    await rate_limiter(request)
    session_id = request.headers.get("X-Session-ID")
    return {"status": "ok", "session_id": session_id}

@router.get("/sampled/health")
async def sampled_health(request: Request):
    await audit_sampler(request)
    session_id = request.headers.get("X-Session-ID")
    return {"status": "ok", "session_id": session_id}

@router.get("/audit/sampled")
def get_audit_sample():
    return fetch_audit_sample()

@router.post("/metadata/sync")
async def sync_metadata(request: Request):
    payload = await request.json()
    # Симуляція оновлення/синхронізації метаданих
    # payload: {"model_id": str, "metadata": {...}}
    model_id = payload.get("model_id")
    metadata = payload.get("metadata")
    # Тут може бути логіка збереження/оновлення у БД або файлі
    # Для прикладу — просто повертаємо отримане
    return {"model_id": model_id, "metadata": metadata, "status": "synced"}

# MCP: Ендпоінт для інтеграції з зовнішніми системами
@router.post("/integration")
async def integration(request: Request):
    payload = await request.json()
    # stub-логіка: просто повертаємо отримане
    return {"status": "ok", "integration_payload": payload}

# MCP: Ендпоінт для рев'ю PBIP, DAX, M-коду
@router.post("/review")
async def review(request: Request):
    payload = await request.json()
    # stub-логіка: повертаємо тип ресурсу та статус
    resource_type = payload.get("resource_type", "unknown")
    return {"status": "reviewed", "resource_type": resource_type}

# MCP: Ендпоінт для перевірки відповідності стандартам
@router.post("/standardize")
async def standardize(request: Request):
    payload = await request.json()
    # stub-логіка: повертаємо результат перевірки
    resource_type = payload.get("resource_type", "unknown")
    return {"status": "standardized", "resource_type": resource_type, "result": "ok"}

# MCP: Ендпоінт для моніторингу сервісу
@router.get("/monitoring")
async def monitoring():
    # stub-логіка: повертаємо статус та timestamp
    import time
    return {"status": "active", "timestamp": time.time()}
