import gzip
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

VCF_TEXT = (
    "##fileformat=VCFv4.2\n"
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS1\tS2\n"
    "1\t10\trs1\tA\tG\t.\tPASS\t.\tGT\t0/1\t1/1\n"
    "1\t20\trs2\tC\tT\t.\tPASS\t.\tGT\t0/0\t./.\n"
)


class UploadRoutesTest(TestCase):
    """Drives /api/vcf/upload and DELETE through HTTP with a temporary upload directory."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.upload_dir = Path(self.tmp.name) / "uploads"
        self.artifact_dir = Path(self.tmp.name) / "artifacts"
        self.settings = Settings(
            _env_file=None,
            upload_dir=str(self.upload_dir),
            artifact_dir=str(self.artifact_dir),
            max_upload_size=1024,
            max_uncompressed_upload_size=4096,
            max_upload_dir_bytes=10_000,
            max_vcf_samples=3,
            max_vcf_variants=5,
            max_vcf_cells=10,
        )
        self.patchers = [
            patch("app.api.routes.vcf.settings", self.settings),
            patch("app.api.routes.plex34_structure.settings", self.settings),
        ]
        for patcher in self.patchers:
            patcher.start()
        self.client = TestClient(create_app(self.settings), raise_server_exceptions=False)
        self.client.__enter__()

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)
        for patcher in self.patchers:
            patcher.stop()
        self.tmp.cleanup()

    def _upload(self, name: str, content: bytes):
        return self.client.post("/api/vcf/upload", files={"file": (name, content, "application/octet-stream")})

    def _stored_files(self) -> list[Path]:
        return sorted(p for p in self.upload_dir.iterdir() if p.is_file()) if self.upload_dir.exists() else []

    def test_valid_upload_is_stored(self) -> None:
        response = self._upload("sample.vcf", VCF_TEXT.encode())
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["size"], len(VCF_TEXT.encode()))
        self.assertEqual([p.name for p in self._stored_files()], [f"{body['file_id']}.vcf"])

    def test_oversized_upload_is_rejected_and_removed(self) -> None:
        response = self._upload("big.vcf", b"#" * 2000)
        self.assertEqual(response.status_code, 413)
        self.assertIn("1024", response.json()["detail"])
        self.assertEqual(self._stored_files(), [])

    def test_gzip_named_vcf_is_rejected(self) -> None:
        response = self._upload("bomb.vcf", gzip.compress(VCF_TEXT.encode()))
        self.assertEqual(response.status_code, 400)
        self.assertIn(".vcf.gz", response.json()["detail"])
        self.assertEqual(self._stored_files(), [])

    def test_plain_text_named_vcf_gz_is_rejected(self) -> None:
        response = self._upload("fake.vcf.gz", VCF_TEXT.encode())
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self._stored_files(), [])

    def test_shape_limit_violation_is_rejected_and_removed(self) -> None:
        too_many_samples = VCF_TEXT.replace("\tS1\tS2\n", "\tS1\tS2\tS3\tS4\n").replace(
            "\t0/1\t1/1\n", "\t0/1\t1/1\t0/0\t0/0\n"
        ).replace("\t0/0\t./.\n", "\t0/0\t./.\t0/0\t0/0\n")
        response = self._upload("wide.vcf", too_many_samples.encode())
        self.assertEqual(response.status_code, 400)
        self.assertIn("maximum allowed is 3", response.json()["detail"])
        self.assertEqual(self._stored_files(), [])

    def test_wrong_extension_is_rejected(self) -> None:
        response = self._upload("notes.txt", VCF_TEXT.encode())
        self.assertEqual(response.status_code, 400)

    def test_near_quota_directory_rejects_with_507_and_writes_nothing(self) -> None:
        self.upload_dir.mkdir(parents=True)
        filler = self.upload_dir / "11111111-1111-4111-8111-111111111111.vcf"
        filler.write_bytes(b"x" * 9_500)  # 10_000 - 9_500 < max_upload_size (1024)

        response = self._upload("sample.vcf", VCF_TEXT.encode())

        self.assertEqual(response.status_code, 507)
        self.assertEqual([p.name for p in self._stored_files()], [filler.name])

    def test_quota_crossed_mid_stream_returns_507_and_removes_partial(self) -> None:
        self.upload_dir.mkdir(parents=True)
        filler = self.upload_dir / "22222222-2222-4222-8222-222222222222.vcf"
        filler.write_bytes(b"x" * 8_900)  # passes pre-check (8_900 + 1024 <= 10_000), remaining = 1_100
        with patch("app.services.upload_storage.UPLOAD_CHUNK_SIZE", 100):
            self.settings.max_upload_size = 5_000
            response = self._upload("sample.vcf", b"#" * 1_200)

        self.assertEqual(response.status_code, 507)
        self.assertEqual([p.name for p in self._stored_files()], [filler.name])

    def test_delete_existing_upload(self) -> None:
        file_id = self._upload("sample.vcf", VCF_TEXT.encode()).json()["file_id"]

        response = self.client.delete(f"/api/vcf/upload/{file_id}")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(self._stored_files(), [])
        self.assertEqual(self.client.post(f"/api/vcf/validate?file_id={file_id}").status_code, 404)

    def test_delete_unknown_and_malformed_ids(self) -> None:
        self.assertEqual(self.client.delete("/api/vcf/upload/not-a-uuid").status_code, 404)
        self.assertEqual(
            self.client.delete("/api/vcf/upload/33333333-3333-4333-8333-333333333333").status_code, 404
        )


class BackgroundSweeperTest(TestCase):
    def test_expired_upload_is_removed_without_any_request(self) -> None:
        import os
        import time

        with tempfile.TemporaryDirectory() as tmp:
            upload_dir = Path(tmp) / "uploads"
            upload_dir.mkdir()
            expired = upload_dir / "44444444-4444-4444-8444-444444444444.vcf"
            expired.write_bytes(b"x")
            old = time.time() - 10_000
            os.utime(expired, (old, old))
            settings = Settings(
                _env_file=None,
                upload_dir=str(upload_dir),
                artifact_dir=str(Path(tmp) / "artifacts"),
                sweep_interval_seconds=0.1,
            )

            with TestClient(create_app(settings)):
                deadline = time.time() + 3
                while expired.exists() and time.time() < deadline:
                    time.sleep(0.05)

            self.assertFalse(expired.exists())
