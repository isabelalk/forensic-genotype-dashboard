import gzip
import tempfile
from pathlib import Path
from unittest import TestCase

from app.services.vcf_limits import VCFLimitError, VCFLimits, check_vcf_limits

LIMITS = VCFLimits(max_samples=5000, max_variants=10000, max_cells=2_000_000)
FIXED = "1\t{pos}\trs{pos}\tA\tG\t.\tPASS\t.\tGT"


def build_vcf(sample_names: list[str], variants: int) -> str:
    header = "##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT"
    if sample_names:
        header += "\t" + "\t".join(sample_names)
    genotypes = "\t".join("0/1" for _ in sample_names)
    rows = [FIXED.format(pos=index + 1) + ("\t" + genotypes if genotypes else "") for index in range(variants)]
    return header + "\n" + "\n".join(rows) + "\n"


class VCFLimitsTest(TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _vcf(self, text: str, name: str = "a.vcf") -> Path:
        path = self.dir / name
        if name.endswith(".gz"):
            path.write_bytes(gzip.compress(text.encode("utf-8")))
        else:
            path.write_text(text, encoding="utf-8")
        return path

    def test_too_many_samples(self) -> None:
        path = self._vcf(build_vcf([f"S{i}" for i in range(5001)], 1))
        with self.assertRaisesRegex(VCFLimitError, "5000"):
            check_vcf_limits(path, LIMITS)

    def test_too_many_variants(self) -> None:
        path = self._vcf(build_vcf(["S1"], 10001))
        with self.assertRaisesRegex(VCFLimitError, "10000"):
            check_vcf_limits(path, LIMITS)

    def test_too_many_cells(self) -> None:
        path = self._vcf(build_vcf([f"S{i}" for i in range(1000)], 3000))
        with self.assertRaisesRegex(VCFLimitError, "2000000"):
            check_vcf_limits(path, LIMITS)

    def test_duplicate_sample_names(self) -> None:
        path = self._vcf(build_vcf(["S1", "S1"], 1))
        with self.assertRaisesRegex(VCFLimitError, "'S1' more than once"):
            check_vcf_limits(path, LIMITS)

    def test_sample_name_with_whitespace(self) -> None:
        path = self._vcf(build_vcf(["Sample 1"], 1))
        with self.assertRaisesRegex(VCFLimitError, "whitespace"):
            check_vcf_limits(path, LIMITS)

    def test_empty_sample_name(self) -> None:
        path = self._vcf(build_vcf(["S1", ""], 1))
        with self.assertRaisesRegex(VCFLimitError, "empty sample name"):
            check_vcf_limits(path, LIMITS)

    def test_missing_header(self) -> None:
        path = self._vcf("##fileformat=VCFv4.2\n1\t1\trs1\tA\tG\t.\tPASS\t.\tGT\t0/1\n")
        with self.assertRaisesRegex(VCFLimitError, "#CHROM"):
            check_vcf_limits(path, LIMITS)

    def test_realistic_casework_file_passes(self) -> None:
        path = self._vcf(build_vcf([f"S{i}" for i in range(10)], 71))
        shape = check_vcf_limits(path, LIMITS)
        self.assertEqual((shape.sample_count, shape.variant_count), (10, 71))

    def test_gzip_input_is_scanned(self) -> None:
        path = self._vcf(build_vcf(["S1", "S1"], 1), name="a.vcf.gz")
        with self.assertRaises(VCFLimitError):
            check_vcf_limits(path, LIMITS)
