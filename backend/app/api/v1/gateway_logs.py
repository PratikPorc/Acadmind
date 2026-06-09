from fastapi import APIRouter, Query

from app.middleware.gateway_log_store import gateway_log_store
from app.models.schemas import GatewayLogResponse

router = APIRouter()


@router.get("/logs", response_model=GatewayLogResponse)
async def list_gateway_logs(
    limit: int = Query(default=50, ge=1, le=200),
) -> GatewayLogResponse:
    """Recent API gateway request logs (dev observability)."""
    entries = gateway_log_store.list(limit=limit)
    return GatewayLogResponse(count=len(entries), entries=entries)
