import re
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core import settings
from app.models import Plex34StructureOutputResponse, Plex34StructureResponse
from app.services import (
    Plex34StructureError,
    Plex34StructureOutputParseError,
    Plex34StructureOutputParser,
    Plex34StructureService,
    StructureArtifactRequest,
    StructureTemplatePaths,
    find_uploaded_vcf,
)

router = APIRouter(prefix="/api/vcf/plex34", tags=["VCF Processing"])
STRUCTURE_OUTPUT_MAX_BYTES = 5 * 1024 * 1024
UPLOAD_READ_CHUNK_SIZE = 1024 * 1024


def _plex34_template_paths() -> StructureTemplatePaths:
    return StructureTemplatePaths(
        population_csv=settings.get_plex34_structure_population_path(),
        mainparams=settings.get_plex34_structure_mainparams_path(),
        extraparams=settings.get_plex34_structure_extraparams_path(),
    )


def _artifact_zip_path(artifact_id: str) -> Path | None:
    if not re.fullmatch(r"[0-9a-f]{32}", artifact_id):
        return None
    return settings.get_artifact_dir() / artifact_id / f"plex34_structure_{artifact_id}.zip"


@router.post("/structure-input", response_model=Plex34StructureResponse)
async def generate_plex34_structure_input(file_id: str):
    file_path = find_uploaded_vcf(file_id, settings.get_upload_dir())
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        artifact = Plex34StructureService.generate_artifact(
            StructureArtifactRequest(
                vcf_path=file_path,
                marker_path=settings.get_markers_path("plex34"),
                template_paths=_plex34_template_paths(),
                artifact_root=settings.get_artifact_dir(),
                max_artifact_age_seconds=settings.max_artifact_age_seconds,
                max_artifact_count=settings.max_artifact_count,
            )
        )
    except Plex34StructureError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except OSError as error:
        raise HTTPException(status_code=500, detail=f"STRUCTURE artifact generation failed: {str(error)}") from error

    return Plex34StructureResponse(
        artifact_id=artifact.artifact_id,
        filenames=artifact.filenames,
        num_samples=artifact.num_samples,
        num_markers=artifact.num_markers,
        missing_markers=artifact.missing_markers,
        warnings=artifact.warnings,
        message="Plex34 STRUCTURE artifact generated successfully",
    )


@router.get("/structure-input/{artifact_id}/download")
async def download_plex34_structure_input(artifact_id: str):
    zip_path = _artifact_zip_path(artifact_id)
    if not zip_path or not zip_path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=zip_path.name,
    )


@router.post("/structure-output", response_model=Plex34StructureOutputResponse)
async def parse_plex34_structure_output(file: UploadFile = File(...)):
    try:
        output_text = (await _read_structure_output(file)).decode("utf-8")
    except UnicodeDecodeError as error:
        raise HTTPException(status_code=400, detail="Uploaded STRUCTURE output must be UTF-8 text.") from error
    except Plex34StructureOutputParseError as error:
        raise HTTPException(status_code=413, detail=str(error)) from error

    try:
        parsed_output = Plex34StructureOutputParser.parse_text(output_text)
    except Plex34StructureOutputParseError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return Plex34StructureOutputResponse(
        sample_lines=parsed_output.sample_lines,
        ancestry_rows=parsed_output.ancestry_rows,
        count=len(parsed_output.sample_lines),
        message="Plex34 STRUCTURE output parsed successfully",
    )


async def _read_structure_output(file: UploadFile) -> bytes:
    output = bytearray()
    while chunk := await file.read(UPLOAD_READ_CHUNK_SIZE):
        output.extend(chunk)
        if len(output) > STRUCTURE_OUTPUT_MAX_BYTES:
            raise Plex34StructureOutputParseError(
                f"Uploaded STRUCTURE output exceeds {STRUCTURE_OUTPUT_MAX_BYTES} bytes."
            )
    return bytes(output)
