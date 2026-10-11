import tempfile
import zipfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services import plex34_structure
from app.services._plex34_structure_io import (
    Plex34StructureConfigError,
    Plex34StructureDataError,
    Plex34StructureOutputTooLargeError,
    PopulationEntry,
    StructureInputData,
    VcfMarker,
    load_marker_ids,
    parse_vcf,
    write_structure_input,
)
from app.services.plex34_structure import (
    Plex34StructureError,
    Plex34StructureService,
    StructureArtifactRequest,
    StructureTemplatePaths,
)

DATA_DIR = Path(__file__).resolve().parents[1] / "app" / "data"
FILE_ID = "88888888-8888-4888-8888-888888888888"
VCF_TEXT = (
    "##fileformat=VCFv4.2\n"
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS1\tS2\n"
    "1\t10\trs1321333\tA\tG\t.\tPASS\t.\tGT\t0/1\t1/1\n"
    "1\t20\trs917118\tC\tT\t.\tPASS\t.\tGT\t0/0\t./.\n"
)


class StructureIoTest(TestCase):
    def test_writer_stops_at_byte_cap(self) -> None:
        markers = {"m1": VcfMarker(marker_id="m1", genotypes={})}
        data = StructureInputData(
            samples=[f"S{i}" for i in range(200)],
            ordered_markers=["m1"],
            markers=markers,
            population={"S0": PopulationEntry(pop_id=1, popflag=1)},
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "input.txt"
            with self.assertRaisesRegex(Plex34StructureOutputTooLargeError, "1024"):
                write_structure_input(output, data, max_bytes=1024)
            self.assertLessEqual(output.stat().st_size, 1024)
            written = write_structure_input(output, data, max_bytes=None)
            self.assertEqual(written, output.stat().st_size)

    def test_missing_marker_file_is_a_config_error_not_a_data_error(self) -> None:
        with self.assertRaises(Plex34StructureConfigError) as caught:
            load_marker_ids(Path("/nonexistent/markers.txt"))
        self.assertNotIsInstance(caught.exception, Plex34StructureDataError)

    def test_binary_vcf_is_a_data_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bin.vcf"
            path.write_bytes(b"\xff\xfe\x00binary")
            with self.assertRaisesRegex(Plex34StructureDataError, "UTF-8"):
                parse_vcf(path, ["rs1"])


class StructureServiceTest(TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.vcf = root / "sample.vcf"
        self.vcf.write_text(VCF_TEXT, encoding="utf-8")
        self.artifact_root = root / "artifacts"
        self.artifact_root.mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _request(self, **overrides) -> StructureArtifactRequest:
        values = dict(
            vcf_path=self.vcf,
            marker_path=DATA_DIR / "plex34_id.txt",
            template_paths=StructureTemplatePaths(
                population_csv=DATA_DIR / "plex34_structure" / "metapop_3202samples.csv",
                mainparams=DATA_DIR / "plex34_structure" / "mainparams",
                extraparams=DATA_DIR / "plex34_structure" / "extraparams",
            ),
            artifact_root=self.artifact_root,
            max_artifact_age_seconds=1800,
            max_artifact_count=100,
            max_artifact_dir_bytes=512 * 1024 * 1024,
            max_structure_input_bytes=50 * 1024 * 1024,
        )
        values.update(overrides)
        return StructureArtifactRequest(**values)

    def test_generates_zip(self) -> None:
        artifact = Plex34StructureService.generate_artifact(self._request())
        self.assertTrue(artifact.zip_path.exists())
        with zipfile.ZipFile(artifact.zip_path) as archive:
            self.assertEqual(sorted(archive.namelist()), ["extraparams", "mainparams", "plex34_structure_input.txt"])

    def test_injected_zip_failure_leaves_no_directory(self) -> None:
        def broken_zip(*_args, **_kwargs):
            raise OSError("disk gone")

        with patch.object(plex34_structure, "write_zip", broken_zip):
            with self.assertRaises(OSError):
                Plex34StructureService.generate_artifact(self._request())

        self.assertEqual(list(self.artifact_root.iterdir()), [])

    def test_output_over_cap_is_a_user_error_and_leaves_no_directory(self) -> None:
        with self.assertRaisesRegex(Plex34StructureError, "maximum allowed is 10"):
            Plex34StructureService.generate_artifact(self._request(max_structure_input_bytes=10))

        self.assertEqual(list(self.artifact_root.iterdir()), [])

    def test_byte_quota_evicts_oldest_before_generation(self) -> None:
        import os
        import time

        old = self.artifact_root / ("a" * 32)
        old.mkdir()
        (old / "plex34_structure_x.zip").write_bytes(b"x" * 900)
        stale = time.time() - 600
        os.utime(old, (stale, stale))

        Plex34StructureService.generate_artifact(
            self._request(max_artifact_dir_bytes=1000, max_structure_input_bytes=500)
        )

        self.assertFalse(old.exists())
        self.assertEqual(len(list(self.artifact_root.iterdir())), 1)

    def test_old_artifact_is_removed_on_generation(self) -> None:
        import os
        import time

        old = self.artifact_root / ("b" * 32)
        old.mkdir()
        stale = time.time() - 1861
        os.utime(old, (stale, stale))

        Plex34StructureService.generate_artifact(self._request())

        self.assertFalse(old.exists())


class StructureRoutesTest(TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.upload_dir = root / "uploads"
        self.upload_dir.mkdir()
        (self.upload_dir / f"{FILE_ID}.vcf").write_text(VCF_TEXT, encoding="utf-8")
        self.base = dict(_env_file=None, upload_dir=str(self.upload_dir), artifact_dir=str(root / "artifacts"))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _client(self, **overrides) -> TestClient:
        settings = Settings(**self.base, **overrides)
        self.patcher = patch("app.api.routes.plex34_structure.settings", settings)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        return TestClient(create_app(settings), raise_server_exceptions=False)

    def test_missing_marker_file_gives_generic_500_without_path(self) -> None:
        with self._client(plex34_markers_path="/srv/missing_markers.txt") as client:
            response = client.post(f"/api/vcf/plex34/structure-input?file_id={FILE_ID}")

        self.assertEqual(response.status_code, 500)
        self.assertTrue(response.json()["detail"].startswith("Internal server error. Reference: "))
        self.assertNotIn("/srv/missing_markers.txt", response.text)

    def test_output_over_cap_gives_400_naming_the_limit(self) -> None:
        with self._client(max_structure_input_bytes=10) as client:
            response = client.post(f"/api/vcf/plex34/structure-input?file_id={FILE_ID}")

        self.assertEqual(response.status_code, 400)
        self.assertIn("maximum allowed is 10", response.json()["detail"])

    def test_generate_then_download_and_traversal_404(self) -> None:
        with self._client() as client:
            generated = client.post(f"/api/vcf/plex34/structure-input?file_id={FILE_ID}")
            self.assertEqual(generated.status_code, 200, generated.text)
            artifact_id = generated.json()["artifact_id"]
            download = client.get(f"/api/vcf/plex34/structure-input/{artifact_id}/download")
            traversal = client.get("/api/vcf/plex34/structure-input/..%2F..%2Fetc/download")
            wrong_shape = client.get("/api/vcf/plex34/structure-input/ABCDEF/download")

        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.headers["content-type"], "application/zip")
        self.assertEqual(traversal.status_code, 404)
        self.assertEqual(wrong_shape.status_code, 404)
