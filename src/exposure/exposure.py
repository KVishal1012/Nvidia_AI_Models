# Building exposure and simple damage assessment

def assess_building_exposure(buildings_gdf, flood_extent_gdf, buffer_m: float = 10.0):
    """Assess building exposure by spatial intersection with flood extent."""
    print(f"Calculating building exposure with {buffer_m}m buffer")
