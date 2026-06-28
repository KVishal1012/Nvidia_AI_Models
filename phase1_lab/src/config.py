# Project configuration
from pathlib import Path

project_root = Path("/content/drive/MyDrive/chennai-flood-mvp")

config_code = '''
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Data folders
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = DATA_DIR / "outputs"

# Area of interest
CITY_NAME = "Chennai"
COUNTRY = "India"
CRS_WGS84 = "EPSG:4326"
CRS_PROJECTED = "EPSG:32644"  # UTM Zone 44N, useful for Chennai distance/area calculations

# File paths
AOI_FILE = RAW_DIR / "chennai_aoi.geojson"
ROADS_FILE = RAW_DIR / "chennai_roads.geojson"
BUILDINGS_FILE = RAW_DIR / "chennai_buildings.geojson"
DRAINAGE_FILE = RAW_DIR / "chennai_drainage.geojson"
RAINFALL_FILE = RAW_DIR / "chennai_rainfall.csv"

FLOOD_MASK_FILE = PROCESSED_DIR / "flood_mask.tif"
FLOOD_EXTENT_FILE = PROCESSED_DIR / "flood_extent.geojson"
FLOODED_ROADS_FILE = PROCESSED_DIR / "flooded_roads.geojson"
EXPOSED_BUILDINGS_FILE = PROCESSED_DIR / "exposed_buildings.geojson"
DRAINAGE_RISK_FILE = PROCESSED_DIR / "drainage_risk.geojson"

FINAL_JSON_FILE = OUTPUT_DIR / "flood_risk_summary.json"
FINAL_GEOJSON_FILE = OUTPUT_DIR / "flood_risk_features.geojson"

# Simple thresholds for MVP
SAR_WATER_THRESHOLD_DB = -17
RAINFALL_HIGH_RISK_MM_24H = 150
RAINFALL_MEDIUM_RISK_MM_24H = 80
BUILDING_EXPOSURE_BUFFER_M = 10
ROAD_FLOOD_BUFFER_M = 5
'''

config_path = project_root / "src/config.py"
config_path.write_text(config_code, encoding="utf-8")

print(f"Updated: {config_path}")