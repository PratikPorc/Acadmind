import logging
import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging_config import request_id_ctx, user_email_ctx
from app.core.security import decode_supabase_jwt
from app.middleware.gateway_log_store import GatewayLogEntry, gateway_log_store

logger = logging.getLogger("acadmind.gateway")

SKIP_VERBOSE_PATHS = {"/api/v1/health", "/api/v1/gateway/logs"}


class ApiGatewayMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
        request_id_ctx.set(request_id)

        user_email: str | None = None
        user_role: str | None = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ").strip()
            user = decode_supabase_jwt(token)
            if user:
                user_email = user.email
                user_role = user.role.value
                user_email_ctx.set(user_email)

        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        query = str(request.url.query) if request.url.query else ""
        method = request.method

        if path not in SKIP_VERBOSE_PATHS:
            logger.info(
                "→ %s %s%s | ip=%s",
                method,
                path,
                f"?{query}" if query else "",
                client_ip,
            )

        start = time.perf_counter()
        error_detail: str | None = None
        status_code = 500
        response: Response | None = None

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            error_detail = str(exc)
            logger.exception("Unhandled error for %s %s", method, path)
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            gateway_log_store.add(
                GatewayLogEntry(
                    request_id=request_id,
                    method=method,
                    path=path,
                    query=query,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    client_ip=client_ip,
                    user_email=user_email,
                    user_role=user_role,
                    error=error_detail,
                )
            )
            request_id_ctx.set(None)
            user_email_ctx.set(None)

        assert response is not None
        response.headers["X-Request-ID"] = request_id

        if path not in SKIP_VERBOSE_PATHS:
            level = logging.INFO
            if status_code >= 500:
                level = logging.ERROR
            elif status_code >= 400:
                level = logging.WARNING
            logger.log(
                level,
                "← %s %s | %s | %.2fms | role=%s",
                status_code,
                path,
                "OK" if status_code < 400 else "ERR",
                duration_ms,
                user_role or "anonymous",
            )

        return response
