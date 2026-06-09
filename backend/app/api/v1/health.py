from fastapi import APIRouter

from app.config import get_settings
from app.db.neo4j import check_neo4j_connection
from app.db.redis_client import check_redis_connection
from app.db.supabase import check_supabase_config
from app.models.schemas import HealthResponse, HealthStatus, ServiceHealth

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    settings = get_settings()
    services: list[ServiceHealth] = []

    neo4j_ok, neo4j_detail = await check_neo4j_connection()
    services.append(
        ServiceHealth(
            name="neo4j",
            status=HealthStatus.ok if neo4j_ok else HealthStatus.error,
            detail=neo4j_detail,
        )
    )

    redis_ok, redis_detail = await check_redis_connection()
    services.append(
        ServiceHealth(
            name="redis",
            status=HealthStatus.ok if redis_ok else HealthStatus.error,
            detail=redis_detail,
        )
    )

    supabase_ok, supabase_detail = check_supabase_config()
    services.append(
        ServiceHealth(
            name="supabase",
            status=HealthStatus.ok if supabase_ok else HealthStatus.degraded,
            detail=supabase_detail,
        )
    )

    from app.core.llm import check_llm_config

    llm_ok, llm_detail = check_llm_config()
    services.append(
        ServiceHealth(
            name="llm",
            status=HealthStatus.ok if llm_ok else HealthStatus.degraded,
            detail=llm_detail,
        )
    )

    critical_ok = neo4j_ok and redis_ok
    overall = HealthStatus.ok if critical_ok else HealthStatus.degraded
    if not neo4j_ok and not redis_ok:
        overall = HealthStatus.error

    return HealthResponse(
        status=overall,
        app=settings.app_name,
        environment=settings.app_env,
        services=services,
    )
