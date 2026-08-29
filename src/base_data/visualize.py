"""
visualize.py

Creates an interactive Folium map for Chennai base datasets.

Layers:
- AOI boundary
- Road network
- Buildings
- Drainage features

Map tools:
- Layer control
- Fullscreen mode
- MiniMap
- Mouse coordinates
- Measurement tool
- Scale bar
- Automatic zoom to AOI
"""

from __future__ import annotations

import geopandas as gpd
import folium
from folium.plugins import (
    Fullscreen,
    MeasureControl,
    MiniMap,
    MousePosition,
)
import json
from typing import Any
import numpy as np 
import pandas as pd 

from src.core.config import (
    AOI_FILE,
    BASE_DATA_MAP_FILE,
    BUILDINGS_FILE,
    CRS_WGS84,
    DRAINAGE_FILE,
    ROADS_FILE,
)
from src.core.logger import get_logger
from src.core.validation import validate_geodataframe


logger = get_logger(__name__)

def make_json_safe(value:Any) -> Any:
    """
    Convert NumPy , Pandas and container values into JSON-safe values.
    """
    if value is None:
        return None
    if isinstance(value,np.ndarray):
        return [make_json_safe(item) for item in value.tolist()]
    if isinstance(value,np.generic):
        return value.item()
    if isinstance(value,pd.Timestamp):
        return value.isoformat()
    if isinstance(value,dict):
        return {
            str(key):make_json_safe(item)
            for key,item in value.items()
        }
    if isinstance(value,(list,tuple,set)):
        return [make_json_safe(item) for item in value]
    try:
        if pd.isna(value):
            return None
    except (TypeError,ValueError):
        pass
    if isinstance(value,(str,int,float,bool)):
        return value

    return str(value)

def prepare_geojson(
    geodataframe: gpd.GeoDataFrame,
    columns: list[str] | None = None,
) -> dict:
    """
    Prepare a GeoDataFrame for safe Folium/JSON serializtion.

    Only the requested attribute columns and geometries are retained.
    """
    geometry_column = geodataframe.geometry.name
    
    if columns is None:
        selected_columns = [
            column
            for column in geodataframe.columns
            if column!= geometry_column
        ]
    else:
        selected_columns = [
            column
            for column in columns
            if column in geodataframe.columns
            and column!= geometry_column
        ]   
    cleaned = geodataframe[
        selected_columns + [geometry_column]
    ].copy()

    for column in selected_columns:
        cleaned[column] = cleaned[column].map(make_json_safe)
    return json.loads(cleaned.to_json())
        

def load_geospatial_dataset(
    file_path,
    dataset_name: str,
    allowed_geometry_types: set[str],
    allow_empty: bool = False,
) -> gpd.GeoDataFrame:
    """
    Load and validate a geospatial dataset.

    Parameters
    ----------
    file_path:
        Path to the geospatial file.

    dataset_name:
        Human-readable dataset name.

    allowed_geometry_types:
        Permitted geometry types.

    allow_empty:
        Whether an empty dataset is acceptable.

    Returns
    -------
    geopandas.GeoDataFrame
        Loaded and validated GeoDataFrame.
    """
    if not file_path.exists():
        raise FileNotFoundError(
            f"{dataset_name} file does not exist: {file_path}"
        )

    logger.info(
        "Loading %s from %s",
        dataset_name,
        file_path,
    )

    geodataframe = gpd.read_file(file_path)

    validate_geodataframe(
        geodataframe,
        dataset_name=dataset_name,
        expected_crs=CRS_WGS84,
        allowed_geometry_types=allowed_geometry_types,
        allow_empty_dataset=allow_empty,
    )

    return geodataframe


def get_map_center(
    aoi: gpd.GeoDataFrame,
) -> list[float]:
    """
    Calculate the map center from the AOI.

    Folium expects coordinates in latitude-longitude order.
    """
    min_x, min_y, max_x, max_y = aoi.total_bounds

    center_latitude = (min_y + max_y) / 2
    center_longitude = (min_x + max_x) / 2

    return [
        center_latitude,
        center_longitude,
    ]


def add_aoi_layer(
    map_object: folium.Map,
    aoi: gpd.GeoDataFrame,
) -> None:
    """Add the Chennai AOI boundary layer."""

    tooltip_fields = [
        column
        for column in [
            "display_name",
            "name",
        ]
        if column in aoi.columns
    ]

    tooltip_alias_mapping = {
        "display_name": "Location",
        "name": "Name",
    }

    tooltip = None

    if tooltip_fields:
        tooltip = folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=[
                tooltip_alias_mapping[field]
                for field in tooltip_fields
            ],
            sticky=False,
        )

    folium.GeoJson(
        data=prepare_geojson(
        aoi,
        columns=tooltip_fields,
    ),
        name="Chennai AOI",
        style_function=lambda feature: {
            "color": "#d62728",
            "weight": 3,
            "fillColor": "#d62728",
            "fillOpacity": 0.05,
        },
        tooltip=tooltip,
        show=True,
    ).add_to(map_object)


def add_roads_layer(
    map_object: folium.Map,
    roads: gpd.GeoDataFrame,
) -> None:
    """Add the Chennai road network."""
    if roads.empty:
        logger.warning("Road layer is empty and will not be added")
        return

    tooltip_fields = [
        column
        for column in [
            "name",
            "highway",
            "oneway",
            "length",
        ]
        if column in roads.columns
    ]

    tooltip_aliases = {
        "name": "Road name",
        "highway": "Road type",
        "oneway": "One way",
        "length": "Length (m)",
    }

    folium.GeoJson(
        data=prepare_geojson(
            roads,
            columns=tooltip_fields,
        ),
        name="Roads",
        style_function=lambda feature: {
            "color": "#4c78a8",
            "weight": 1.5,
            "opacity": 0.75,
        },
        highlight_function=lambda feature: {
            "color": "#1f4e79",
            "weight": 4,
            "opacity": 1,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=[
                tooltip_aliases[field]
                for field in tooltip_fields
            ],
            sticky=False,
        )
        if tooltip_fields
        else None,
        show=True,
    ).add_to(map_object)


def add_buildings_layer(
    map_object: folium.Map,
    buildings: gpd.GeoDataFrame,
) -> None:
    """Add the Chennai building footprints."""
    if buildings.empty:
        logger.warning(
            "Building layer is empty and will not be added"
        )
        return

    tooltip_fields = [
        column
        for column in [
            "name",
            "building",
            "osmid",
        ]
        if column in buildings.columns
    ]

    tooltip_aliases = {
        "name": "Building name",
        "building": "Building type",
        "osmid": "OSM ID",
    }

    folium.GeoJson(
        data=prepare_geojson(
            buildings,
            columns=tooltip_fields,
        ),
        name="Buildings",
        style_function=lambda feature: {
            "color": "#7f7f7f",
            "weight": 0.5,
            "fillColor": "#bdbdbd",
            "fillOpacity": 0.45,
        },
        highlight_function=lambda feature: {
            "color": "#333333",
            "weight": 2,
            "fillOpacity": 0.7,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=[
                tooltip_aliases[field]
                for field in tooltip_fields
            ],
            sticky=False,
        )
        if tooltip_fields
        else None,
        show=False,
    ).add_to(map_object)


def add_drainage_layer(
    map_object: folium.Map,
    drainage: gpd.GeoDataFrame,
) -> None:
    """Add drainage, canal, and stream features."""
    if drainage.empty:
        logger.warning(
            "Drainage layer is empty and will not be added"
        )
        return

    tooltip_fields = [
        column
        for column in [
            "name",
            "waterway",
            "osmid",
        ]
        if column in drainage.columns
    ]

    tooltip_aliases = {
        "name": "Waterway name",
        "waterway": "Waterway type",
        "osmid": "OSM ID",
    }

    folium.GeoJson(
        data=prepare_geojson(
            drainage,
            columns=tooltip_fields,
        ),
        name="Drainage",
        style_function=lambda feature: {
            "color": "#17becf",
            "weight": 2.5,
            "opacity": 0.9,
        },
        highlight_function=lambda feature: {
            "color": "#006d77",
            "weight": 5,
            "opacity": 1,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=[
                tooltip_aliases[field]
                for field in tooltip_fields
            ],
            sticky=False,
        )
        if tooltip_fields
        else None,
        show=True,
    ).add_to(map_object)


def add_map_controls(
    map_object: folium.Map,
) -> None:
    """Add interactive controls to the Folium map."""
    Fullscreen(
        position="topright",
        title="Open fullscreen",
        title_cancel="Exit fullscreen",
        force_separate_button=True,
    ).add_to(map_object)

    MiniMap(
        toggle_display=True,
        position="bottomright",
    ).add_to(map_object)

    MousePosition(
        position="bottomleft",
        separator=" | ",
        prefix="Coordinates:",
        num_digits=5,
        lat_formatter="function(num) {return L.Util.formatNum(num, 5);}",
        lng_formatter="function(num) {return L.Util.formatNum(num, 5);}",
    ).add_to(map_object)

    MeasureControl(
        position="topleft",
        primary_length_unit="meters",
        secondary_length_unit="kilometers",
        primary_area_unit="sqmeters",
        secondary_area_unit="hectares",
    ).add_to(map_object)

    folium.LayerControl(
        position="topright",
        collapsed=False,
    ).add_to(map_object)


def fit_map_to_aoi(
    map_object: folium.Map,
    aoi: gpd.GeoDataFrame,
) -> None:
    """Adjust the map extent to the AOI bounds."""
    min_x, min_y, max_x, max_y = aoi.total_bounds

    map_object.fit_bounds(
        [
            [min_y, min_x],
            [max_y, max_x],
        ]
    )


def create_base_data_map() -> folium.Map:
    """Create the complete Chennai base-data map."""
    logger.info("Starting base-data visualization")

    aoi = load_geospatial_dataset(
        AOI_FILE,
        dataset_name="Chennai AOI",
        allowed_geometry_types={
            "Polygon",
            "MultiPolygon",
        },
    )

    roads = load_geospatial_dataset(
        ROADS_FILE,
        dataset_name="Chennai roads",
        allowed_geometry_types={
            "LineString",
            "MultiLineString",
        },
    )

    buildings = load_geospatial_dataset(
        BUILDINGS_FILE,
        dataset_name="Chennai buildings",
        allowed_geometry_types={
            "Polygon",
            "MultiPolygon",
        },
        allow_empty=True,
    )

    drainage = load_geospatial_dataset(
        DRAINAGE_FILE,
        dataset_name="Chennai drainage",
        allowed_geometry_types={
            "LineString",
            "MultiLineString",
        },
        allow_empty=True,
    )

    map_center = get_map_center(aoi)

    map_object = folium.Map(
        location=map_center,
        zoom_start=11,
        tiles=None,
        control_scale=True,
        prefer_canvas=True,
    )

    folium.TileLayer(
        tiles="OpenStreetMap",
        name="OpenStreetMap",
        control=True,
        show=True,
    ).add_to(map_object)

    folium.TileLayer(
        tiles="CartoDB positron",
        name="Light basemap",
        control=True,
        show=False,
    ).add_to(map_object)

    folium.TileLayer(
        tiles="CartoDB dark_matter",
        name="Dark basemap",
        control=True,
        show=False,
    ).add_to(map_object)

    add_aoi_layer(
        map_object,
        aoi,
    )

    add_roads_layer(
        map_object,
        roads,
    )

    add_buildings_layer(
        map_object,
        buildings,
    )

    add_drainage_layer(
        map_object,
        drainage,
    )

    add_map_controls(map_object)
    fit_map_to_aoi(map_object, aoi)

    logger.info("Base-data visualization created successfully")

    return map_object


def save_base_data_map(
    map_object: folium.Map,
) -> None:
    """Save the Folium map as an HTML file."""
    BASE_DATA_MAP_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    map_object.save(
        str(BASE_DATA_MAP_FILE)
    )

    logger.info(
        "Base-data map saved: %s",
        BASE_DATA_MAP_FILE,
    )


def main() -> None:
    """Generate and save the base-data map."""
    try:
        map_object = create_base_data_map()
        save_base_data_map(map_object)

    except KeyboardInterrupt:
        logger.warning(
            "Visualization generation stopped by the user"
        )
        raise

    except Exception:
        logger.exception(
            "Base-data visualization failed"
        )
        raise

    logger.info(
        "Base-data visualization pipeline completed"
    )


if __name__ == "__main__":
    main()