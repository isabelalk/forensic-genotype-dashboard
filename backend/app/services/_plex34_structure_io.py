from __future__ import annotations

import csv
import gzip
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, TextIO


BASE_TO_CODE = {"A": "2", "C": "3", "G": "5", "T": "7"}
MISSING_CODE = "-9"
PARENTAL_CONTINENTS = {"Africa", "Europe", "East Asia", "South Asia"}
STRUCTURE_INPUT_FILENAME = "plex34_structure_input.txt"
MAINPARAMS_FILENAME = "mainparams"
EXTRAPARAMS_FILENAME = "extraparams"


class Plex34StructureDataError(Exception):
    pass


@dataclass(frozen=True)
class PopulationEntry:
    pop_id: int
    popflag: int


@dataclass(frozen=True)
class VcfMarker:
    marker_id: str
    genotypes: dict[str, tuple[str, str]]


@dataclass(frozen=True)
class VcfData:
    samples: list[str]
    markers: dict[str, VcfMarker]
    warnings: list[str]


@dataclass(frozen=True)
class StructureInputData:
    samples: list[str]
    ordered_markers: list[str]
    markers: dict[str, VcfMarker]
    population: dict[str, PopulationEntry]


@dataclass(frozen=True)
class MainparamsData:
    num_samples: int
    num_markers: int
    input_filename: str


def load_marker_ids(marker_path: Path) -> list[str]:
    if not marker_path.exists():
        raise Plex34StructureDataError(f"Marker file not found: {marker_path}")

    markers: list[str] = []
    seen: set[str] = set()
    with marker_path.open("r", encoding="utf-8") as marker_file:
        for raw_line in marker_file:
            marker = raw_line.strip()
            if marker and not marker.startswith("#") and marker not in seen:
                markers.append(marker)
                seen.add(marker)

    if not markers:
        raise Plex34StructureDataError("Plex34 marker file is empty.")
    return markers


def load_population_data(population_csv: Path) -> dict[str, PopulationEntry]:
    if not population_csv.exists():
        raise Plex34StructureDataError(f"Population CSV not found: {population_csv}")

    with population_csv.open("r", encoding="utf-8-sig", newline="") as population_file:
        first_line = population_file.readline()
        delimiter = _detect_delimiter(first_line)
        population_file.seek(0)
        reader = csv.DictReader(population_file, delimiter=delimiter)
        columns = _required_columns(reader.fieldnames)
        return _read_population_rows(reader, columns)


def parse_vcf(vcf_path: Path, required_markers: list[str]) -> VcfData:
    marker_filter = set(required_markers)
    samples: list[str] = []
    markers: dict[str, VcfMarker] = {}
    warnings: list[str] = []

    with _open_vcf(vcf_path) as vcf_file:
        for raw_line in vcf_file:
            if raw_line.startswith("##"):
                continue
            if raw_line.startswith("#CHROM"):
                samples = raw_line.rstrip("\n").split("\t")[9:]
                continue
            if not samples:
                continue

            marker = _parse_marker_line(raw_line, samples, marker_filter)
            if marker is None:
                continue
            if marker.marker_id in markers:
                warnings.append(f"Duplicate marker {marker.marker_id} ignored after first occurrence.")
                continue
            markers[marker.marker_id] = marker

    if not samples:
        raise Plex34StructureDataError("VCF header with sample columns was not found.")
    return VcfData(samples=samples, markers=markers, warnings=warnings)


def write_structure_input(output_path: Path, data: StructureInputData) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        for sample in data.samples:
            entry = data.population.get(sample, PopulationEntry(pop_id=0, popflag=0))
            row = [sample, str(entry.pop_id), str(entry.popflag)]
            for marker_id in data.ordered_markers:
                allele_one, allele_two = data.markers[marker_id].genotypes.get(sample, (MISSING_CODE, MISSING_CODE))
                row.extend([allele_one, allele_two])
            output_file.write("\t".join(row) + "\n")


def write_mainparams(template_path: Path, output_path: Path, data: MainparamsData) -> None:
    replacements = {
        r"#define\s+NUMINDS\s+\d+": f"#define NUMINDS {data.num_samples}",
        r"#define\s+NUMLOCI\s+\d+": f"#define NUMLOCI {data.num_markers}",
        r"#define\s+INFILE.*": f"#define INFILE {data.input_filename}",
        r"#define\s+LABEL\s+\d+": "#define LABEL 1",
        r"#define\s+POPDATA\s+\d+": "#define POPDATA 1",
        r"#define\s+POPFLAG\s+\d+": "#define POPFLAG 1",
        r"#define\s+LOCDATA\s+\d+": "#define LOCDATA 1",
        r"#define\s+EXTRACOLS\s+\d+": "#define EXTRACOLS 0",
        r"#define\s+MARKERNAMES\s+\d+": "#define MARKERNAMES 0",
        r"#define\s+ONEROWPERIND\s+\d+": "#define ONEROWPERIND 1",
        r"#define\s+USEPOPINFO\s+\d+": "#define USEPOPINFO 1",
    }
    text = template_path.read_text(encoding="utf-8")
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    output_path.write_text(text, encoding="utf-8")


def write_zip(zip_path: Path, files: Iterable[Path]) -> None:
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as artifact_zip:
        for file_path in files:
            artifact_zip.write(file_path, arcname=file_path.name)


def _detect_delimiter(first_line: str) -> str:
    if "\t" in first_line:
        return "\t"
    if ";" in first_line:
        return ";"
    return ","


def _required_columns(fieldnames: Optional[list[str]]) -> dict[str, str]:
    if fieldnames is None:
        raise Plex34StructureDataError("Population CSV is missing a header row.")

    columns = {name.lower().strip(): name for name in fieldnames}
    required = ["sample", "continent", "pop_id"]
    missing = [name for name in required if name not in columns]
    if missing:
        raise Plex34StructureDataError(f"Population CSV is missing columns: {', '.join(missing)}")
    return columns


def _read_population_rows(rows: csv.DictReader[str], columns: dict[str, str]) -> dict[str, PopulationEntry]:
    population: dict[str, PopulationEntry] = {}
    for row in rows:
        sample = row[columns["sample"]].strip()
        continent = row[columns["continent"]].strip()
        pop_id = _parse_pop_id(row[columns["pop_id"]])
        if sample:
            population[sample] = PopulationEntry(pop_id=pop_id, popflag=1 if continent in PARENTAL_CONTINENTS else 0)
    return population


def _parse_pop_id(raw_value: str) -> int:
    try:
        return int(raw_value)
    except ValueError:
        return 0


def _open_vcf(vcf_path: Path) -> TextIO:
    if vcf_path.name.endswith(".gz"):
        return gzip.open(vcf_path, "rt", encoding="utf-8")
    return vcf_path.open("r", encoding="utf-8")


def _parse_marker_line(raw_line: str, samples: list[str], marker_filter: set[str]) -> Optional[VcfMarker]:
    fields = raw_line.rstrip("\n").split("\t")
    if len(fields) < 9:
        raise Plex34StructureDataError("VCF row has fewer than 9 fixed columns.")

    marker_id = fields[2]
    if marker_id not in marker_filter:
        return None

    allele_map = [fields[3].upper()] + [alt.upper() for alt in fields[4].split(",")]
    sample_genotypes = {
        sample: _encode_sample_genotype(sample_field, allele_map)
        for sample, sample_field in zip(samples, fields[9:])
    }
    return VcfMarker(marker_id=marker_id, genotypes=sample_genotypes)


def _encode_sample_genotype(sample_field: str, allele_map: list[str]) -> tuple[str, str]:
    genotype = sample_field.split(":", 1)[0]
    if genotype in {".", "./.", ".|.", "NA", "na", "nan", "NaN"}:
        return (MISSING_CODE, MISSING_CODE)

    separator = "/" if "/" in genotype else "|"
    alleles = genotype.split(separator)
    if len(alleles) != 2 or "." in alleles:
        return (MISSING_CODE, MISSING_CODE)

    return (_encode_allele(alleles[0], allele_map), _encode_allele(alleles[1], allele_map))


def _encode_allele(raw_allele: str, allele_map: list[str]) -> str:
    try:
        base = allele_map[int(raw_allele)]
    except (ValueError, IndexError):
        return MISSING_CODE
    return BASE_TO_CODE.get(base, MISSING_CODE)
