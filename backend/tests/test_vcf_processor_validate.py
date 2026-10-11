import tempfile
from pathlib import Path
from unittest import TestCase

from app.services.vcf_duplicate_warnings import VCFDuplicateWarningService
from app.services.vcf_processor import VCFParseError, VCFProcessor

HEADER = (
    "##fileformat=VCFv4.2\n"
    '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n'
    "##contig=<ID=1>\n"
    "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS1\tS2\n"
)
ROWS = (
    "1\t10\trs1\tA\tG\t.\tPASS\t.\tGT\t0/1\t1/1\n"
    "1\t20\trs2\tC\tT\t.\tPASS\t.\tGT\t0/0\t./.\n"
    "1\t30\trs2\tG\tA\t.\tPASS\t.\tGT\t./.\t0/1\n"
    "1\t40\t.\tT\tC\t.\tPASS\t.\tGT\t0/0\t0/0\n"
)


class VCFProcessorValidateTest(TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "fixture.vcf"
        self.path.write_text(HEADER + ROWS, encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_single_pass_matches_legacy_multi_call_results(self) -> None:
        # Given: the same fixture read by the old per-check methods.
        with VCFProcessor(self.path) as legacy:
            expected = {
                "has_ids": legacy.verify_has_ids(),
                "samples": legacy.get_samples(),
                "marker_ids": legacy.get_marker_ids(),
                "missing": legacy.verify_missing_genotypes(),
                "ref_alt_valid": legacy.verify_ref_alt(),
            }
        duplicates = VCFDuplicateWarningService.verify_duplicate_ids(self.path).duplicate_markers

        # When: the single-pass validation runs.
        with VCFProcessor(self.path) as processor:
            summary = processor.validate()

        # Then: every field matches the legacy path.
        self.assertEqual(summary.has_ids, expected["has_ids"])
        self.assertEqual(summary.samples, expected["samples"])
        self.assertEqual(summary.marker_ids, expected["marker_ids"])
        self.assertEqual(summary.missing_genotypes_count, expected["missing"][0])
        self.assertEqual(summary.missing_genotypes, expected["missing"][1])
        self.assertEqual(summary.ref_alt_valid, expected["ref_alt_valid"])
        self.assertEqual(summary.duplicate_markers, duplicates)
        self.assertEqual(summary.duplicate_markers, ["rs2"])
        self.assertEqual(summary.missing_genotypes_count, 2)

    def test_detail_is_capped_while_count_keeps_running(self) -> None:
        # Given: 500 variants, each with one missing genotype.
        rows = "".join(f"1\t{i + 1}\trs{i}\tA\tG\t.\tPASS\t.\tGT\t./.\t0/1\n" for i in range(500))
        self.path.write_text(HEADER + rows, encoding="utf-8")

        with VCFProcessor(self.path) as processor:
            summary = processor.validate(limit_details=100)

        self.assertEqual(summary.missing_genotypes_count, 500)
        self.assertEqual(len(summary.missing_genotypes), 100)

    def test_invalid_ref_alt_is_detected(self) -> None:
        self.path.write_text(HEADER + "1\t10\trs1\tN\tG\t.\tPASS\t.\tGT\t0/1\t1/1\n", encoding="utf-8")
        with VCFProcessor(self.path) as processor:
            self.assertFalse(processor.validate().ref_alt_valid)

    def test_unparseable_file_raises_vcf_parse_error(self) -> None:
        self.path.write_text("this is not a vcf\n", encoding="utf-8")
        with self.assertRaises(VCFParseError):
            with VCFProcessor(self.path):
                pass
