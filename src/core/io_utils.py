"""
I/O utility functions for file handling and spatial vector/raster persistence.
"""

from pathlib import Path
import json

def ensure_dir(path: Path) -> Path:
    """Ensure directory exists and return Path object."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def save_geojson(data: dict, output_path: Path):
    """Save dictionary content to GeoJSON file."""
    ensure_dir(output_path.parent)
    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
