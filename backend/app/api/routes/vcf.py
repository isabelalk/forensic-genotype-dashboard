import io
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse

from app.core import settings
from app.models import (
    ConversionRequest, ConversionResponse, FileUploadResponse, MarkersResponse, ValidationResult,
)
from app.services import (
    VCFProcessor,
    MarkerService,
    UploadInvalidGzipError,
    UploadTooLargeError,
    VCFDuplicateWarningService,
    find_uploaded_vcf,
    save_upload_stream,
    validate_stored_upload,
)

router = APIRouter(prefix="/api/vcf", tags=["VCF Processing"])


@router.post("/upload", response_model=FileUploadResponse)
async def upload_vcf(file: UploadFile = File(...)):
    # Validate file extension
    if not (file.filename.endswith('.vcf') or file.filename.endswith('.vcf.gz')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .vcf or .vcf.gz files are allowed."
        )
    
    # Generate unique file ID
    file_id = str(uuid.uuid4())
    
    extension = '.vcf.gz' if file.filename.endswith('.vcf.gz') else '.vcf'
    
    # Save file
    upload_dir = settings.get_upload_dir()
    file_path = upload_dir / f"{file_id}{extension}"
    
    try:
        file_size = save_upload_stream(file.file, file_path, settings.max_upload_size)
        validate_stored_upload(file_path, settings.max_uncompressed_upload_size)
        
        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            size=file_size,
            message="File uploaded successfully"
        )
    
    except UploadTooLargeError:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum upload size of {settings.max_upload_size} bytes."
        )
    except UploadInvalidGzipError:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=400, detail="Invalid gzip-compressed VCF file.")
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@router.post("/validate", response_model=ValidationResult)
async def validate_vcf(file_id: str):
    # Find file
    upload_dir = settings.get_upload_dir()
    file_path = find_uploaded_vcf(file_id, upload_dir)
    
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Load marker lists
        hirisplex_markers = MarkerService.load_markers_from_file(
            settings.get_markers_path("hirisplex")
        )
        plex34_markers = MarkerService.load_markers_from_file(
            settings.get_markers_path("plex34")
        )

        required_markers = hirisplex_markers.union(plex34_markers)

        # Process VCF
        with VCFProcessor(file_path) as processor:
            # Check IDs
            has_ids = processor.verify_has_ids()
            
            # Get samples
            samples = processor.get_samples()
            
            # Check markers
            file_markers = processor.get_marker_ids()
            markers_complete, missing_markers = MarkerService.verify_markers(
                file_markers, required_markers
            )
            
            # Check missing genotypes
            missing_count, missing_list = processor.verify_missing_genotypes()
            
            # Check REF/ALT
            ref_alt_valid = processor.verify_ref_alt()

            duplicate_report = VCFDuplicateWarningService.verify_duplicate_ids(file_path)
        
        return ValidationResult(
            file_id=file_id,
            filename=file_path.name,
            has_ids=has_ids,
            markers_complete=markers_complete,
            missing_markers=missing_markers,
            missing_genotypes_count=missing_count,
            missing_genotypes=missing_list[:100],  # Limit to first 100
            ref_alt_valid=ref_alt_valid,
            samples=samples,
            sample_count=len(samples),
            duplicate_markers=duplicate_report.duplicate_markers,
            warnings=duplicate_report.warnings,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.post("/convert", response_model=ConversionResponse)
async def convert_vcf(request: ConversionRequest):
    # Find file
    upload_dir = settings.get_upload_dir()
    file_path = find_uploaded_vcf(request.file_id, upload_dir)
    
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Load appropriate markers
        markers = MarkerService.load_markers_from_file(
            settings.get_markers_path(request.marker_type)
        )
        
        # Convert
        with VCFProcessor(file_path) as processor:
            if request.marker_type == "hirisplex":
                df = processor.convert_to_hirisplex(markers)
                filename = "hirisplex_input.csv"
            else:
                df = processor.convert_to_plex34(markers)
                filename = "plex34_input.csv"
        
        # Convert to CSV string
        csv_data = df.to_csv(index=False)
        
        return ConversionResponse(
            file_id=request.file_id,
            marker_type=request.marker_type,
            csv_data=csv_data,
            filename=filename,
            row_count=len(df),
            message="Conversion successful"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")


@router.get("/download/{file_id}/{marker_type}")
async def download_converted(file_id: str, marker_type: str):
    if marker_type not in ["hirisplex", "plex34"]:
        raise HTTPException(status_code=400, detail="Invalid marker type")
    
    # Find file
    upload_dir = settings.get_upload_dir()
    file_path = find_uploaded_vcf(file_id, upload_dir)
    
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Load markers and convert
        markers = MarkerService.load_markers_from_file(
            settings.get_markers_path(marker_type)
        )
        
        with VCFProcessor(file_path) as processor:
            if marker_type == "hirisplex":
                df = processor.convert_to_hirisplex(markers)
                filename = "hirisplex_input.csv"
            else:
                df = processor.convert_to_plex34(markers)
                filename = "plex34_input.csv"
        
        # Create CSV stream
        csv_data = df.to_csv(index=False)
        
        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/markers/{marker_type}", response_model=MarkersResponse)
async def get_markers(marker_type: str):
    if marker_type not in ["hirisplex", "plex34"]:
        raise HTTPException(status_code=400, detail="Invalid marker type")
    
    try:
        markers = MarkerService.load_markers_from_file(
            settings.get_markers_path(marker_type)
        )
        
        return MarkersResponse(
            marker_type=marker_type,
            markers=sorted(list(markers)),
            count=len(markers)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load markers: {str(e)}")


@router.get("/download-full/{file_id}")
async def download_full_vcf_csv(file_id: str):
    """Download full VCF as CSV (all rows, not just converted)"""

    # Find file
    upload_dir = settings.get_upload_dir()
    file_path = find_uploaded_vcf(file_id, upload_dir)

    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        with VCFProcessor(file_path) as processor:
            df = processor.get_full_vcf_dataframe()

        # Create CSV stream
        csv_data = df.to_csv(index=False)

        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=converted_vcf.csv"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
