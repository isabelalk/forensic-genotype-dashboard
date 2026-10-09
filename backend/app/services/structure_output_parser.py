import re
from dataclasses import dataclass

from app.models import Plex34AncestryRow, Plex34ClusterProbability


INFERRED_ANCESTRY_SECTION = "Inferred ancestry of individuals"
ALLELE_FREQUENCIES_SECTION = "Estimated Allele Frequencies in each cluster"
PROBABILITY_TOKEN = re.compile(r"^(?:0(?:\.\d+)?|1(?:\.0+)?|\.\d+)$")


@dataclass(frozen=True, slots=True)
class ParsedStructureOutput:
    sample_lines: list[str]
    ancestry_rows: list[Plex34AncestryRow]


@dataclass(frozen=True, slots=True)
class Plex34StructureOutputParseError(Exception):
    detail: str

    def __str__(self) -> str:
        return self.detail


class Plex34StructureOutputParser:
    @staticmethod
    def parse_text(output_text: str) -> ParsedStructureOutput:
        lines = output_text.splitlines()
        start_index: int | None = None
        end_index: int | None = None

        for index, line in enumerate(lines):
            if INFERRED_ANCESTRY_SECTION in line:
                start_index = index
                continue
            if ALLELE_FREQUENCIES_SECTION in line:
                end_index = index
                break

        if start_index is None:
            raise Plex34StructureOutputParseError(
                f"Section '{INFERRED_ANCESTRY_SECTION}' was not found."
            )
        if end_index is None:
            raise Plex34StructureOutputParseError(
                f"Section '{ALLELE_FREQUENCIES_SECTION}' was not found."
            )

        sample_lines = [
            stripped_line
            for line in lines[start_index:end_index]
            if (stripped_line := line.strip()) and stripped_line[0].isdigit()
        ]
        if not sample_lines:
            raise Plex34StructureOutputParseError(
                "No inferred ancestry sample lines were found in the STRUCTURE output."
            )

        ancestry_rows = [
            Plex34StructureOutputParser._parse_ancestry_row(row_index=row_index, sample_line=sample_line)
            for row_index, sample_line in enumerate(sample_lines, start=1)
        ]

        return ParsedStructureOutput(sample_lines=sample_lines, ancestry_rows=ancestry_rows)

    @staticmethod
    def _parse_ancestry_row(row_index: int, sample_line: str) -> Plex34AncestryRow:
        header_text, probabilities = Plex34StructureOutputParser._split_probability_tokens(sample_line)
        cluster_probabilities = [
            Plex34ClusterProbability(label=f"Cluster {cluster_index}", probability=probability)
            for cluster_index, probability in enumerate(probabilities, start=1)
        ]
        top_probability = max(cluster_probabilities, key=lambda probability: probability.probability)
        return Plex34AncestryRow(
            row_index=row_index,
            sample_id=Plex34StructureOutputParser._sample_id(header_text),
            probabilities=cluster_probabilities,
            top_cluster=top_probability.label,
            confidence=top_probability.probability,
        )

    @staticmethod
    def _split_probability_tokens(sample_line: str) -> tuple[str, list[float]]:
        if ":" in sample_line:
            header_text, probability_text = sample_line.split(":", 1)
            probabilities = [
                Plex34StructureOutputParser._parse_probability(token)
                for token in probability_text.split()
                if Plex34StructureOutputParser._is_probability_token(token)
            ]
            if probabilities:
                return header_text, probabilities
            raise Plex34StructureOutputParseError(
                f"No cluster probabilities were found after ':' in STRUCTURE sample line: {sample_line}"
            )

        tokens = sample_line.split()
        probability_tokens: list[str] = []
        for token in reversed(tokens):
            if not Plex34StructureOutputParser._is_probability_token(token):
                break
            probability_tokens.append(token)

        if not probability_tokens:
            raise Plex34StructureOutputParseError(
                f"No trailing cluster probabilities were found in STRUCTURE sample line: {sample_line}"
            )

        probability_tokens.reverse()
        header_tokens = tokens[: len(tokens) - len(probability_tokens)]
        return " ".join(header_tokens), [
            Plex34StructureOutputParser._parse_probability(token) for token in probability_tokens
        ]

    @staticmethod
    def _is_probability_token(token: str) -> bool:
        return bool(PROBABILITY_TOKEN.fullmatch(token))

    @staticmethod
    def _parse_probability(token: str) -> float:
        try:
            return float(token)
        except ValueError as error:
            raise Plex34StructureOutputParseError(f"Invalid STRUCTURE probability token: {token}") from error

    @staticmethod
    def _sample_id(header_text: str) -> str:
        tokens = header_text.split()
        if len(tokens) >= 2 and tokens[0].isdigit():
            return tokens[1]
        if tokens:
            return tokens[0]
        raise Plex34StructureOutputParseError("STRUCTURE sample line is missing a sample identifier.")
