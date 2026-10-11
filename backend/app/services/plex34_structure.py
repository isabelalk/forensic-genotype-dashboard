import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

from ._plex34_structure_io import (
    EXTRAPARAMS_FILENAME,
    MAINPARAMS_FILENAME,
    STRUCTURE_INPUT_FILENAME,
    MainparamsData,
    Plex34StructureConfigError,
    Plex34StructureDataError,
    Plex34StructureOutputTooLargeError,
    StructureInputData,
    load_marker_ids,
    load_population_data,
    parse_vcf,
    write_mainparams,
    write_structure_input,
    write_zip,
)
from .retention import sweep_artifacts

__all__ = [
    "Plex34StructureConfigError",
    "Plex34StructureError",
    "Plex34StructureOutputTooLargeError",
    "Plex34StructureService",
    "StructureArtifact",
    "StructureArtifactRequest",
    "StructureTemplatePaths",
]


class Plex34StructureError(Exception):
    """User-facing generation error (bad VCF content, output over the cap)."""


@dataclass(frozen=True)
class StructureArtifact:
    artifact_id: str
    filenames: list[str]
    num_samples: int
    num_markers: int
    missing_markers: list[str]
    warnings: list[str]
    zip_path: Path


@dataclass(frozen=True)
class StructureTemplatePaths:
    population_csv: Path
    mainparams: Path
    extraparams: Path


@dataclass(frozen=True)
class StructureArtifactRequest:
    vcf_path: Path
    marker_path: Path
    template_paths: StructureTemplatePaths
    artifact_root: Path
    max_artifact_age_seconds: int
    max_artifact_count: int
    max_artifact_dir_bytes: int
    max_structure_input_bytes: int


class Plex34StructureService:
    @staticmethod
    def generate_artifact(request: StructureArtifactRequest) -> StructureArtifact:
        # Make room first: age/count/byte rules, reserving the worst case for this artifact.
        sweep_artifacts(
            request.artifact_root,
            max_age_seconds=request.max_artifact_age_seconds,
            max_count=request.max_artifact_count - 1,
            max_bytes=request.max_artifact_dir_bytes,
            reserve_bytes=request.max_structure_input_bytes,
        )
        try:
            markers = load_marker_ids(request.marker_path)
            population = load_population_data(request.template_paths.population_csv)
            vcf_data = parse_vcf(request.vcf_path, markers)
        except Plex34StructureDataError as error:
            raise Plex34StructureError(str(error)) from error
        ordered_markers = [marker for marker in markers if marker in vcf_data.markers]
        missing_markers = [marker for marker in markers if marker not in vcf_data.markers]
        artifact_id = uuid.uuid4().hex
        artifact_dir = request.artifact_root / artifact_id
        artifact_dir.mkdir(parents=True)

        try:
            input_path = artifact_dir / STRUCTURE_INPUT_FILENAME
            mainparams_path = artifact_dir / MAINPARAMS_FILENAME
            extraparams_path = artifact_dir / EXTRAPARAMS_FILENAME
            zip_path = artifact_dir / f"plex34_structure_{artifact_id}.zip"

            write_structure_input(
                input_path,
                StructureInputData(
                    samples=vcf_data.samples,
                    ordered_markers=ordered_markers,
                    markers=vcf_data.markers,
                    population=population,
                ),
                max_bytes=request.max_structure_input_bytes,
            )
            write_mainparams(
                request.template_paths.mainparams,
                mainparams_path,
                MainparamsData(
                    num_samples=len(vcf_data.samples),
                    num_markers=len(ordered_markers),
                    input_filename=STRUCTURE_INPUT_FILENAME,
                ),
            )
            shutil.copyfile(request.template_paths.extraparams, extraparams_path)
            write_zip(zip_path, (input_path, mainparams_path, extraparams_path))
        except Plex34StructureOutputTooLargeError as error:
            shutil.rmtree(artifact_dir, ignore_errors=True)
            raise Plex34StructureError(str(error)) from error
        except BaseException:
            shutil.rmtree(artifact_dir, ignore_errors=True)
            raise

        warnings = list(vcf_data.warnings)
        if missing_markers:
            warnings.append(f"{len(missing_markers)} Plex34 markers were not found in the VCF.")

        return StructureArtifact(
            artifact_id=artifact_id,
            filenames=[STRUCTURE_INPUT_FILENAME, MAINPARAMS_FILENAME, EXTRAPARAMS_FILENAME, zip_path.name],
            num_samples=len(vcf_data.samples),
            num_markers=len(ordered_markers),
            missing_markers=missing_markers,
            warnings=warnings,
            zip_path=zip_path,
        )
