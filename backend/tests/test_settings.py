from unittest import TestCase
from unittest.mock import patch

from app.core.config import GIB, MIB, Settings


class SettingsDefaultsTest(TestCase):
    def test_defaults_match_security_limits(self) -> None:
        # Given: no environment overrides (and no .env file influence for the keys under test).
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings(_env_file=None)

        # Then: the documented defaults load.
        self.assertEqual(settings.app_env, "development")
        self.assertTrue(settings.is_development)
        self.assertEqual(settings.api_shared_secret, "")
        self.assertEqual(settings.max_upload_size, 20 * MIB)
        self.assertEqual(settings.max_uncompressed_upload_size, 100 * MIB)
        self.assertEqual(settings.upload_idle_ttl_seconds, 300)
        self.assertEqual(settings.upload_max_age_seconds, 1800)
        self.assertEqual(settings.max_upload_dir_bytes, 1 * GIB)
        self.assertEqual(settings.max_vcf_samples, 5000)
        self.assertEqual(settings.max_vcf_variants, 10000)
        self.assertEqual(settings.max_vcf_cells, 2_000_000)
        self.assertEqual(settings.max_concurrent_heavy_jobs, 2)
        self.assertEqual(settings.max_artifact_age_seconds, 1800)
        self.assertEqual(settings.max_artifact_count, 100)
        self.assertEqual(settings.max_artifact_dir_bytes, 512 * MIB)
        self.assertEqual(settings.max_structure_input_bytes, 50 * MIB)
        self.assertEqual(settings.max_results_upload_bytes, 5 * MIB)
        self.assertEqual(settings.max_results_rows, 10000)
        self.assertEqual(settings.max_structure_output_lines, 10000)
        self.assertEqual(settings.max_structure_clusters, 64)
        self.assertEqual(settings.sweep_interval_seconds, 60)

    def test_environment_overrides_are_honoured(self) -> None:
        # Given: environment variables overriding a limit and the environment name.
        with patch.dict("os.environ", {"MAX_UPLOAD_SIZE": "1", "APP_ENV": "production"}, clear=True):
            settings = Settings(_env_file=None)

        # Then: the overrides win over the defaults.
        self.assertEqual(settings.max_upload_size, 1)
        self.assertFalse(settings.is_development)
