from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

MIB = 1024 * 1024
GIB = 1024 * MIB


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # API
    backend_port: int = 3002
    app_title: str = "HIrisPlex-S API"
    app_version: str = "1.0.0"
    app_env: str = "development"  # "development" enables /docs; anything else hides them

    # Access control: when non-empty, /api/* requires a matching X-Internal-Token header
    api_shared_secret: str = ""

    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Upload storage
    upload_dir: str = "uploads"
    artifact_dir: str = "artifacts"
    max_upload_size: int = 20 * MIB
    max_uncompressed_upload_size: int = 100 * MIB
    max_upload_dir_bytes: int = 1 * GIB
    upload_idle_ttl_seconds: int = 300
    upload_max_age_seconds: int = 1800
    sweep_interval_seconds: float = 60

    # VCF shape limits (enforced at upload)
    max_vcf_samples: int = 5000
    max_vcf_variants: int = 10000
    max_vcf_cells: int = 2_000_000

    # Heavy processing
    max_concurrent_heavy_jobs: int = 2

    # STRUCTURE artifacts
    max_artifact_age_seconds: int = 1800
    max_artifact_count: int = 100
    max_artifact_dir_bytes: int = 512 * MIB
    max_structure_input_bytes: int = 50 * MIB

    # Results readers
    max_results_upload_bytes: int = 5 * MIB
    max_results_rows: int = 10000
    max_structure_output_lines: int = 10000
    max_structure_clusters: int = 64

    # Data paths
    hirisplex_markers_path: str = "data/hrisplexs_id.txt"
    plex34_markers_path: str = "data/plex34_id.txt"
    plex34_structure_population_path: str = "data/plex34_structure/metapop_3202samples.csv"
    plex34_structure_mainparams_path: str = "data/plex34_structure/mainparams"
    plex34_structure_extraparams_path: str = "data/plex34_structure/extraparams"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"

    def get_markers_path(self, marker_type: str) -> Path:
        """Get absolute path to marker file"""
        if marker_type == "hirisplex":
            return self._app_path(self.hirisplex_markers_path)
        elif marker_type == "plex34":
            return self._app_path(self.plex34_markers_path)
        else:
            raise ValueError(f"Unknown marker type: {marker_type}")

    def get_upload_dir(self) -> Path:
        """Get absolute path to upload directory"""
        upload_path = self._app_path(self.upload_dir)
        upload_path.mkdir(parents=True, exist_ok=True)
        return upload_path

    def get_artifact_dir(self) -> Path:
        artifact_path = self._app_path(self.artifact_dir)
        artifact_path.mkdir(parents=True, exist_ok=True)
        return artifact_path

    def get_plex34_structure_population_path(self) -> Path:
        return self._app_path(self.plex34_structure_population_path)

    def get_plex34_structure_mainparams_path(self) -> Path:
        return self._app_path(self.plex34_structure_mainparams_path)

    def get_plex34_structure_extraparams_path(self) -> Path:
        return self._app_path(self.plex34_structure_extraparams_path)

    def _app_path(self, configured_path: str) -> Path:
        path = Path(configured_path)
        if path.is_absolute():
            return path.resolve()
        return (Path(__file__).resolve().parents[1] / path).resolve()


settings = Settings()
