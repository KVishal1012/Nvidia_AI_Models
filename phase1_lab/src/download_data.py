# Download Sentinel, rainfall, roads, buildings, and drainage data
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

import geopandas as gpd
import pandas as pd
import osmnx as ox

from config import (
    CITY_NAME,
    COUNTRY,
    RAW_DIR,
    AOI_FILE,
    ROADS_FILE,
    BUILDINGS_FILE,
    DRAINAGE_FILE,
    RAINFALL_FILE,
    CRS_WGS84,
)


PLACE_NAME = f"{CITY_NAME}, {COUNTRY}"


def ensure_directories():
    """Create required folders if they do not already exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)


def save_empty_geojson(path: Path):
    """Save an empty GeoJSON file if a layer cannot be downloaded."""
    empty_geojson = {
        "type": "FeatureCollection",
        "features": []
    }

    path.write_text(json.dumps(empty_geojson, indent=2), encoding="utf-8")


def download_aoi():
    """Download Chennai boundary from OpenStreetMap/Nominatim."""
    print("Downloading Chennai AOI...")

    aoi = ox.geocode_to_gdf(PLACE_NAME)
    aoi = aoi.to_crs(CRS_WGS84)

    aoi.to_file(AOI_FILE, driver="GeoJSON")

    print(f"Saved AOI: {AOI_FILE}")


def download_roads():
    """Download road network from OpenStreetMap."""
    print("Downloading Chennai road network...")

    graph = ox.graph_from_place(
        PLACE_NAME,
        network_type="drive",
        simplify=True
    )

    nodes, edges = ox.graph_to_gdfs(graph)

    roads = edges.reset_index()
    roads = roads.to_crs(CRS_WGS84)

    useful_columns = [
        "osmid",
        "name",
        "highway",
        "oneway",
        "length",
        "geometry"
    ]

    roads = roads[[col for col in useful_columns if col in roads.columns]]
    roads.to_file(ROADS_FILE, driver="GeoJSON")

    print(f"Saved roads: {ROADS_FILE}")
    print(f"Road segments: {len(roads)}")


def download_buildings():
    """Download building footprints from OpenStreetMap."""
    print("Downloading Chennai building footprints...")

    try:
        tags = {"building": True}
        buildings = ox.features_from_place(PLACE_NAME, tags)

        buildings = buildings.reset_index()
        buildings = buildings.to_crs(CRS_WGS84)

        buildings = buildings[
            buildings.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
        ]

        useful_columns = [
            "osmid",
            "building",
            "name",
            "geometry"
        ]

        buildings = buildings[[col for col in useful_columns if col in buildings.columns]]
        buildings.to_file(BUILDINGS_FILE, driver="GeoJSON")

        print(f"Saved buildings: {BUILDINGS_FILE}")
        print(f"Buildings: {len(buildings)}")

    except Exception as e:
        print("Could not download buildings.")
        print(f"Reason: {e}")
        save_empty_geojson(BUILDINGS_FILE)
        print(f"Saved empty buildings file: {BUILDINGS_FILE}")


def download_drainage():
    """
    Download simple drainage-related OSM features.

    For MVP, this uses OSM waterway features:
    - drain
    - canal
    - stream

    This is a proxy layer, not a full engineering drainage network.
    """
    print("Downloading drainage / waterway features...")

    try:
        tags = {
            "waterway": ["drain", "canal", "stream"]
        }

        drainage = ox.features_from_place(PLACE_NAME, tags)

        drainage = drainage.reset_index()
        drainage = drainage.to_crs(CRS_WGS84)

        drainage = drainage[
            drainage.geometry.geom_type.isin(["LineString", "MultiLineString"])
        ]

        useful_columns = [
            "osmid",
            "waterway",
            "name",
            "geometry"
        ]

        drainage = drainage[[col for col in useful_columns if col in drainage.columns]]
        drainage.to_file(DRAINAGE_FILE, driver="GeoJSON")

        print(f"Saved drainage: {DRAINAGE_FILE}")
        print(f"Drainage features: {len(drainage)}")

    except Exception as e:
        print("Could not download drainage data.")
        print(f"Reason: {e}")
        save_empty_geojson(DRAINAGE_FILE)
        print(f"Saved empty drainage file: {DRAINAGE_FILE}")


def create_sample_rainfall():
    """
    Create a simple sample rainfall CSV.

    Later this can be replaced with real rainfall data from:
    - IMD
    - ERA5
    - local rain gauge data
    """
    print("Creating sample rainfall CSV...")

    rainfall = pd.DataFrame(
        {
            "date": [
                "2023-12-01",
                "2023-12-02",
                "2023-12-03",
                "2023-12-04",
                "2023-12-05"
            ],
            "rainfall_mm_24h": [
                20,
                65,
                110,
                180,
                95
            ],
            "source": [
                "sample",
                "sample",
                "sample",
                "sample",
                "sample"
            ]
        }
    )

    rainfall.to_csv(RAINFALL_FILE, index=False)

    print(f"Saved rainfall CSV: {RAINFALL_FILE}")


def main():
    ensure_directories()

    download_aoi()
    download_roads()
    download_buildings()
    download_drainage()
    create_sample_rainfall()

    print("\nData download step completed.")


if __name__ == "__main__":
    main()