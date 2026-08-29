# Download AOI, rainfall, roads, buildings, and drainage data
"""
download_data.py

Downloads beginner-friendly supporting datasets for the Chennai Flood MVP.

This script creates:
- Chennai AOI GeoJSON
- Road network GeoJSON
- Building footprints GeoJSON
- Drainage / waterway GeoJSON
- Sample rainfall CSV

Satellite data will be added later.
"""

import json
from pathlib import Path

import pandas as pd
import osmnx as ox

from src.core.config import (
    AOI_FILE,
    BUILDINGS_FILE,
    BUILDING_TAGS,
    CITY_NAME,
    COUNTRY,
    CRS_WGS84,
    DRAINAGE_FILE,
    DRAINAGE_TAGS,
    RAINFALL_FILE,
    RAW_DIR,
    ROADS_FILE,
    VALID_BUILDING_GEOMETRIES,
    VALID_DRAINAGE_GEOMETRIES,
    VALID_ROAD_GEOMETRIES,
)

from src.core.logger import get_logger
from src.core.validation import (
    validate_dataframe,
    validate_geodataframe,
)

logger = get_logger(__name__)

from src.core.metadata import generate_metadata_files

PLACE_NAME = f"{CITY_NAME}, {COUNTRY}"


def ensure_directories() -> None:
    """Create required folders if they do not already exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Raw data directory ready: %s", RAW_DIR)


def save_empty_geojson(path: Path):
    """Save an empty GeoJSON file if a layer cannot be downloaded."""
    empty_geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    path.write_text(json.dumps(empty_geojson, indent=2), encoding="utf-8")


def download_aoi() -> None:
    """Download the Chennai boundary from OpenStreetMap/Nominatim."""
    logger.info("Downloading AOI for %s", PLACE_NAME)

    aoi = ox.geocode_to_gdf(PLACE_NAME)
    aoi = aoi.to_crs(CRS_WGS84)

    validate_geodataframe(
        aoi,
        dataset_name="Chennai AOI",
        expected_crs=CRS_WGS84,
        allowed_geometry_types={"Polygon", "MultiPolygon"},
    )

    aoi.to_file(AOI_FILE, driver="GeoJSON")

    logger.info(
        "AOI saved successfully: %s | Features: %s",
        AOI_FILE,
        len(aoi),
    )

def download_roads() -> None:
    """Download the road network from OpenStreetMap."""
    logger.info("Downloading road network for %s", PLACE_NAME)

    graph = ox.graph_from_place(
        PLACE_NAME,
        network_type="drive",
        simplify=True,
    )

    _, edges = ox.graph_to_gdfs(graph)

    roads = edges.reset_index()
    roads = roads.to_crs(CRS_WGS84)

    useful_columns = [
        "osmid",
        "name",
        "highway",
        "oneway",
        "length",
        "geometry",
    ]

    roads = roads[
        [column for column in useful_columns if column in roads.columns]
    ]

    validate_geodataframe(
        roads,
        dataset_name="Chennai roads",
        expected_crs=CRS_WGS84,
        required_columns={"geometry"},
        allowed_geometry_types=VALID_ROAD_GEOMETRIES,
    )

    roads.to_file(ROADS_FILE, driver="GeoJSON")

    logger.info(
        "Road network saved successfully: %s | Segments: %s",
        ROADS_FILE,
        len(roads),
    )

def download_buildings() -> None:
    """Download building footprints from OpenStreetMap."""
    logger.info("Downloading building footprints for %s", PLACE_NAME)

    try:

        buildings = ox.features_from_place(
            PLACE_NAME,
            BUILDING_TAGS,
        )

        buildings = buildings.reset_index()
        buildings = buildings.to_crs(CRS_WGS84)

        buildings = buildings[
            buildings.geometry.geom_type.isin(
                ["Polygon", "MultiPolygon"]
            )
        ]

        useful_columns = [
            "osmid",
            "building",
            "name",
            "geometry",
        ]

        buildings = buildings[
            [
                column
                for column in useful_columns
                if column in buildings.columns
            ]
        ]
        validate_geodataframe(
            buildings,
            dataset_name="Chennai buildings",
            expected_crs=CRS_WGS84,
            required_columns={"geometry"},
            allowed_geometry_types=VALID_BUILDING_GEOMETRIES,
        )
        buildings.to_file(
            BUILDINGS_FILE,
            driver="GeoJSON",
        )

        logger.info(
            "Buildings saved successfully: %s | Features: %s",
            BUILDINGS_FILE,
            len(buildings),
        )

    except Exception:
        logger.exception(
            "Building download failed. An empty GeoJSON will be created."
        )

        save_empty_geojson(BUILDINGS_FILE)

        logger.warning(
            "Empty buildings file saved: %s",
            BUILDINGS_FILE,
        )


def download_drainage() -> None:
    """
    Download simple drainage-related OSM features.

    This includes:
    - drains
    - canals
    - streams

    This is a proxy layer and not a complete engineering drainage network.
    """
    logger.info("Downloading drainage features for %s", PLACE_NAME)

    try:
        drainage = ox.features_from_place(
            PLACE_NAME,
            DRAINAGE_TAGS,
        )

        drainage = drainage.reset_index()
        drainage = drainage.to_crs(CRS_WGS84)

        drainage = drainage[
            drainage.geometry.geom_type.isin(
                ["LineString", "MultiLineString"]
            )
        ]

        useful_columns = [
            "osmid",
            "waterway",
            "name",
            "geometry",
        ]

        drainage = drainage[
            [
                column
                for column in useful_columns
                if column in drainage.columns
            ]
        ]
        validate_geodataframe(
            drainage,
            dataset_name="Chennai drainage",
            expected_crs=CRS_WGS84,
            required_columns={"geometry"},
            allowed_geometry_types=VALID_DRAINAGE_GEOMETRIES,
        )
        drainage.to_file(
            DRAINAGE_FILE,
            driver="GeoJSON",
        )

        logger.info(
            "Drainage data saved successfully: %s | Features: %s",
            DRAINAGE_FILE,
            len(drainage),
        )

    except Exception:
        logger.exception(
            "Drainage download failed. An empty GeoJSON will be created."
        )

        save_empty_geojson(DRAINAGE_FILE)

        logger.warning(
            "Empty drainage file saved: %s",
            DRAINAGE_FILE,
        )


def create_sample_rainfall() -> None:
    """Create a sample rainfall CSV for initial pipeline testing."""
    logger.info("Creating sample rainfall dataset")

    rainfall = pd.DataFrame(
        {
            "date": [
                "2023-12-01",
                "2023-12-02",
                "2023-12-03",
                "2023-12-04",
                "2023-12-05",
            ],
            "rainfall_mm_24h": [
                20,
                65,
                110,
                180,
                95,
            ],
            "source": [
                "sample",
                "sample",
                "sample",
                "sample",
                "sample",
            ],
        }
    )
    validate_dataframe(
    rainfall,
    dataset_name="Sample rainfall",
    required_columns={
        "date",
        "rainfall_mm_24h",
        "source",
        },
    )
    rainfall.to_csv(
        RAINFALL_FILE,
        index=False,
    )

    logger.info(
        "Rainfall CSV saved successfully: %s | Records: %s",
        RAINFALL_FILE,
        len(rainfall),
    )


def main() -> None:
    """Run the complete base-data download workflow."""
    logger.info("Starting Chennai base-data download pipeline")
    logger.info("Data directory: %s", RAW_DIR)

    try:
        ensure_directories()
        download_aoi()
        download_roads()
        download_buildings()
        download_drainage()
        create_sample_rainfall()
        generate_metadata_files()
    except KeyboardInterrupt:
        logger.warning("Pipeline stopped by the user")
        raise

    except Exception:
        logger.exception("Base-data download pipeline failed")
        raise

    logger.info("Base-data download pipeline completed successfully")


if __name__ == "__main__":
    main()
