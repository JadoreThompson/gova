from __future__ import annotations

from collections.abc import Iterable

from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from core.exception import ExceptionHandler, load_exception_handlers


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Convert service exceptions into their configured HTTP responses."""

    def __init__(
        self,
        app,
        handlers: Iterable[type[ExceptionHandler]] | None = None,
    ):
        super().__init__(app)
        self.exception_map = load_exception_handlers(handlers)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            http_exception = self._resolve(exc)
            if http_exception is None:
                raise

            return JSONResponse(
                status_code=http_exception.status_code,
                content={"detail": http_exception.detail},
                headers=http_exception.headers,
            )

    def _resolve(self, exc: Exception) -> HTTPException | None:
        for exc_type in type(exc).__mro__:
            if exc_type in self.exception_map:
                return self.exception_map[exc_type]
