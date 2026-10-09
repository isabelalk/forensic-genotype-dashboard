from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models import HirisPlexSResultsResponse
from app.services import HirisPlexSResultsParseError, HirisPlexSResultsParser


router = APIRouter(prefix="/api/results", tags=["Results"])


@router.post("/hirisplex-s", response_model=HirisPlexSResultsResponse)
async def parse_hirisplex_s_results(file: UploadFile = File(...)) -> HirisPlexSResultsResponse:
    try:
        csv_text = (await file.read()).decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise HTTPException(status_code=400, detail="Uploaded HIrisPlex-S results must be UTF-8 CSV text.") from error

    try:
        return HirisPlexSResultsParser.parse_text(csv_text)
    except HirisPlexSResultsParseError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
