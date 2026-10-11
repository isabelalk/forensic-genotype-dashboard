import gzip
from pathlib import Path
from typing import BinaryIO, Callable

UPLOAD_CHUNK_SIZE = 1024 * 1024
GZIP_SIGNATURE = b"\x1f\x8b"
GZIP_EXTENSION = ".vcf.gz"


class UploadTooLargeError(Exception):
    pass


class UploadInvalidGzipError(Exception):
    pass


class UploadGzipNameMismatchError(Exception):
    """Gzip content was uploaded under a filename that does not end in .vcf.gz."""


class UploadQuotaExceededError(Exception):
    """Storing the upload would push the upload directory over its byte quota."""


def save_upload_stream(
    upload_stream: BinaryIO,
    destination: Path,
    max_size_bytes: int,
    quota_remaining: int | None = None,
) -> int:
    """Stream an upload to disk.

    Raises UploadTooLargeError past `max_size_bytes` and UploadQuotaExceededError
    once more than `quota_remaining` bytes have been written (when given).
    """
    file_size = 0
    with destination.open("wb") as output_file:
        while chunk := upload_stream.read(UPLOAD_CHUNK_SIZE):
            file_size += len(chunk)
            if file_size > max_size_bytes:
                raise UploadTooLargeError
            if quota_remaining is not None and file_size > quota_remaining:
                raise UploadQuotaExceededError
            output_file.write(chunk)
    return file_size


def is_gzip_file(path: Path) -> bool:
    with path.open("rb") as handle:
        return handle.read(2) == GZIP_SIGNATURE


def validate_stored_upload(upload_path: Path, max_uncompressed_size: int) -> None:
    """Check gzip uploads by content signature rather than filename.

    - gzip signature + name ending in .vcf.gz: walk the stream, enforcing the decompressed cap
    - gzip signature + any other name: UploadGzipNameMismatchError
    - no signature + name ending in .gz: UploadInvalidGzipError
    - no signature + other name: plain text, nothing to check here
    """
    gzipped = is_gzip_file(upload_path)
    named_gzip = upload_path.name.endswith(".gz")

    if gzipped and not upload_path.name.endswith(GZIP_EXTENSION):
        raise UploadGzipNameMismatchError
    if not gzipped:
        if named_gzip:
            raise UploadInvalidGzipError
        return

    decompressed_size = 0
    try:
        with gzip.open(upload_path, "rb") as gzip_file:
            while chunk := gzip_file.read(UPLOAD_CHUNK_SIZE):
                decompressed_size += len(chunk)
                if decompressed_size > max_uncompressed_size:
                    raise UploadTooLargeError
    except (EOFError, OSError) as error:
        raise UploadInvalidGzipError from error
