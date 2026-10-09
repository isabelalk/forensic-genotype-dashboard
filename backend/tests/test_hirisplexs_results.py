from pathlib import Path
from io import BytesIO
from unittest import TestCase

import anyio
from starlette.datastructures import UploadFile

from app.main import app
from app.api.routes.hirisplex_results import parse_hirisplex_s_results
from app.services import HirisPlexSResultsParser


SAMPLE_RESULTS = Path(__file__).resolve().parents[1] / "app" / "data" / "results_hirisplexs.csv"


class HirisPlexSResultsParserTest(TestCase):
    def test_parse_results_returns_top_predictions_when_csv_has_required_probabilities(self) -> None:
        # Given: the bundled HIrisPlex-S result CSV with eye, hair, and shade probabilities.
        csv_text = SAMPLE_RESULTS.read_text(encoding="utf-8")

        # When: the backend parser reads the uploaded result text.
        parsed = HirisPlexSResultsParser.parse_text(csv_text)

        # Then: one typed row is returned with top predictions and skin marked unavailable.
        self.assertEqual(parsed.count, 1)
        row = parsed.rows[0]
        self.assertEqual(row.row_index, 1)
        self.assertEqual(row.probabilities.PBlueEye, 0.967887786492122)
        self.assertEqual(row.probabilities.PRedHair, 0.999999969065613)
        self.assertEqual(row.probabilities.PLightHair, 0.988632271402713)
        self.assertEqual(row.top_predictions.eye_color, "Blue")
        self.assertEqual(row.top_predictions.eye_probability, 0.967887786492122)
        self.assertEqual(row.top_predictions.hair_color, "Red")
        self.assertEqual(row.top_predictions.hair_probability, 0.999999969065613)
        self.assertEqual(row.top_predictions.hair_shade, "Light")
        self.assertEqual(row.top_predictions.hair_shade_probability, 0.988632271402713)
        self.assertEqual(row.top_predictions.skin, "unavailable")
        self.assertIsNone(row.top_predictions.skin_probability)

    def test_parse_results_returns_top_skin_prediction_when_csv_has_skin_probabilities(self) -> None:
        # Given: HIrisPlex-S results with the complete optional skin probability column set.
        csv_text = (
            "SampleID,PBlueEye,PIntermediateEye,PBrownEye,PBlondHair,PBrownHair,PRedHair,PBlackHair,PLightHair,"
            "PDarkHair,PVeryPaleSkin,PPaleSkin,PIntermediateSkin,PDarkSkin,PDarktoBlackSkin\n"
            "sample-1,0.1,0.8,0.1,0.2,0.3,0.1,0.4,0.6,0.4,0.05,0.12,0.73,0.08,0.02\n"
        )

        # When: the backend parser reads the uploaded result text.
        parsed = HirisPlexSResultsParser.parse_text(csv_text)

        # Then: the row includes the real top skin prediction and probability.
        row = parsed.rows[0]
        self.assertEqual(row.top_predictions.skin, "Intermediate")
        self.assertEqual(row.top_predictions.skin_probability, 0.73)
        self.assertEqual(row.probabilities.PIntermediateSkin, 0.73)

    def test_parse_results_keeps_missing_sample_id_as_none_when_csv_has_no_id_column(self) -> None:
        # Given: the bundled example has no sample identifier column.
        csv_text = SAMPLE_RESULTS.read_text(encoding="utf-8")

        # When: the backend parser reads the uploaded result text.
        parsed = HirisPlexSResultsParser.parse_text(csv_text)

        # Then: the row remains identifiable by row index only.
        self.assertIsNone(parsed.rows[0].sample_id)

    def test_parse_results_raises_when_required_probability_column_is_missing(self) -> None:
        # Given: a CSV without the required dark hair shade probability.
        csv_text = "PBlueEye,PIntermediateEye,PBrownEye,PBlondHair,PBrownHair,PRedHair,PBlackHair,PLightHair\n0.1,0.2,0.7,0.1,0.2,0.3,0.4,0.5\n"

        # When/Then: parsing fails at the trust boundary with a typed parser error.
        with self.assertRaisesRegex(Exception, "PDarkHair"):
            HirisPlexSResultsParser.parse_text(csv_text)

    def test_parse_results_raises_when_probability_is_not_numeric(self) -> None:
        # Given: a CSV with an invalid probability token in one required column.
        csv_text = SAMPLE_RESULTS.read_text(encoding="utf-8").replace("0.967887786492122", "not-a-number", 1)

        # When/Then: parsing reports the invalid column and row.
        with self.assertRaisesRegex(Exception, "PBlueEye"):
            HirisPlexSResultsParser.parse_text(csv_text)

    def test_parse_results_raises_when_required_probability_is_nan(self) -> None:
        # Given: a CSV with a non-finite value in one required probability column.
        csv_text = SAMPLE_RESULTS.read_text(encoding="utf-8").replace("0.967887786492122", "nan", 1)

        # When/Then: parsing rejects the non-finite probability at the trust boundary.
        with self.assertRaisesRegex(Exception, "PBlueEye"):
            HirisPlexSResultsParser.parse_text(csv_text)

    def test_parse_results_raises_when_skin_probability_column_set_is_partial(self) -> None:
        # Given: HIrisPlex-S results with one skin probability column but not the complete set.
        csv_text = (
            "PBlueEye,PIntermediateEye,PBrownEye,PBlondHair,PBrownHair,PRedHair,PBlackHair,PLightHair,"
            "PDarkHair,PVeryPaleSkin\n"
            "0.1,0.8,0.1,0.2,0.3,0.1,0.4,0.6,0.4,0.05\n"
        )

        # When/Then: parsing rejects the incomplete optional skin probability set.
        with self.assertRaisesRegex(Exception, "PPaleSkin"):
            HirisPlexSResultsParser.parse_text(csv_text)

    def test_parse_results_raises_when_skin_probability_is_out_of_range(self) -> None:
        # Given: HIrisPlex-S results with a complete skin probability set and one invalid value.
        csv_text = (
            "PBlueEye,PIntermediateEye,PBrownEye,PBlondHair,PBrownHair,PRedHair,PBlackHair,PLightHair,"
            "PDarkHair,PVeryPaleSkin,PPaleSkin,PIntermediateSkin,PDarkSkin,PDarktoBlackSkin\n"
            "0.1,0.8,0.1,0.2,0.3,0.1,0.4,0.6,0.4,0.05,0.12,1.2,0.08,0.02\n"
        )

        # When/Then: parsing applies the same probability range rule to skin columns.
        with self.assertRaisesRegex(Exception, "PIntermediateSkin"):
            HirisPlexSResultsParser.parse_text(csv_text)

    def test_parse_results_raises_when_skin_probability_cell_is_missing(self) -> None:
        # Given: complete skin headers but a result row that omits the last skin probability cell.
        csv_text = (
            "PBlueEye,PIntermediateEye,PBrownEye,PBlondHair,PBrownHair,PRedHair,PBlackHair,PLightHair,"
            "PDarkHair,PVeryPaleSkin,PPaleSkin,PIntermediateSkin,PDarkSkin,PDarktoBlackSkin\n"
            "0.1,0.8,0.1,0.2,0.3,0.1,0.4,0.6,0.4,0.05,0.12,0.73,0.08\n"
        )

        # When/Then: parsing rejects the malformed row instead of treating skin as unavailable.
        with self.assertRaisesRegex(Exception, "PDarktoBlackSkin"):
            HirisPlexSResultsParser.parse_text(csv_text)

    def test_parse_results_raises_when_skin_probability_is_nan(self) -> None:
        # Given: complete skin headers but a non-finite skin probability value.
        csv_text = (
            "PBlueEye,PIntermediateEye,PBrownEye,PBlondHair,PBrownHair,PRedHair,PBlackHair,PLightHair,"
            "PDarkHair,PVeryPaleSkin,PPaleSkin,PIntermediateSkin,PDarkSkin,PDarktoBlackSkin\n"
            "0.1,0.8,0.1,0.2,0.3,0.1,0.4,0.6,0.4,0.05,0.12,nan,0.08,0.02\n"
        )

        # When/Then: parsing applies finite-number validation to skin columns.
        with self.assertRaisesRegex(Exception, "PIntermediateSkin"):
            HirisPlexSResultsParser.parse_text(csv_text)

    def test_upload_results_endpoint_returns_parsed_rows_when_csv_file_uploaded(self) -> None:
        # Given: the endpoint function and bundled HIrisPlex-S result CSV uploaded as multipart data.
        csv_text = SAMPLE_RESULTS.read_text(encoding="utf-8")
        upload = UploadFile(file=BytesIO(csv_text.encode("utf-8")), filename="results_hirisplexs.csv")

        # When: the results upload endpoint receives the CSV file.
        payload = anyio.run(parse_hirisplex_s_results, upload)

        # Then: the endpoint returns typed rows and top predictions without running HIrisPlex-S.
        self.assertEqual(payload.count, 1)
        self.assertEqual(payload.rows[0].top_predictions.eye_color, "Blue")
        self.assertEqual(payload.rows[0].top_predictions.hair_color, "Red")
        self.assertEqual(payload.rows[0].top_predictions.hair_shade, "Light")
        self.assertEqual(payload.rows[0].top_predictions.skin, "unavailable")
        paths = {route.path for route in app.routes}
        self.assertIn("/api/results/hirisplex-s", paths)
