from io import BytesIO
from unittest import TestCase

import anyio
from starlette.datastructures import UploadFile

from app.api.routes.plex34_structure import parse_plex34_structure_output
from app.services import Plex34StructureOutputParser


STRUCTURE_OUTPUT = """
Header
Inferred ancestry of individuals:
1 sample_A (0) : 0.123 0.877
2 sample_B 0.450 0.550
Estimated Allele Frequencies in each cluster
Footer
"""


class Plex34StructureOutputParserTest(TestCase):
    def test_parse_text_returns_structured_ancestry_when_sample_lines_have_probabilities(self) -> None:
        # Given: STRUCTURE output with colon-delimited and trailing probability sample lines.

        # When: the parser extracts the inferred ancestry section.
        parsed = Plex34StructureOutputParser.parse_text(STRUCTURE_OUTPUT)

        # Then: raw sample lines are preserved and structured ancestry rows expose top clusters.
        self.assertEqual(parsed.sample_lines, ["1 sample_A (0) : 0.123 0.877", "2 sample_B 0.450 0.550"])
        self.assertEqual(len(parsed.ancestry_rows), 2)
        self.assertEqual(parsed.ancestry_rows[0].sample_id, "sample_A")
        self.assertEqual(parsed.ancestry_rows[0].probabilities[0].label, "Cluster 1")
        self.assertEqual(parsed.ancestry_rows[0].probabilities[0].probability, 0.123)
        self.assertEqual(parsed.ancestry_rows[0].top_cluster, "Cluster 2")
        self.assertEqual(parsed.ancestry_rows[0].confidence, 0.877)
        self.assertEqual(parsed.ancestry_rows[1].sample_id, "sample_B")
        self.assertEqual(parsed.ancestry_rows[1].top_cluster, "Cluster 2")
        self.assertEqual(parsed.ancestry_rows[1].confidence, 0.55)

    def test_parse_text_raises_when_sample_line_has_no_probabilities(self) -> None:
        # Given: a STRUCTURE output sample row without cluster probabilities.
        structure_output = """
Header
Inferred ancestry of individuals:
1 sample_A (0) :
Estimated Allele Frequencies in each cluster
Footer
"""

        # When/Then: parsing fails instead of inventing ancestry output.
        with self.assertRaisesRegex(Exception, "No cluster probabilities"):
            Plex34StructureOutputParser.parse_text(structure_output)

    def test_structure_output_endpoint_includes_structured_ancestry_rows(self) -> None:
        # Given: a multipart STRUCTURE output upload.
        upload = UploadFile(file=BytesIO(STRUCTURE_OUTPUT.encode("utf-8")), filename="structure.out")

        # When: the output parser endpoint receives the STRUCTURE text.
        payload = anyio.run(parse_plex34_structure_output, upload)

        # Then: the response keeps the legacy fields and includes structured ancestry rows.
        self.assertEqual(payload.sample_lines, ["1 sample_A (0) : 0.123 0.877", "2 sample_B 0.450 0.550"])
        self.assertEqual(payload.count, 2)
        self.assertEqual(payload.message, "Plex34 STRUCTURE output parsed successfully")
        self.assertEqual(payload.ancestry_rows[0].sample_id, "sample_A")
        self.assertEqual(payload.ancestry_rows[0].top_cluster, "Cluster 2")
        self.assertEqual(payload.ancestry_rows[0].confidence, 0.877)
