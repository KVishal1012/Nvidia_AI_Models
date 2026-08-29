"""
Dataset metadata extraction and cataloging functions.
"""

from pathlib import Path

def extract_layer_metadata(file_path: Path) -> dict:
    """Extract metadata for vector or raster layer."""
    path = Path(file_path)
    return {
        "filename": path.name,
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }
