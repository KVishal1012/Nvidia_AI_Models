"""
metadata.py

Generates metadata and summary information for geospatial and tabular datasets.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

from src.core.config import (
    AOI_FILE,
    BUILDINGS_FILE,
    CITY_NAME,
    DATA_OUTPUTS_DIR,
    DATA_SUMMARY_FILE,
    DRAINAGE_FILE,
    METADATA_FILE,
    RAINFALL_FILE,
    ROADS_FILE,
)
from src.core.logger import get_logger


logger = get_logger(__name__)


def get_file_size_mb(file_path: Path) -> float:
    """Return the file size in megabytes."""
    if not file_path.exists():
        return 0.0

    return round(file_path.stat().st_size / (1024 * 1024), 3)


def get_modified_time(file_path: Path) -> str | None:
    """Return the file modification time in UTC ISO format."""
    if not file_path.exists():
        return None

    modified_time = datetime.fromtimestamp(
        file_path.stat().st_mtime,
        tz=timezone.utc,
    )

    return modified_time.isoformat()


def generate_geospatial_metadata(
    dataset_name: str,
    file_path: Path,
) -> dict[str, Any]:
    """Generate metadata for a geospatial dataset."""
    if not file_path.exists():
        logger.warning(
            "%s file does not exist: %s",
            dataset_name,
            file_path,
        )

        return {
            "dataset": dataset_name,
            "path": str(file_path),
            "exists": False,
        }

    geodataframe = gpd.read_file(file_path)

    geometry_types = sorted(
        geodataframe.geometry.dropna().geom_type.unique().tolist()
    )

    bounds = (
        geodataframe.total_bounds.tolist()
        if not geodataframe.empty
        else None
    )

    metadata = {
        "dataset": dataset_name,
        "path": str(file_path),
        "exists": True,
        "feature_count": len(geodataframe),
        "column_count": len(geodataframe.columns),
        "columns": geodataframe.columns.tolist(),
        "crs": (
            geodataframe.crs.to_string()
            if geodataframe.crs is not None
            else None
        ),
        "geometry_types": geometry_types,
        "bounding_box": bounds,
        "null_geometry_count": int(
            geodataframe.geometry.isna().sum()
        ),
        "empty_geometry_count": int(
            geodataframe.geometry.dropna().is_empty.sum()
        ),
        "invalid_geometry_count": int(
            (~geodataframe.geometry.dropna().is_valid).sum()
        ),
        "file_size_mb": get_file_size_mb(file_path),
        "modified_at": get_modified_time(file_path),
    }

    logger.info(
        "Generated metadata for %s | Features: %s",
        dataset_name,
        len(geodataframe),
    )

    return metadata


def generate_tabular_metadata(
    dataset_name: str,
    file_path: Path,
) -> dict[str, Any]:
    """Generate metadata for a CSV dataset."""
    if not file_path.exists():
        logger.warning(
            "%s file does not exist: %s",
            dataset_name,
            file_path,
        )

        return {
            "dataset": dataset_name,
            "path": str(file_path),
            "exists": False,
        }

    dataframe = pd.read_csv(file_path)

    metadata = {
        "dataset": dataset_name,
        "path": str(file_path),
        "exists": True,
        "record_count": len(dataframe),
        "column_count": len(dataframe.columns),
        "columns": dataframe.columns.tolist(),
        "null_value_count": int(
            dataframe.isna().sum().sum()
        ),
        "file_size_mb": get_file_size_mb(file_path),
        "modified_at": get_modified_time(file_path),
    }

    logger.info(
        "Generated metadata for %s | Records: %s",
        dataset_name,
        len(dataframe),
    )

    return metadata


def build_dataset_metadata() -> dict[str, Any]:
    """Generate metadata for all base datasets."""
    generated_at = datetime.now(timezone.utc).isoformat()

    metadata = {
        "city": CITY_NAME,
        "generated_at": generated_at,
        "datasets": {
            "aoi": generate_geospatial_metadata(
                "Chennai AOI",
                AOI_FILE,
            ),
            "roads": generate_geospatial_metadata(
                "Chennai roads",
                ROADS_FILE,
            ),
            "buildings": generate_geospatial_metadata(
                "Chennai buildings",
                BUILDINGS_FILE,
            ),
            "drainage": generate_geospatial_metadata(
                "Chennai drainage",
                DRAINAGE_FILE,
            ),
            "rainfall": generate_tabular_metadata(
                "Chennai rainfall",
                RAINFALL_FILE,
            ),
        },
    }

    return metadata


def build_data_summary(
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Create a lightweight summary from the full metadata."""
    datasets = metadata["datasets"]

    summary = {
        "city": metadata["city"],
        "generated_at": metadata["generated_at"],
        "datasets": {
            "aoi": datasets["aoi"].get("feature_count", 0),
            "roads": datasets["roads"].get("feature_count", 0),
            "buildings": datasets["buildings"].get(
                "feature_count",
                0,
            ),
            "drainage": datasets["drainage"].get(
                "feature_count",
                0,
            ),
            "rainfall": datasets["rainfall"].get(
                "record_count",
                0,
            ),
        },
    }

    return summary


def save_json(
    data: dict[str, Any],
    output_path: Path,
) -> None:
    """Save a dictionary as formatted JSON."""
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False,
        )

    logger.info("JSON file saved: %s", output_path)


def generate_metadata_files() -> tuple[dict[str, Any], dict[str, Any]]:
    """Generate and save metadata and summary files."""
    logger.info("Starting dataset metadata generation")

    DATA_OUTPUTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    metadata = build_dataset_metadata()
    summary = build_data_summary(metadata)

    save_json(metadata, METADATA_FILE)
    save_json(summary, DATA_SUMMARY_FILE)

    logger.info("Dataset metadata generation completed")

    return metadata, summary


def main() -> None:
    """Generate metadata from the command line."""
    metadata, summary = generate_metadata_files()

    logger.info(
        "Metadata generated for %s datasets",
        len(metadata["datasets"]),
    )

    logger.info(
        "Data summary: %s",
        summary["datasets"],
    )


if __name__ == "__main__":
    main()