from unittest import TestCase
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services import HirisPlexSResultsParseError, HirisPlexSResultsParser, Plex34StructureOutputParser
from app.services.structure_output_parser import Plex34StructureOutputParseError

RESULT_COLUMNS = (
    "SampleID,PBlueEye,PIntermediateEye,PBrownEye,PBlondHair,PBrownHair,PRedHair,PBlackHair,PLightHair,PDarkHair"
)
RESULT_ROW = "s{index},0.9,0.05,0.05,0.1,0.6,0.1,0.2,0.3,0.7"


def results_csv(rows: int) -> str:
    return RESULT_COLUMNS + "\n" + "\n".join(RESULT_ROW.format(index=i) for i in range(rows)) + "\n"


def structure_output(lines: int, clusters: int) -> str:
    probabilities = " ".join(["0.5"] * clusters)
    body = "\n".join(f"{i + 1} sample_{i} (0) : {probabilities}" for i in range(lines))
    return f"Header\nInferred ancestry of individuals:\n{body}\nEstimated Allele Frequencies in each cluster\n"


class HirisPlexSResultsLimitsTest(TestCase):
    def test_row_cap_is_enforced_before_row_n_plus_one(self) -> None:
        with self.assertRaisesRegex(HirisPlexSResultsParseError, "maximum allowed is 10000"):
            HirisPlexSResultsParser.parse_text(results_csv(10_001), max_rows=10_000)

    def test_rows_at_the_cap_parse(self) -> None:
        parsed = HirisPlexSResultsParser.parse_text(results_csv(10_000), max_rows=10_000)
        self.assertEqual(parsed.count, 10_000)


class StructureOutputLimitsTest(TestCase):
    def test_too_many_clusters(self) -> None:
        with self.assertRaisesRegex(Plex34StructureOutputParseError, "maximum allowed is 64"):
            Plex34StructureOutputParser.parse_text(structure_output(1, 65), max_lines=10_000, max_clusters=64)

    def test_too_many_lines(self) -> None:
        with self.assertRaisesRegex(Plex34StructureOutputParseError, "maximum allowed is 10000"):
            Plex34StructureOutputParser.parse_text(structure_output(10_001, 2), max_lines=10_000, max_clusters=64)

    def test_typical_output_passes(self) -> None:
        parsed = Plex34StructureOutputParser.parse_text(structure_output(20, 4), max_lines=10_000, max_clusters=64)
        self.assertEqual(len(parsed.sample_lines), 20)
        self.assertEqual(len(parsed.ancestry_rows[0].probabilities), 4)


class ResultsRoutesTest(TestCase):
    def _client(self, **overrides) -> TestClient:
        settings = Settings(_env_file=None, **overrides)
        for target in ("app.api.routes.hirisplex_results.settings", "app.api.routes.plex34_structure.settings"):
            patcher = patch(target, settings)
            patcher.start()
            self.addCleanup(patcher.stop)
        return TestClient(create_app(settings), raise_server_exceptions=False)

    def test_results_upload_over_size_cap_is_413(self) -> None:
        with self._client(max_results_upload_bytes=1024) as client:
            response = client.post(
                "/api/results/hirisplex-s",
                files={"file": ("r.csv", results_csv(200).encode(), "text/csv")},
            )
        self.assertEqual(response.status_code, 413)
        self.assertIn("1024", response.json()["detail"])

    def test_oversized_csv_field_is_400_not_500(self) -> None:
        huge_field = RESULT_COLUMNS + "\n" + '"' + "x" * 200_000 + '",0.9,0.05,0.05,0.1,0.6,0.1,0.2,0.3,0.7\n'
        with self._client() as client:
            response = client.post(
                "/api/results/hirisplex-s",
                files={"file": ("r.csv", huge_field.encode(), "text/csv")},
            )
        self.assertEqual(response.status_code, 400)
        self.assertIn("could not be parsed", response.json()["detail"])

    def test_results_row_cap_via_route(self) -> None:
        with self._client(max_results_rows=5) as client:
            over = client.post("/api/results/hirisplex-s", files={"file": ("r.csv", results_csv(6).encode(), "text/csv")})
            at = client.post("/api/results/hirisplex-s", files={"file": ("r.csv", results_csv(5).encode(), "text/csv")})
        self.assertEqual(over.status_code, 400)
        self.assertEqual(at.status_code, 200)
        self.assertEqual(at.json()["count"], 5)

    def test_structure_output_caps_via_route(self) -> None:
        with self._client(max_structure_clusters=3, max_structure_output_lines=2) as client:
            clusters = client.post(
                "/api/vcf/plex34/structure-output",
                files={"file": ("s.out", structure_output(1, 4).encode(), "text/plain")},
            )
            lines = client.post(
                "/api/vcf/plex34/structure-output",
                files={"file": ("s.out", structure_output(3, 2).encode(), "text/plain")},
            )
            ok = client.post(
                "/api/vcf/plex34/structure-output",
                files={"file": ("s.out", structure_output(2, 3).encode(), "text/plain")},
            )
        self.assertEqual(clusters.status_code, 400)
        self.assertIn("maximum allowed is 3", clusters.json()["detail"])
        self.assertEqual(lines.status_code, 400)
        self.assertIn("maximum allowed is 2", lines.json()["detail"])
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()["count"], 2)
