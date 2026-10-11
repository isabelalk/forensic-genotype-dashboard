import gzip
import tempfile
from io import BytesIO
from pathlib import Path
from unittest import TestCase

from app.services.upload_storage import (
    UploadGzipNameMismatchError,
    UploadInvalidGzipError,
    UploadQuotaExceededError,
    UploadTooLargeError,
    is_gzip_file,
    save_upload_stream,
    validate_stored_upload,
)

VCF_TEXT = b"##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS1\n1\t10\trs1\tA\tG\t.\tPASS\t.\tGT\t0/1\n"


class UploadStorageTest(TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write(self, name: str, content: bytes) -> Path:
        path = self.dir / name
        path.write_bytes(content)
        return path

    def test_gzip_named_vcf_is_a_name_mismatch(self) -> None:
        path = self._write("x.vcf", gzip.compress(VCF_TEXT))
        self.assertTrue(is_gzip_file(path))
        with self.assertRaises(UploadGzipNameMismatchError):
            validate_stored_upload(path, max_uncompressed_size=1024 * 1024)

    def test_plain_text_named_vcf_gz_is_invalid_gzip(self) -> None:
        path = self._write("x.vcf.gz", VCF_TEXT)
        with self.assertRaises(UploadInvalidGzipError):
            validate_stored_upload(path, max_uncompressed_size=1024 * 1024)

    def test_gzip_over_decompressed_limit_is_too_large(self) -> None:
        path = self._write("x.vcf.gz", gzip.compress(b"A" * 4096))
        with self.assertRaises(UploadTooLargeError):
            validate_stored_upload(path, max_uncompressed_size=32)

    def test_valid_pairs_pass(self) -> None:
        plain = self._write("ok.vcf", VCF_TEXT)
        packed = self._write("ok.vcf.gz", gzip.compress(VCF_TEXT))
        validate_stored_upload(plain, max_uncompressed_size=1024)
        validate_stored_upload(packed, max_uncompressed_size=1024)

    def test_truncated_gzip_is_invalid(self) -> None:
        path = self._write("cut.vcf.gz", gzip.compress(VCF_TEXT)[:-8])
        with self.assertRaises(UploadInvalidGzipError):
            validate_stored_upload(path, max_uncompressed_size=1024 * 1024)

    def test_save_stream_enforces_file_limit(self) -> None:
        with self.assertRaises(UploadTooLargeError):
            save_upload_stream(BytesIO(b"x" * 100), self.dir / "big.vcf", max_size_bytes=99)

    def test_save_stream_enforces_quota_remaining(self) -> None:
        with self.assertRaises(UploadQuotaExceededError):
            save_upload_stream(BytesIO(b"x" * 100), self.dir / "q.vcf", max_size_bytes=1000, quota_remaining=50)

    def test_save_stream_returns_size(self) -> None:
        size = save_upload_stream(BytesIO(VCF_TEXT), self.dir / "s.vcf", max_size_bytes=1000)
        self.assertEqual(size, len(VCF_TEXT))
        self.assertEqual((self.dir / "s.vcf").read_bytes(), VCF_TEXT)
