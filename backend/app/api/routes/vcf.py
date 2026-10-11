import io
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Response
from fastapi.responses import StreamingResponse

from app.core import settings
from app.models import (
    ConversionRequest, ConversionResponse, FileUploadResponse, MarkersResponse, ValidationResult,
)
from app.services.csv_safety import neutralize_dataframe
from app.services.heavy_jobs import run_heavy
from app.services.vcf_processor import VCFParseError
from app.services import (
    VCFProcessor,
    MarkerService,
    UploadGzipNameMismatchError,
    UploadInvalidGzipError,
    UploadQuotaExceededError,
    UploadTooLargeError,
    VCFLimitError,
    VCFLimits,
    check_vcf_limits,
    directory_bytes,
    find_uploaded_vcf,
    save_upload_stream,
    sweep_all,
    validate_stored_upload,
)

router = APIRouter(prefix="/api/vcf", tags=["VCF Processing"])

STORAGE_FULL_DETAIL = "Upload storage is full. Try again in a few minutes."
VALIDATION_DETAIL_LIMIT = 100


def _store_upload(upload_file: UploadFile, file_path: Path) -> int:
    """Stream, size-check, gzip-check and shape-check an upload. Removes the file on any failure."""
    try:
        sweep_all(settings)
        used = directory_bytes(file_path.parent)
        if used + settings.max_upload_size > settings.max_upload_dir_bytes:
            raise UploadQuotaExceededError
        file_size = save_upload_stream(
            upload_file.file,
            file_path,
            settings.max_upload_size,
            quota_remaining=settings.max_upload_dir_bytes - used,
        )
        validate_stored_upload(file_path, settings.max_uncompressed_upload_size)
        check_vcf_limits(
            file_path,
            VCFLimits(
                max_samples=settings.max_vcf_samples,
                max_variants=settings.max_vcf_variants,
                max_cells=settings.max_vcf_cells,
            ),
        )
        return file_size
    except UploadQuotaExceededError:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=507, detail=STORAGE_FULL_DETAIL)
    except UploadTooLargeError:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=413,
            detail=(
                f"File exceeds the maximum upload size of {settings.max_upload_size} bytes "
                f"({settings.max_uncompressed_upload_size} bytes after decompression)."
            ),
        )
    except UploadGzipNameMismatchError:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail="Compressed uploads must use the .vcf.gz extension.",
        )
    except UploadInvalidGzipError:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Invalid gzip-compressed VCF file.")
    except VCFLimitError as error:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(error))
    except UnicodeDecodeError:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="VCF files must be UTF-8 text.")
    except BaseException:
        file_path.unlink(missing_ok=True)
        raise


@router.post("/upload", response_model=FileUploadResponse)
async def upload_vcf(file: UploadFile = File(...)):
    filename = file.filename or ""
    if not (filename.endswith('.vcf') or filename.endswith('.vcf.gz')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .vcf or .vcf.gz files are allowed."
        )

    file_id = str(uuid.uuid4())
    extension = '.vcf.gz' if filename.endswith('.vcf.gz') else '.vcf'
    file_path = settings.get_upload_dir() / f"{file_id}{extension}"

    file_size = await run_heavy(_store_upload, file, file_path)

    return FileUploadResponse(
        file_id=file_id,
        filename=filename,
        size=file_size,
        message="File uploaded successfully"
    )


@router.delete("/upload/{file_id}", status_code=204, response_class=Response)
async def delete_upload(file_id: str) -> Response:
    file_path = find_uploaded_vcf(file_id, settings.get_upload_dir())
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    file_path.unlink(missing_ok=True)
    return Response(status_code=204)


@router.post("/validate", response_model=ValidationResult)
async def validate_vcf(file_id: str):
    file_path = find_uploaded_vcf(file_id, settings.get_upload_dir())
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        return await run_heavy(_validate, file_id, file_path)
    except VCFParseError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


def _validate(file_id: str, file_path: Path) -> ValidationResult:
    hirisplex_markers = MarkerService.load_markers_from_file(settings.get_markers_path("hirisplex"))
    plex34_markers = MarkerService.load_markers_from_file(settings.get_markers_path("plex34"))
    required_markers = hirisplex_markers.union(plex34_markers)

    with VCFProcessor(file_path) as processor:
        summary = processor.validate(limit_details=VALIDATION_DETAIL_LIMIT)

    markers_complete, missing_markers = MarkerService.verify_markers(summary.marker_ids, required_markers)
    warnings: list[str] = []
    if summary.duplicate_markers:
        warnings.append(f"{len(summary.duplicate_markers)} duplicate marker ID occurrences were found in the VCF.")

    return ValidationResult(
        file_id=file_id,
        filename=file_path.name,
        has_ids=summary.has_ids,
        markers_complete=markers_complete,
        missing_markers=missing_markers,
        missing_genotypes_count=summary.missing_genotypes_count,
        missing_genotypes=summary.missing_genotypes,
        ref_alt_valid=summary.ref_alt_valid,
        samples=summary.samples,
        sample_count=len(summary.samples),
        duplicate_markers=summary.duplicate_markers,
        warnings=warnings,
    )


def _convert(file_path: Path, marker_type: str) -> tuple[str, str, int]:
    """Returns (csv_text, filename, row_count) for the requested marker set."""
    markers = MarkerService.load_markers_from_file(settings.get_markers_path(marker_type))
    with VCFProcessor(file_path) as processor:
        if marker_type == "hirisplex":
            df = processor.convert_to_hirisplex(markers)
            filename = "hirisplex_input.csv"
        else:
            df = processor.convert_to_plex34(markers)
            filename = "plex34_input.csv"
    return neutralize_dataframe(df).to_csv(index=False), filename, len(df)


@router.post("/convert", response_model=ConversionResponse)
async def convert_vcf(request: ConversionRequest):
    file_path = find_uploaded_vcf(request.file_id, settings.get_upload_dir())
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        csv_data, filename, row_count = await run_heavy(_convert, file_path, request.marker_type)
    except VCFParseError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return ConversionResponse(
        file_id=request.file_id,
        marker_type=request.marker_type,
        csv_data=csv_data,
        filename=filename,
        row_count=row_count,
        message="Conversion successful"
    )


@router.get("/download/{file_id}/{marker_type}")
async def download_converted(file_id: str, marker_type: str):
    if marker_type not in ["hirisplex", "plex34"]:
        raise HTTPException(status_code=400, detail="Invalid marker type")

    file_path = find_uploaded_vcf(file_id, settings.get_upload_dir())
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        csv_data, filename, _ = await run_heavy(_convert, file_path, marker_type)
    except VCFParseError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/markers/{marker_type}", response_model=MarkersResponse)
async def get_markers(marker_type: str):
    if marker_type not in ["hirisplex", "plex34"]:
        raise HTTPException(status_code=400, detail="Invalid marker type")

    markers = MarkerService.load_markers_from_file(settings.get_markers_path(marker_type))
    return MarkersResponse(
        marker_type=marker_type,
        markers=sorted(list(markers)),
        count=len(markers)
    )


def _full_csv(file_path: Path) -> str:
    with VCFProcessor(file_path) as processor:
        df = processor.get_full_vcf_dataframe()
    return neutralize_dataframe(df).to_csv(index=False)


@router.get("/download-full/{file_id}")
async def download_full_vcf_csv(file_id: str):
    """Download full VCF as CSV (all rows, not just converted)"""
    file_path = find_uploaded_vcf(file_id, settings.get_upload_dir())
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        csv_data = await run_heavy(_full_csv, file_path)
    except VCFParseError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=converted_vcf.csv"}
    )
