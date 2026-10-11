import hmac
import logging

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

INTERNAL_TOKEN_HEADER = b"x-internal-token"
PROTECTED_PREFIX = "/api/"

logger = logging.getLogger(__name__)


class InternalTokenMiddleware:
    """Rejects /api/* requests that do not carry the shared secret the proxy injects.

    When `secret` is empty the middleware passes everything through; the app logs
    a warning at startup in that case so an unprotected deployment is visible.
    """

    def __init__(self, app: ASGIApp, secret: str) -> None:
        self.app = app
        self.secret = secret.encode("utf-8")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not self.secret or not scope["path"].startswith(PROTECTED_PREFIX):
            await self.app(scope, receive, send)
            return

        if not self._has_valid_token(scope):
            response = JSONResponse({"detail": "Forbidden"}, status_code=403)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)

    def _has_valid_token(self, scope: Scope) -> bool:
        for name, value in scope.get("headers", []):
            if name == INTERNAL_TOKEN_HEADER:
                return hmac.compare_digest(value, self.secret)
        return False


def warn_if_unprotected(secret: str) -> None:
    if not secret:
        logger.warning(
            "API_SHARED_SECRET is empty: /api routes accept requests from any caller. "
            "Set it (and the proxy's BACKEND_SHARED_SECRET) for any non-local deployment."
        )
