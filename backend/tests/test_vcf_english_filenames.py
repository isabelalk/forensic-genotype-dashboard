from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from unittest import TestCase
from unittest.mock import patch

import anyio

from app.api.routes import vcf
from app.models import ConversionRequest


@dataclass(frozen=True, slots=True)
class RouteFilenameDataFrame:
    rows: int = 1

    def to_csv(self, index: bool = False) -> str:
        return "SampleID\nsample-1\n"

    def __len__(self) -> int:
        return self.rows


class RouteFilenameProcessor:
    def __init__(self, vcf_path: Path) -> None:
        self.vcf_path = vcf_path

    def __enter__(self) -> "RouteFilenameProcessor":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    def convert_to_hirisplex(self, required_markers: set[str]) -> RouteFilenameDataFrame:
        return RouteFilenameDataFrame()

    def convert_to_plex34(self, required_markers: set[str]) -> RouteFilenameDataFrame:
        return RouteFilenameDataFrame()

    def get_full_vcf_dataframe(self) -> RouteFilenameDataFrame:
        return RouteFilenameDataFrame()


@dataclass(frozen=True, slots=True)
class RouteFilenameSettings:
    def get_upload_dir(self) -> Path:
        return Path(".")

    def get_markers_path(self, marker_type: str) -> Path:
        return Path(f"{marker_type}.txt")


class VCFEnglishFilenamesTest(TestCase):
    def test_conversion_and_download_routes_use_english_csv_filenames(self) -> None:
        # Given: an uploaded VCF lookup and processor are available to the route layer.
        with (
            patch.object(vcf, "settings", RouteFilenameSettings()),
            patch.object(vcf, "find_uploaded_vcf", return_value=Path("uploaded.vcf")),
            patch.object(vcf.MarkerService, "load_markers_from_file", return_value={"rs1"}),
            patch.object(vcf, "VCFProcessor", RouteFilenameProcessor),
        ):
            # When: conversion and download endpoints produce user-facing CSV filenames.
            hirisplex_payload = anyio.run(
                vcf.convert_vcf,
                ConversionRequest(file_id="file-1", marker_type="hirisplex"),
            )
            plex34_payload = anyio.run(
                vcf.convert_vcf,
                ConversionRequest(file_id="file-1", marker_type="plex34"),
            )
            plex34_download = anyio.run(vcf.download_converted, "file-1", "plex34")
            full_vcf_download = anyio.run(vcf.download_full_vcf_csv, "file-1")

        # Then: every surfaced CSV filename is English.
        self.assertEqual(hirisplex_payload.filename, "hirisplex_input.csv")
        self.assertEqual(plex34_payload.filename, "plex34_input.csv")
        self.assertEqual(
            plex34_download.headers["content-disposition"],
            "attachment; filename=plex34_input.csv",
        )
        self.assertEqual(
            full_vcf_download.headers["content-disposition"],
            "attachment; filename=converted_vcf.csv",
        )
