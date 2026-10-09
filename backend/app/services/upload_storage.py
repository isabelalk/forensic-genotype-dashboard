import gzip
from pathlib import Path
from typing import BinaryIO


UPLOAD_CHUNK_SIZE = 1024 * 1024


class UploadTooLargeError(Exception):
    pass


class UploadInvalidGzipError(Exception):
    pass


def save_upload_stream(upload_stream: BinaryIO, destination: Path, max_size_bytes: int) -> int:
    file_size = 0
    with destination.open("wb") as output_file:
        while chunk := upload_stream.read(UPLOAD_CHUNK_SIZE):
            file_size += len(chunk)
            if file_size > max_size_bytes:
                raise UploadTooLargeError
            output_file.write(chunk)
    return file_size


def validate_stored_upload(upload_path: Path, max_uncompressed_size: int) -> None:
    if not upload_path.name.endswith(".gz"):
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
