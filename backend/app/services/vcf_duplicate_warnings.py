from dataclasses import dataclass
from pathlib import Path

from cyvcf2 import VCF


@dataclass(frozen=True)
class DuplicateMarkerReport:
    duplicate_markers: list[str]
    warnings: list[str]


class VCFDuplicateWarningService:
    @staticmethod
    def verify_duplicate_ids(vcf_path: Path) -> DuplicateMarkerReport:
        seen_markers: set[str] = set()
        duplicate_markers: list[str] = []

        vcf = VCF(str(vcf_path))
        try:
            for variant in vcf:
                marker_id = variant.ID
                if not marker_id or marker_id == ".":
                    continue
                if marker_id in seen_markers:
                    duplicate_markers.append(marker_id)
                    continue
                seen_markers.add(marker_id)
        finally:
            vcf.close()

        warnings: list[str] = []
        if duplicate_markers:
            warnings.append(
                f"{len(duplicate_markers)} duplicate marker ID occurrences were found in the VCF."
            )

        return DuplicateMarkerReport(
            duplicate_markers=duplicate_markers,
            warnings=warnings,
        )
