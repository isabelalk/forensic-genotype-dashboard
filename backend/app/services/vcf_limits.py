import gzip
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

FIXED_VCF_COLUMNS = 9


class VCFLimitError(Exception):
    """The uploaded VCF violates a shape limit; the message is safe to show to the client."""


@dataclass(frozen=True, slots=True)
class VCFLimits:
    max_samples: int
    max_variants: int
    max_cells: int


@dataclass(frozen=True, slots=True)
class VCFShape:
    sample_count: int
    variant_count: int


def check_vcf_limits(vcf_path: Path, limits: VCFLimits) -> VCFShape:
    """Scan the VCF once as text and enforce header and size limits.

    Memory stays flat: nothing per row is retained. Raises VCFLimitError on the
    first violation so a 100 MiB file is abandoned as soon as it is over a cap.
    """
    samples: list[str] | None = None
    variant_count = 0

    with _open_text(vcf_path) as vcf_file:
        for raw_line in vcf_file:
            if raw_line.startswith("##"):
                continue
            if raw_line.startswith("#CHROM"):
                samples = _parse_samples(raw_line, limits)
                continue
            if samples is None:
                continue
            if not raw_line.strip():
                continue
            variant_count += 1
            if variant_count > limits.max_variants:
                raise VCFLimitError(
                    f"VCF has more than {limits.max_variants} variants (maximum allowed is {limits.max_variants})."
                )
            if len(samples) * variant_count > limits.max_cells:
                raise VCFLimitError(
                    f"VCF has more than {limits.max_cells} sample x variant cells "
                    f"(maximum allowed is {limits.max_cells})."
                )

    if samples is None:
        raise VCFLimitError("VCF is missing the #CHROM header line.")
    return VCFShape(sample_count=len(samples), variant_count=variant_count)


def _parse_samples(header_line: str, limits: VCFLimits) -> list[str]:
    samples = header_line.rstrip("\r\n").split("\t")[FIXED_VCF_COLUMNS:]
    if len(samples) > limits.max_samples:
        raise VCFLimitError(
            f"VCF has {len(samples)} samples (maximum allowed is {limits.max_samples})."
        )
    seen: set[str] = set()
    for sample in samples:
        if sample == "":
            raise VCFLimitError("VCF header contains an empty sample name.")
        if any(character.isspace() for character in sample):
            raise VCFLimitError(f"Sample names must not contain whitespace: {sample!r}.")
        if sample in seen:
            raise VCFLimitError(f"VCF header lists the sample name {sample!r} more than once.")
        seen.add(sample)
    return samples


def _open_text(vcf_path: Path) -> TextIO:
    if vcf_path.name.endswith(".gz"):
        return gzip.open(vcf_path, "rt", encoding="utf-8", errors="strict")
    return vcf_path.open("r", encoding="utf-8", errors="strict")
