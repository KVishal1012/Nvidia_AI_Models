# Rule-based Sentinel-1 SAR flood mask generation

def generate_flood_mask(sar_raster_path: str, threshold_db: float = -17.0):
    """Generate binary flood mask raster from Sentinel-1 SAR backscatter coefficient."""
    print(f"Generating flood mask using SAR threshold: {threshold_db} dB")
