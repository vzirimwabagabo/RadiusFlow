import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("radiusflow.requests")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        started_at = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started_at) * 1000
        logger.info("%s %s %s %.2fms", request.method, request.url.path, response.status_code, duration_ms)
        return response
