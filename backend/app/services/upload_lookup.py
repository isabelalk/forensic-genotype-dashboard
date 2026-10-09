from pathlib import Path
from uuid import UUID


def find_uploaded_vcf(file_id: str, upload_dir: Path) -> Path | None:
    try:
        UUID(file_id)
    except ValueError:
        return None

    for extension in (".vcf", ".vcf.gz"):
        candidate = upload_dir / f"{file_id}{extension}"
        if candidate.exists():
            return candidate
    return None
