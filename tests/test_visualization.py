import folium

from src.base_data.visualize import (
    create_base_data_map,
    save_base_data_map,
)
from src.core.config import BASE_DATA_MAP_FILE


def test_create_base_data_map():
    map_object = create_base_data_map()

    assert isinstance(map_object, folium.Map)


def test_save_base_data_map():
    map_object = create_base_data_map()

    save_base_data_map(map_object)

    assert BASE_DATA_MAP_FILE.exists()
    assert BASE_DATA_MAP_FILE.stat().st_size > 0