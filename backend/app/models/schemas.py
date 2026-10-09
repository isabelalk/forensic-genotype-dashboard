from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Literal


class FileUploadResponse(BaseModel):
    """Response after file upload"""
    file_id: str
    filename: str
    size: int
    message: str


class ValidationResult(BaseModel):
    """VCF validation results"""
    file_id: str
    filename: str
    has_ids: bool
    markers_complete: bool
    missing_markers: List[str]
    missing_genotypes_count: int
    missing_genotypes: List[dict]  # [{row, sample}]
    ref_alt_valid: bool
    samples: List[str]
    sample_count: int
    duplicate_markers: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class ConversionRequest(BaseModel):
    """Request to convert VCF to specific format"""
    file_id: str
    marker_type: Literal["hirisplex", "plex34"] = Field(
        ..., 
        description="Type of marker panel to use"
    )


class ConversionResponse(BaseModel):
    """Response after conversion"""
    file_id: str
    marker_type: str
    csv_data: str
    filename: str
    row_count: int
    message: str


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None


class MarkersResponse(BaseModel):
    """Marker list response"""
    marker_type: str
    markers: List[str]
    count: int


class Plex34StructureResponse(BaseModel):
    artifact_id: str
    filenames: List[str]
    num_samples: int
    num_markers: int
    missing_markers: List[str]
    warnings: List[str]
    message: str


class HirisPlexSProbabilities(BaseModel):
    model_config = ConfigDict(frozen=True)

    PBlueEye: float
    PIntermediateEye: float
    PBrownEye: float
    PBlondHair: float
    PBrownHair: float
    PRedHair: float
    PBlackHair: float
    PLightHair: float
    PDarkHair: float
    PVeryPaleSkin: float | None = None
    PPaleSkin: float | None = None
    PIntermediateSkin: float | None = None
    PDarkSkin: float | None = None
    PDarktoBlackSkin: float | None = None


class HirisPlexSTopPredictions(BaseModel):
    model_config = ConfigDict(frozen=True)

    eye_color: str
    eye_probability: float
    hair_color: str
    hair_probability: float
    hair_shade: str
    hair_shade_probability: float
    skin: str
    skin_probability: float | None


class HirisPlexSResultRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    row_index: int
    sample_id: str | None = None
    probabilities: HirisPlexSProbabilities
    top_predictions: HirisPlexSTopPredictions


class HirisPlexSResultsResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    rows: List[HirisPlexSResultRow]
    count: int
    message: str


class Plex34ClusterProbability(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: str
    probability: float


class Plex34AncestryRow(BaseModel):
    model_config = ConfigDict(frozen=True)

    row_index: int
    sample_id: str
    probabilities: List[Plex34ClusterProbability]
    top_cluster: str
    confidence: float


class Plex34StructureOutputResponse(BaseModel):
    sample_lines: List[str]
    ancestry_rows: List[Plex34AncestryRow]
    count: int
    message: str
