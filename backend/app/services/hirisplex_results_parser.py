import csv
import math
from dataclasses import dataclass
from io import StringIO
from typing import Final

from app.models import HirisPlexSProbabilities, HirisPlexSResultRow, HirisPlexSResultsResponse, HirisPlexSTopPredictions


REQUIRED_PROBABILITY_COLUMNS: Final[tuple[str, ...]] = (
    "PBlueEye",
    "PIntermediateEye",
    "PBrownEye",
    "PBlondHair",
    "PBrownHair",
    "PRedHair",
    "PBlackHair",
    "PLightHair",
    "PDarkHair",
)

SKIN_PROBABILITY_COLUMNS: Final[tuple[str, ...]] = (
    "PVeryPaleSkin",
    "PPaleSkin",
    "PIntermediateSkin",
    "PDarkSkin",
    "PDarktoBlackSkin",
)


@dataclass(frozen=True, slots=True)
class HirisPlexSResultsParseError(Exception):
    detail: str

    def __str__(self) -> str:
        return self.detail


class HirisPlexSResultsParser:
    @staticmethod
    def parse_text(csv_text: str) -> HirisPlexSResultsResponse:
        reader = csv.DictReader(StringIO(csv_text))
        fieldnames = reader.fieldnames
        if fieldnames is None:
            raise HirisPlexSResultsParseError("HIrisPlex-S results CSV is missing a header row.")

        missing_columns = [column for column in REQUIRED_PROBABILITY_COLUMNS if column not in fieldnames]
        if missing_columns:
            raise HirisPlexSResultsParseError(
                f"HIrisPlex-S results CSV is missing required probability columns: {', '.join(missing_columns)}."
            )
        present_skin_columns = [column for column in SKIN_PROBABILITY_COLUMNS if column in fieldnames]
        has_skin_columns = len(present_skin_columns) == len(SKIN_PROBABILITY_COLUMNS)
        if present_skin_columns and len(present_skin_columns) != len(SKIN_PROBABILITY_COLUMNS):
            missing_skin_columns = [column for column in SKIN_PROBABILITY_COLUMNS if column not in fieldnames]
            raise HirisPlexSResultsParseError(
                "HIrisPlex-S results CSV is missing required skin probability columns: "
                f"{', '.join(missing_skin_columns)}."
            )

        rows = [
            HirisPlexSResultsParser._parse_row(
                row_index=row_index,
                raw_row=raw_row,
                has_skin_columns=has_skin_columns,
            )
            for row_index, raw_row in enumerate(reader, start=1)
        ]
        if not rows:
            raise HirisPlexSResultsParseError("HIrisPlex-S results CSV does not contain result rows.")

        return HirisPlexSResultsResponse(
            rows=rows,
            count=len(rows),
            message="HIrisPlex-S results parsed successfully",
        )

    @staticmethod
    def _parse_row(row_index: int, raw_row: dict[str, str], has_skin_columns: bool) -> HirisPlexSResultRow:
        probabilities = HirisPlexSProbabilities(
            PBlueEye=HirisPlexSResultsParser._parse_probability(raw_row["PBlueEye"], row_index, "PBlueEye"),
            PIntermediateEye=HirisPlexSResultsParser._parse_probability(
                raw_row["PIntermediateEye"], row_index, "PIntermediateEye"
            ),
            PBrownEye=HirisPlexSResultsParser._parse_probability(raw_row["PBrownEye"], row_index, "PBrownEye"),
            PBlondHair=HirisPlexSResultsParser._parse_probability(raw_row["PBlondHair"], row_index, "PBlondHair"),
            PBrownHair=HirisPlexSResultsParser._parse_probability(raw_row["PBrownHair"], row_index, "PBrownHair"),
            PRedHair=HirisPlexSResultsParser._parse_probability(raw_row["PRedHair"], row_index, "PRedHair"),
            PBlackHair=HirisPlexSResultsParser._parse_probability(raw_row["PBlackHair"], row_index, "PBlackHair"),
            PLightHair=HirisPlexSResultsParser._parse_probability(raw_row["PLightHair"], row_index, "PLightHair"),
            PDarkHair=HirisPlexSResultsParser._parse_probability(raw_row["PDarkHair"], row_index, "PDarkHair"),
            PVeryPaleSkin=HirisPlexSResultsParser._parse_optional_skin_probability(
                raw_row, row_index, "PVeryPaleSkin", has_skin_columns
            ),
            PPaleSkin=HirisPlexSResultsParser._parse_optional_skin_probability(
                raw_row, row_index, "PPaleSkin", has_skin_columns
            ),
            PIntermediateSkin=HirisPlexSResultsParser._parse_optional_skin_probability(
                raw_row, row_index, "PIntermediateSkin", has_skin_columns
            ),
            PDarkSkin=HirisPlexSResultsParser._parse_optional_skin_probability(
                raw_row, row_index, "PDarkSkin", has_skin_columns
            ),
            PDarktoBlackSkin=HirisPlexSResultsParser._parse_optional_skin_probability(
                raw_row, row_index, "PDarktoBlackSkin", has_skin_columns
            ),
        )
        return HirisPlexSResultRow(
            row_index=row_index,
            sample_id=HirisPlexSResultsParser._sample_id(raw_row),
            probabilities=probabilities,
            top_predictions=HirisPlexSResultsParser._top_predictions(probabilities),
        )

    @staticmethod
    def _parse_probability(raw_value: str | None, row_index: int, column: str) -> float:
        if raw_value is None or raw_value.strip() == "":
            raise HirisPlexSResultsParseError(
                f"Row {row_index} is missing a probability value for {column}."
            )
        try:
            probability = float(raw_value)
        except (TypeError, ValueError) as error:
            raise HirisPlexSResultsParseError(
                f"Row {row_index} has a non-numeric value for {column}: {raw_value!r}."
            ) from error
        if not math.isfinite(probability) or probability < 0 or probability > 1:
            raise HirisPlexSResultsParseError(
                f"Row {row_index} has an out-of-range probability for {column}: {raw_value!r}."
            )
        return probability

    @staticmethod
    def _parse_optional_skin_probability(
        raw_row: dict[str, str],
        row_index: int,
        column: str,
        has_skin_columns: bool,
    ) -> float | None:
        if not has_skin_columns:
            return None
        raw_value = raw_row.get(column)
        return HirisPlexSResultsParser._parse_probability(raw_value, row_index, column)

    @staticmethod
    def _sample_id(raw_row: dict[str, str]) -> str | None:
        for column in ("SampleID", "sample_id", "sampleid", "Sample", "sample"):
            value = raw_row.get(column)
            if value:
                return value
        return None

    @staticmethod
    def _top_predictions(probabilities: HirisPlexSProbabilities) -> HirisPlexSTopPredictions:
        eye_color, eye_probability = max(
            (
                ("Blue", probabilities.PBlueEye),
                ("Intermediate", probabilities.PIntermediateEye),
                ("Brown", probabilities.PBrownEye),
            ),
            key=lambda item: item[1],
        )
        hair_color, hair_probability = max(
            (
                ("Blond", probabilities.PBlondHair),
                ("Brown", probabilities.PBrownHair),
                ("Red", probabilities.PRedHair),
                ("Black", probabilities.PBlackHair),
            ),
            key=lambda item: item[1],
        )
        hair_shade, hair_shade_probability = max(
            (("Light", probabilities.PLightHair), ("Dark", probabilities.PDarkHair)),
            key=lambda item: item[1],
        )
        skin, skin_probability = HirisPlexSResultsParser._top_skin_prediction(probabilities)
        return HirisPlexSTopPredictions(
            eye_color=eye_color,
            eye_probability=eye_probability,
            hair_color=hair_color,
            hair_probability=hair_probability,
            hair_shade=hair_shade,
            hair_shade_probability=hair_shade_probability,
            skin=skin,
            skin_probability=skin_probability,
        )

    @staticmethod
    def _top_skin_prediction(probabilities: HirisPlexSProbabilities) -> tuple[str, float | None]:
        if probabilities.PVeryPaleSkin is None:
            return "unavailable", None
        skin, skin_probability = max(
            (
                ("Very Pale", probabilities.PVeryPaleSkin),
                ("Pale", probabilities.PPaleSkin),
                ("Intermediate", probabilities.PIntermediateSkin),
                ("Dark", probabilities.PDarkSkin),
                ("Dark-to-Black", probabilities.PDarktoBlackSkin),
            ),
            key=lambda item: item[1] if item[1] is not None else -1,
        )
        return skin, skin_probability
