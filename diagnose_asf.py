import asf_search as asf
from src.satellite.catalog import load_aoi

aoi = load_aoi().to_crs("EPSG:4326")
wkt = aoi.geometry.union_all().convex_hull.wkt

results = asf.geo_search(
    platform=[asf.PLATFORM.SENTINEL1],
    processingLevel="GRD_HD",
    intersectsWith=wkt,
    start="2023-11-01T00:00:00Z",
    end="2024-06-30T23:59:59Z",
    maxResults=500,
)

seen = set()

for product in sorted(
    results,
    key=lambda p: p.properties.get("startTime", "")
):
    p = product.properties

    key = (
        str(p.get("startTime", ""))[:10],
        p.get("flightDirection"),
        p.get("pathNumber"),
    )

    if key in seen:
        continue

    seen.add(key)

    print(
        f"Date: {key[0]} | "
        f"Direction: {key[1]} | "
        f"Orbit: {key[2]}"
    )