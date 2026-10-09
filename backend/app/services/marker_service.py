from pathlib import Path
from typing import Set


class MarkerService:
    """Service for loading and managing marker lists"""
    
    @staticmethod
    def load_markers_from_file(file_path: Path) -> Set[str]:
        """Load marker IDs from text file"""
        if not file_path.exists():
            raise FileNotFoundError(f"Marker file not found: {file_path}")
        
        markers = set()
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    markers.add(line)
        
        return markers
    
    @staticmethod
    def verify_markers(file_markers: Set[str], required_markers: Set[str]) -> tuple[bool, list[str]]:
        """
        Verify if all required markers are present in the file.
        Returns: (is_complete, missing_markers)
        """
        missing = [m for m in required_markers if m not in file_markers]
        return (len(missing) == 0, missing)
