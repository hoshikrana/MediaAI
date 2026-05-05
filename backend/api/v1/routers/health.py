import time
import torch
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import get_db
from backend.core.config import settings
from backend.core.dependencies import get_superuser, get_model_registry
from backend.orchestration.resilience import CIRCUIT_BREAKERS
from backend.orchestration.queue import task_queue
from backend.utils.cache import analysis_cache, rag_cache, user_cache

router = APIRouter()

@router.get("/")
async def health_check():
    """Fast liveness probe."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "uptime_seconds": time.time() - getattr(router.default_app.state, "start_time", time.time()).timestamp() if hasattr(router, 'default_app') else 0,
        "version": settings.VERSION
    }

@router.get("/ready")
async def readiness_probe(request):
    if getattr(request.app.state, "is_ready", False):
        return {"status": "ready"}
    return {"status": "starting_up"}, 503

@router.get("/detailed")
async def detailed_health(request, db: AsyncSession = Depends(get_db), registry = Depends(get_model_registry)):
    status = "healthy"
    warnings = []
    components = {}
    
    # Check DB
    db_start = time.monotonic()
    try:
        await db.execute(text("SELECT 1"))
        components["database"] = {"healthy": True, "response_ms": (time.monotonic() - db_start) * 1000}
    except Exception as e:
        components["database"] = {"healthy": False, "error": str(e)}
        status = "unhealthy"
        
    # Check GPU
    if torch.cuda.is_available():
        try:
            vram_total = torch.cuda.get_device_properties(0).total_memory // 1024 // 1024
            vram_free = torch.cuda.mem_get_info()[0] // 1024 // 1024
            components["gpu"] = {
                "healthy": True,
                "gpu_name": torch.cuda.get_device_name(0),
                "vram_total_mb": vram_total,
                "vram_free_mb": vram_free,
                "vram_used_percent": round((1 - vram_free/max(1, vram_total)) * 100, 1)
            }
        except Exception as e:
             components["gpu"] = {"healthy": False, "error": str(e)}
    else:
        components["gpu"] = {"healthy": True, "note": "No GPU available — running on CPU"}

    # Models & Queue
    components["models"] = registry.get_status() if registry else {"error": "Registry not loaded"}
    components["task_queue"] = {"active": task_queue._active_count, "healthy": task_queue._is_running}
    
    # Cache & Circuits
    components["cache"] = {
        "analysis_cache": analysis_cache.stats(),
        "rag_cache": rag_cache.stats(),
        "user_cache": user_cache.stats()
    }
    
    cb_states = {}
    for name, cb in CIRCUIT_BREAKERS.items():
        cb_states[name] = cb.get_status()
        if cb.state.value == "OPEN":
            status = "degraded" if status != "unhealthy" else "unhealthy"
            warnings.append(f"{name} circuit breaker is OPEN")
    components["circuit_breakers"] = cb_states

    return {
        "status": status,
        "uptime_seconds": time.time() - request.app.state.start_time.timestamp() if hasattr(request.app.state, 'start_time') else 0,
        "components": components,
        "warnings": warnings
    }

@router.get("/metrics")
async def get_metrics(superuser = Depends(get_superuser)):
    # Assuming AccessLogMiddleware populates a dictionary mapping endpoints to stats.
    # We return a stub here to fulfill the contract.
    return {
        "total_requests": 0,
        "total_errors": 0,
        "error_rate": 0.0,
        "endpoints": []
    }

@router.post("/circuit-breakers/{name}/reset")
async def reset_circuit(name: str, superuser = Depends(get_superuser)):
    if name in CIRCUIT_BREAKERS:
        CIRCUIT_BREAKERS[name].force_close()
        return {"status": "success", "message": f"Circuit {name} closed"}
    return {"status": "error", "message": "Circuit not found"}, 404
