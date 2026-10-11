from pathlib import Path
from uuid import UUID

from .retention import touch_last_use


def find_uploaded_vcf(file_id: str, upload_dir: Path) -> Path | None:
    """Locate a stored upload by ID and record the use (refreshes its idle TTL)."""
    try:
        UUID(file_id)
    except ValueError:
        return None

    for extension in (".vcf", ".vcf.gz"):
        candidate = upload_dir / f"{file_id}{extension}"
        if candidate.exists():
            touch_last_use(candidate)
            return candidate
    return None
