import logging
from unittest import TestCase

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

ORIGIN = "http://localhost:5173"


def make_client(**overrides) -> TestClient:
    settings = Settings(_env_file=None, cors_origins=ORIGIN, **overrides)
    application = create_app(settings)

    @application.get("/boom")
    async def boom():
        raise RuntimeError("secret /srv/private/path leaked")

    return TestClient(application, raise_server_exceptions=False)


class RequestIdTest(TestCase):
    def test_generated_request_id_is_returned(self) -> None:
        # Given: a request without X-Request-ID.
        with make_client() as client:
            # When: any endpoint is called.
            response = client.get("/health")

        # Then: a non-empty request ID header is present.
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers.get("x-request-id"))

    def test_supplied_request_id_is_echoed(self) -> None:
        with make_client() as client:
            response = client.get("/health", headers={"X-Request-ID": "abc-123"})

        self.assertEqual(response.headers["x-request-id"], "abc-123")

    def test_invalid_supplied_request_id_is_replaced(self) -> None:
        with make_client() as client:
            response = client.get("/health", headers={"X-Request-ID": "bad id with spaces!"})

        self.assertNotEqual(response.headers["x-request-id"], "bad id with spaces!")
        self.assertTrue(response.headers["x-request-id"])


class UnhandledErrorTest(TestCase):
    def test_unexpected_exception_returns_generic_body_with_request_id(self) -> None:
        # Given: a route that raises an exception containing a server path.
        with make_client() as client, self.assertLogs("app", level="ERROR") as logs:
            # When: the route is called with a known request ID.
            response = client.get("/boom", headers={"X-Request-ID": "req-42"})

        # Then: the body is generic, carries only the ID, and the log has the traceback with the ID.
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "Internal server error. Reference: req-42"})
        self.assertNotIn("secret", response.text)
        self.assertNotIn("/srv/private/path", response.text)
        self.assertEqual(response.headers["x-request-id"], "req-42")
        joined = "\n".join(logs.output)
        self.assertIn("req-42", joined)
        self.assertIn("RuntimeError: secret /srv/private/path leaked", joined)


class InternalTokenTest(TestCase):
    def test_missing_header_is_forbidden(self) -> None:
        with make_client(api_shared_secret="s3cret") as client:
            response = client.get("/api/vcf/markers/plex34")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "Forbidden"})

    def test_wrong_header_is_forbidden(self) -> None:
        with make_client(api_shared_secret="s3cret") as client:
            response = client.get("/api/vcf/markers/plex34", headers={"X-Internal-Token": "nope"})

        self.assertEqual(response.status_code, 403)

    def test_correct_header_is_served(self) -> None:
        with make_client(api_shared_secret="s3cret") as client:
            response = client.get("/api/vcf/markers/plex34", headers={"X-Internal-Token": "s3cret"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["marker_type"], "plex34")

    def test_health_needs_no_header(self) -> None:
        with make_client(api_shared_secret="s3cret") as client:
            response = client.get("/health")

        self.assertEqual(response.status_code, 200)

    def test_empty_secret_passes_and_warns(self) -> None:
        with self.assertLogs("app.core.internal_token", level="WARNING") as logs:
            with make_client(api_shared_secret="") as client:
                response = client.get("/api/vcf/markers/plex34")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(any("API_SHARED_SECRET is empty" in line for line in logs.output))


class CorsAndDocsTest(TestCase):
    def test_preflight_from_unknown_origin_is_not_allowed(self) -> None:
        with make_client() as client:
            response = client.options(
                "/api/vcf/markers/plex34",
                headers={
                    "Origin": "https://evil.example",
                    "Access-Control-Request-Method": "POST",
                },
            )

        self.assertNotIn("access-control-allow-origin", response.headers)

    def test_preflight_from_known_origin_has_no_credentials_header(self) -> None:
        with make_client() as client:
            response = client.options(
                "/api/vcf/upload",
                headers={
                    "Origin": ORIGIN,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], ORIGIN)
        self.assertIn("POST", response.headers["access-control-allow-methods"])
        self.assertNotIn("access-control-allow-credentials", response.headers)

    def test_docs_hidden_outside_development(self) -> None:
        with make_client(app_env="production") as client:
            statuses = {path: client.get(path).status_code for path in ("/docs", "/redoc", "/openapi.json")}

        self.assertEqual(statuses, {"/docs": 404, "/redoc": 404, "/openapi.json": 404})

    def test_docs_available_in_development(self) -> None:
        with make_client(app_env="development") as client:
            response = client.get("/docs")

        self.assertEqual(response.status_code, 200)
