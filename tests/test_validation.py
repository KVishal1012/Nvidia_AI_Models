import geopandas as gpd
import pandas as pd

from src.core.config import (
    AOI_FILE,
    BUILDINGS_FILE,
    CRS_WGS84,
    DRAINAGE_FILE,
    RAINFALL_FILE,
    ROADS_FILE,
    VALID_BUILDING_GEOMETRIES,
    VALID_DRAINAGE_GEOMETRIES,
    VALID_ROAD_GEOMETRIES,
)
from src.core.validation import (
    validate_dataframe,
    validate_geodataframe,
)

datasets = [
    ("AOI", AOI_FILE, {"Polygon", "MultiPolygon"}, False),
    ("Roads", ROADS_FILE, VALID_ROAD_GEOMETRIES, False),
    ("Buildings", BUILDINGS_FILE, VALID_BUILDING_GEOMETRIES, True),
    ("Drainage", DRAINAGE_FILE, VALID_DRAINAGE_GEOMETRIES, True),
]

for name, path, geometry_types, allow_empty in datasets:
    gdf = gpd.read_file(path)

    summary = validate_geodataframe(
        gdf,
        dataset_name=name,
        expected_crs=CRS_WGS84,
        allowed_geometry_types=geometry_types,
        allow_empty_dataset=allow_empty,
    )

    print(summary)

rainfall = pd.read_csv(RAINFALL_FILE)

print(
    validate_dataframe(
        rainfall,
        dataset_name="Rainfall",
        required_columns={
            "date",
            "rainfall_mm_24h",
            "source",
        },
    )
)
