from unittest import TestCase

from app.main import app


class VCFResultRoutesRemovedTest(TestCase):
    def test_vcf_derived_result_routes_are_not_exposed_after_replacement_apis_exist(self) -> None:
        # Given: the FastAPI app route table after registering replacement result readers.
        paths = {route.path for route in app.routes}

        # When/Then: the old VCF-derived results routes are no longer part of the API surface.
        self.assertNotIn("/api/vcf/calculate-results", paths)
        self.assertNotIn("/api/vcf/download-results/{file_id}", paths)
        self.assertIn("/api/results/hirisplex-s", paths)
        self.assertIn("/api/vcf/plex34/structure-output", paths)
