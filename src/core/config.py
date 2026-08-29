"""
config.py

Central configuration for the Chennai Flood GeoAI project.

Storage strategy:
- Source code stays in the GitHub repository.
- Large datasets stay outside Git.
- On Google Colab, data is stored in mounted Google Drive.
- On local machines, GEOAI_DATA_ROOT defines the data location.
- If no external path is configured, the project uses a local data folder.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


# ---------------------------------------------------------------------
# Project identity
# ---------------------------------------------------------------------

CITY_NAME = "Chennai"
COUNTRY = "India"
PLACE_NAME = f"{CITY_NAME}, {COUNTRY}"


# ---------------------------------------------------------------------
# Coordinate reference systems
# ---------------------------------------------------------------------

# OpenStreetMap, GeoJSON, Folium and web-map coordinates.
CRS_WGS84 = "EPSG:4326"

# UTM Zone 44N for Chennai-area distance and area calculations.
CRS_PROJECTED = "EPSG:32644"


# ---------------------------------------------------------------------
# Repository directories
# ---------------------------------------------------------------------

# File location:
# nvidia_geoai_lab/src/core/config.py
#
# parents[0] = core
# parents[1] = src
# parents[2] = nvidia_geoai_lab
PROJECT_ROOT = Path(__file__).resolve().parents[2]

SRC_DIR = PROJECT_ROOT / "src"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
DOCS_DIR = PROJECT_ROOT / "docs"
TESTS_DIR = PROJECT_ROOT / "tests"
ASSETS_DIR = PROJECT_ROOT / "assets"
CONFIGS_DIR = PROJECT_ROOT / "configs"
MODELS_DIR = PROJECT_ROOT / "models"
CACHE_DIR = PROJECT_ROOT / "cache"
LOGS_DIR = PROJECT_ROOT / "logs"


# ---------------------------------------------------------------------
# Runtime detection
# ---------------------------------------------------------------------

def is_colab() -> bool:
    """Return True when the code is running inside Google Colab."""
    return (
        "google.colab" in sys.modules
        or "COLAB_RELEASE_TAG" in os.environ
        or "COLAB_GPU" in os.environ
    )


def get_data_root() -> Path:
    """
    Resolve the project's data directory.

    Priority:
    1. GEOAI_DATA_ROOT environment variable
    2. Mounted Google Drive when running in Colab
    3. Local project data directory as a fallback
    """

    configured_path = os.getenv("GEOAI_DATA_ROOT")

    if configured_path:
        return Path(configured_path).expanduser().resolve()

    if is_colab():
        colab_drive_root = Path("/content/drive/MyDrive")

        if not colab_drive_root.exists():
            raise RuntimeError(
                "Google Drive is not mounted. Run the following in Colab:\n"
                "from google.colab import drive\n"
                "drive.mount('/content/drive')"
            )

        return colab_drive_root / "chennai-flood-mvp" / "data"

    return PROJECT_ROOT / "data"


# ---------------------------------------------------------------------
# Main data directories
# ---------------------------------------------------------------------

DATA_DIR = get_data_root()

RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DATA_OUTPUTS_DIR = DATA_DIR / "outputs"

VECTOR_RAW_DIR = RAW_DIR / "vector"
RASTER_RAW_DIR = RAW_DIR / "raster"
SATELLITE_RAW_DIR = RAW_DIR / "satellite"
RAINFALL_RAW_DIR = RAW_DIR / "rainfall"

VECTOR_PROCESSED_DIR = PROCESSED_DIR / "vector"
RASTER_PROCESSED_DIR = PROCESSED_DIR / "raster"
SATELLITE_PROCESSED_DIR = PROCESSED_DIR / "satellite"
FLOOD_PROCESSED_DIR = PROCESSED_DIR / "flood"
EXPOSURE_PROCESSED_DIR = PROCESSED_DIR / "exposure"


# ---------------------------------------------------------------------
# Base GIS files
# ---------------------------------------------------------------------

AOI_FILE = RAW_DIR / "chennai_aoi.geojson"
ROADS_FILE = RAW_DIR / "chennai_roads.geojson"
BUILDINGS_FILE = RAW_DIR / "chennai_buildings.geojson"
DRAINAGE_FILE = RAW_DIR / "chennai_drainage.geojson"
RAINFALL_FILE = RAW_DIR / "chennai_rainfall.csv"


# ---------------------------------------------------------------------
# Satellite directories and files
# ---------------------------------------------------------------------

SENTINEL1_RAW_DIR = SATELLITE_RAW_DIR / "sentinel1"
SENTINEL2_RAW_DIR = SATELLITE_RAW_DIR / "sentinel2"

SENTINEL1_PROCESSED_DIR = SATELLITE_PROCESSED_DIR / "sentinel1"
SENTINEL2_PROCESSED_DIR = SATELLITE_PROCESSED_DIR / "sentinel2"

SENTINEL1_PRE_EVENT_FILE = (
    SENTINEL1_PROCESSED_DIR / "s1_pre_event.tif"
)

SENTINEL1_EVENT_FILE = (
    SENTINEL1_PROCESSED_DIR / "s1_event.tif"
)

SENTINEL1_CHANGE_FILE = (
    SENTINEL1_PROCESSED_DIR / "s1_change.tif"
)

SENTINEL2_PRE_EVENT_FILE = (
    SENTINEL2_PROCESSED_DIR / "s2_pre_event.tif"
)

SENTINEL2_EVENT_FILE = (
    SENTINEL2_PROCESSED_DIR / "s2_event.tif"
)

NDWI_FILE = SENTINEL2_PROCESSED_DIR / "ndwi.tif"
MNDWI_FILE = SENTINEL2_PROCESSED_DIR / "mndwi.tif"


# ---------------------------------------------------------------------
# Flood and exposure outputs
# ---------------------------------------------------------------------

FLOOD_MASK_FILE = FLOOD_PROCESSED_DIR / "flood_mask.tif"

FLOOD_EXTENT_FILE = (
    FLOOD_PROCESSED_DIR / "flood_extent.geojson"
)

EXPOSED_BUILDINGS_FILE = (
    EXPOSURE_PROCESSED_DIR / "exposed_buildings.geojson"
)

AFFECTED_ROADS_FILE = (
    EXPOSURE_PROCESSED_DIR / "affected_roads.geojson"
)

DRAINAGE_RISK_FILE = (
    EXPOSURE_PROCESSED_DIR / "drainage_risk.geojson"
)


# ---------------------------------------------------------------------
# Reports, metadata and maps
# ---------------------------------------------------------------------

DATA_SUMMARY_FILE = DATA_OUTPUTS_DIR / "data_summary.json"

METADATA_FILE = (
    DATA_OUTPUTS_DIR / "dataset_metadata.json"
)

PIPELINE_SUMMARY_FILE = (
    DATA_OUTPUTS_DIR / "pipeline_summary.json"
)

BASE_DATA_MAP_FILE = (
    DATA_OUTPUTS_DIR / "chennai_base_data_map.html"
)

FLOOD_MAP_FILE = (
    DATA_OUTPUTS_DIR / "chennai_flood_map.html"
)

FINAL_REPORT_FILE = (
    DATA_OUTPUTS_DIR / "chennai_flood_report.json"
)


# ---------------------------------------------------------------------
# OpenStreetMap settings
# ---------------------------------------------------------------------

OSM_NETWORK_TYPE = "drive"

BUILDING_TAGS = {
    "building": True,
}

DRAINAGE_TAGS = {
    "waterway": [
        "drain",
        "canal",
        "stream",
    ]
}

VALID_BUILDING_GEOMETRIES = {
    "Polygon",
    "MultiPolygon",
}

VALID_ROAD_GEOMETRIES = {
    "LineString",
    "MultiLineString",
}

VALID_DRAINAGE_GEOMETRIES = {
    "LineString",
    "MultiLineString",
}


# ---------------------------------------------------------------------
# Initial Chennai flood event dates
# ---------------------------------------------------------------------

PRE_EVENT_START_DATE = "2023-11-15"
PRE_EVENT_END_DATE = "2023-11-30"

EVENT_START_DATE = "2023-12-01"
EVENT_END_DATE = "2023-12-08"

MAX_SENTINEL2_CLOUD_COVER = 40


# ---------------------------------------------------------------------
# Directory management
# ---------------------------------------------------------------------

DIRECTORIES_TO_CREATE = [
    RAW_DIR,
    PROCESSED_DIR,
    DATA_OUTPUTS_DIR,
    VECTOR_RAW_DIR,
    RASTER_RAW_DIR,
    SATELLITE_RAW_DIR,
    RAINFALL_RAW_DIR,
    VECTOR_PROCESSED_DIR,
    RASTER_PROCESSED_DIR,
    SATELLITE_PROCESSED_DIR,
    FLOOD_PROCESSED_DIR,
    EXPOSURE_PROCESSED_DIR,
    SENTINEL1_RAW_DIR,
    SENTINEL2_RAW_DIR,
    SENTINEL1_PROCESSED_DIR,
    SENTINEL2_PROCESSED_DIR,
    CACHE_DIR,
    LOGS_DIR,
]


def create_project_directories() -> None:
    """Create all configured project directories."""
    for directory in DIRECTORIES_TO_CREATE:
        directory.mkdir(parents=True, exist_ok=True)


def print_configuration() -> None:
    """Print the resolved configuration for debugging."""
    runtime = "Google Colab" if is_colab() else "Local"

    print(f"Runtime:       {runtime}")
    print(f"Project root:  {PROJECT_ROOT}")
    print(f"Data root:     {DATA_DIR}")
    print(f"Raw data:      {RAW_DIR}")
    print(f"Processed:     {PROCESSED_DIR}")
    print(f"Data outputs:  {DATA_OUTPUTS_DIR}")
    print(f"Logs:          {LOGS_DIR}")


if __name__ == "__main__":
    create_project_directories()
    print_configuration()