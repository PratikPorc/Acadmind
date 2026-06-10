from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.logging_config import setup_logging
from app.db.neo4j import close_neo4j_driver, init_neo4j_driver
from app.db.redis_client import close_redis, init_redis
from app.middleware.api_gateway import ApiGatewayMiddleware
from app.middleware.gateway_log_store import configure_gateway_log_store
from app.services.demo_seed_service import seed_demo_once


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    init_neo4j_driver(settings)
    init_redis(settings)
    if settings.demo_seed_enabled:
        await seed_demo_once()
    yield
    await close_redis()
    await close_neo4j_driver()


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)
    configure_gateway_log_store(settings.gateway_log_buffer_size)

    app = FastAPI(
        title=settings.app_name,
        description="Unified Agentic AI for Academic Query Resolution and Memory Management",
        version="0.1.0",
        lifespan=lifespan,
        debug=settings.debug,
    )

    if settings.log_gateway_requests:
        app.add_middleware(ApiGatewayMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
