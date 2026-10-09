from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    # API
    backend_port: int = 3002
    app_title: str = "HIrisPlex-S API"
    app_version: str = "1.0.0"
    
    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    
    # Upload
    upload_dir: str = "uploads"
    artifact_dir: str = "artifacts"
    max_upload_size: int = 104857600  # 100MB
    max_uncompressed_upload_size: int = 104857600
    max_artifact_age_seconds: int = 86400
    max_artifact_count: int = 25
    
    # Data paths
    hirisplex_markers_path: str = "data/hrisplexs_id.txt"
    plex34_markers_path: str = "data/plex34_id.txt"
    plex34_structure_population_path: str = "data/plex34_structure/metapop_3202samples.csv"
    plex34_structure_mainparams_path: str = "data/plex34_structure/mainparams"
    plex34_structure_extraparams_path: str = "data/plex34_structure/extraparams"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
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
