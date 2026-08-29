"""
Preprocess Sentinel-2 optical multispectral imagery.
"""

def preprocess_sentinel2_optical(input_raster_path: str):
    """Preprocess Sentinel-2 optical imagery (cloud masking, band resample)."""
    print(f"Preprocessing Sentinel-2 optical data from: {input_raster_path}")
