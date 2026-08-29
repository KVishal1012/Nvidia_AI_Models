import geopandas as gpd
import pandas as pd

from src.core.config import (
    AOI_FILE,
    BUILDINGS_FILE,
    DRAINAGE_FILE,
    RAINFALL_FILE,
    ROADS_FILE,
)


def test_aoi_file_exists():
    assert AOI_FILE.exists()


def test_roads_file_exists():
    assert ROADS_FILE.exists()


def test_buildings_file_exists():
    assert BUILDINGS_FILE.exists()


def test_drainage_file_exists():
    assert DRAINAGE_FILE.exists()


def test_rainfall_file_exists():
    assert RAINFALL_FILE.exists()


def test_aoi_can_be_read():
    aoi = gpd.read_file(AOI_FILE)

    assert not aoi.empty
    assert aoi.geometry.name in aoi.columns


def test_roads_can_be_read():
    roads = gpd.read_file(ROADS_FILE)

    assert not roads.empty
    assert roads.geometry.name in roads.columns


def test_buildings_can_be_read():
    buildings = gpd.read_file(BUILDINGS_FILE)

    assert buildings.geometry.name in buildings.columns


def test_drainage_can_be_read():
    drainage = gpd.read_file(DRAINAGE_FILE)

    assert drainage.geometry.name in drainage.columns


def test_rainfall_can_be_read():
    rainfall = pd.read_csv(RAINFALL_FILE)

    assert not rainfall.empty