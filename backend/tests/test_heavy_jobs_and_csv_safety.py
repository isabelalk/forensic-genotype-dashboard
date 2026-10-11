import tempfile
import threading
import time
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import anyio
import pandas as pd
from anyio import CapacityLimiter
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services import heavy_jobs
from app.services.csv_safety import neutralize_dataframe

HEADER = (
    "##fileformat=VCFv4.2\n"
    '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n'
    "##contig=<ID=1>\n"
)


class HeavyJobLimiterTest(TestCase):
    def test_limiter_of_one_serialises_two_jobs(self) -> None:
        timeline: list[tuple[str, float]] = []

        def slow(name: str) -> None:
            timeline.append((f"{name}-start", time.monotonic()))
            time.sleep(0.2)
            timeline.append((f"{name}-end", time.monotonic()))

        async def main() -> None:
            async with anyio.create_task_group() as tg:
                tg.start_soon(heavy_jobs.run_heavy, slow, "a")
                tg.start_soon(heavy_jobs.run_heavy, slow, "b")

        with patch.object(heavy_jobs, "HEAVY_JOB_LIMITER", CapacityLimiter(1)):
            anyio.run(main)

        events = [name for name, _ in sorted(timeline, key=lambda item: item[1])]
        self.assertIn(events, (["a-start", "a-end", "b-start", "b-end"], ["b-start", "b-end", "a-start", "a-end"]))

    def test_health_answers_while_a_heavy_job_sleeps(self) -> None:
        settings = Settings(_env_file=None)
        application = create_app(settings)
        release = threading.Event()

        def block() -> dict:
            release.wait(5)
            return {"done": True}

        @application.get("/slow")
        async def slow():
            return await heavy_jobs.run_heavy(block)

        with TestClient(application) as client:
            worker = threading.Thread(target=lambda: client.get("/slow"))
            worker.start()
            time.sleep(0.1)
            started = time.monotonic()
            response = client.get("/health")
            elapsed = time.monotonic() - started
            release.set()
            worker.join(5)

        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 1.0)


class CsvSafetyTest(TestCase):
    def test_formula_prefixes_are_neutralised(self) -> None:
        df = pd.DataFrame({'=HYPERLINK("http://x")': ["+1", "-5", "@cmd", "\tx", "\ry", "AG"], "S1": ["AG", "", "CT", "=x", "1", "2"]})

        safe = neutralize_dataframe(df)

        self.assertEqual(list(safe.columns), ["'=HYPERLINK(\"http://x\")", "S1"])
        self.assertEqual(list(safe.iloc[:, 0]), ["'+1", "'-5", "'@cmd", "'\tx", "'\ry", "AG"])
        self.assertEqual(list(safe["S1"]), ["AG", "", "CT", "'=x", "1", "2"])
        self.assertEqual(list(df.columns)[0], '=HYPERLINK("http://x")')  # input untouched

    def test_convert_route_escapes_sample_name_in_csv_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            upload_dir = Path(tmp) / "uploads"
            upload_dir.mkdir()
            file_id = "55555555-5555-4555-8555-555555555555"
            (upload_dir / f"{file_id}.vcf").write_text(
                HEADER
                + '#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t=HYPERLINK("x")\tS2\n'
                + "1\t10\trs1\tA\tG\t.\tPASS\t.\tGT\t0/1\t1/1\n",
                encoding="utf-8",
            )
            markers = Path(tmp) / "markers.txt"
            markers.write_text("rs1\n", encoding="utf-8")
            settings = Settings(
                _env_file=None,
                upload_dir=str(upload_dir),
                artifact_dir=str(Path(tmp) / "artifacts"),
                hirisplex_markers_path=str(markers),
                plex34_markers_path=str(markers),
            )
            with patch("app.api.routes.vcf.settings", settings), TestClient(create_app(settings)) as client:
                convert = client.post("/api/vcf/convert", json={"file_id": file_id, "marker_type": "hirisplex"})
                full = client.get(f"/api/vcf/download-full/{file_id}")

        self.assertEqual(convert.status_code, 200, convert.text)
        self.assertIn("'=HYPERLINK", convert.json()["csv_data"])
        self.assertNotIn('\n=HYPERLINK', convert.json()["csv_data"])
        self.assertEqual(full.status_code, 200)
        self.assertIn("'=HYPERLINK", full.text)

    def test_unexpected_processor_error_returns_generic_500(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            upload_dir = Path(tmp) / "uploads"
            upload_dir.mkdir()
            file_id = "66666666-6666-4666-8666-666666666666"
            (upload_dir / f"{file_id}.vcf").write_text("x", encoding="utf-8")
            settings = Settings(_env_file=None, upload_dir=str(upload_dir), artifact_dir=str(Path(tmp) / "a"))

            def explode(*_args, **_kwargs):
                raise RuntimeError("boom /opt/secret")

            with (
                patch("app.api.routes.vcf.settings", settings),
                patch("app.api.routes.vcf._full_csv", explode),
                TestClient(create_app(settings), raise_server_exceptions=False) as client,
            ):
                response = client.get(f"/api/vcf/download-full/{file_id}")

        self.assertEqual(response.status_code, 500)
        self.assertTrue(response.json()["detail"].startswith("Internal server error. Reference: "))
        self.assertNotIn("/opt/secret", response.text)

    def test_unparseable_vcf_is_a_client_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            upload_dir = Path(tmp) / "uploads"
            upload_dir.mkdir()
            file_id = "77777777-7777-4777-8777-777777777777"
            (upload_dir / f"{file_id}.vcf").write_text("not a vcf at all\n", encoding="utf-8")
            settings = Settings(_env_file=None, upload_dir=str(upload_dir), artifact_dir=str(Path(tmp) / "a"))
            with patch("app.api.routes.vcf.settings", settings), TestClient(create_app(settings)) as client:
                response = client.post(f"/api/vcf/validate?file_id={file_id}")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "The VCF file could not be parsed.")
