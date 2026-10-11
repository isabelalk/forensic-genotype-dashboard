import asyncio
import logging
from contextlib import asynccontextmanager, suppress

import anyio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import hirisplex_results, plex34_structure, vcf
from app.core import settings as default_settings
from app.core.config import Settings
from app.core.internal_token import InternalTokenMiddleware, warn_if_unprotected
from app.core.request_id import REQUEST_ID_HEADER, RequestIdLogFilter, RequestIdMiddleware, request_id_from_scope
from app.services.retention import sweep_all

logger = logging.getLogger("app")


def _configure_logging() -> None:
    """INFO-level handler for the app's own loggers, tagged with the request ID.

    Uvicorn only configures its own loggers; without this the retention sweep
    and error logs would be dropped by the root logger's WARNING default.
    """
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.addFilter(RequestIdLogFilter())
    handler.setFormatter(logging.Formatter("%(levelname)s:     [%(name)s] [request_id=%(request_id)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


_configure_logging()


async def _retention_sweeper(settings: Settings) -> None:
    """Periodically removes expired uploads and artifacts, even with no traffic."""
    while True:
        await asyncio.sleep(settings.sweep_interval_seconds)
        try:
            await anyio.to_thread.run_sync(sweep_all, settings)
        except Exception:  # keep the sweeper alive; the next tick retries
            logger.exception("Retention sweep failed")


def create_app(settings: Settings) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        warn_if_unprotected(settings.api_shared_secret)
        sweeper = asyncio.create_task(_retention_sweeper(settings))
        try:
            yield
        finally:
            sweeper.cancel()
            with suppress(asyncio.CancelledError):
                await sweeper

    application = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        description="API for HIrisPlex-S and PLEX-34 phenotypic modeling",
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
    )

    # Middleware order (outermost first): request ID -> CORS -> shared-secret check -> routes
    application.add_middleware(InternalTokenMiddleware, secret=settings.api_shared_secret)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type"],
    )
    application.add_middleware(RequestIdMiddleware)

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = request_id_from_scope(request.scope)
        logger.exception(
            "Unhandled error [request_id=%s] on %s %s", request_id, request.method, request.url.path
        )
        return JSONResponse(
            {"detail": f"Internal server error. Reference: {request_id}"},
            status_code=500,
            headers={REQUEST_ID_HEADER: request_id},
        )

    application.include_router(vcf.router)
    application.include_router(plex34_structure.router)
    application.include_router(hirisplex_results.router)

    @application.get("/")
    async def root():
        """Root endpoint"""
        return {"message": "HIrisPlex-S API", "version": settings.app_version}

    @application.get("/health")
    async def health():
        """Health check endpoint"""
        return {"status": "ok"}

    return application


app = create_app(default_settings)
