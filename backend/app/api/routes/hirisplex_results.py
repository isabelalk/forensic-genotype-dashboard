import csv

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core import settings
from app.models import HirisPlexSResultsResponse
from app.services import HirisPlexSResultsParseError, HirisPlexSResultsParser


router = APIRouter(prefix="/api/results", tags=["Results"])
UPLOAD_READ_CHUNK_SIZE = 1024 * 1024


@router.post("/hirisplex-s", response_model=HirisPlexSResultsResponse)
async def parse_hirisplex_s_results(file: UploadFile = File(...)) -> HirisPlexSResultsResponse:
    raw = await _read_capped(file, settings.max_results_upload_bytes)
    try:
        csv_text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise HTTPException(status_code=400, detail="Uploaded HIrisPlex-S results must be UTF-8 CSV text.") from error

    try:
        return HirisPlexSResultsParser.parse_text(csv_text, max_rows=settings.max_results_rows)
    except HirisPlexSResultsParseError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except csv.Error as error:
        raise HTTPException(status_code=400, detail="HIrisPlex-S results CSV could not be parsed.") from error


async def _read_capped(file: UploadFile, limit: int) -> bytes:
    output = bytearray()
    while chunk := await file.read(UPLOAD_READ_CHUNK_SIZE):
        output.extend(chunk)
        if len(output) > limit:
            raise HTTPException(
                status_code=413,
                detail=f"Uploaded HIrisPlex-S results exceed {limit} bytes.",
            )
    return bytes(output)
