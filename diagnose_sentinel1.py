from pystac_client import Client

STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"

client = Client.open(STAC_URL)

collection = client.get_collection("sentinel-1-rtc")

print("\nCOLLECTION INFORMATION")
print("ID:", collection.id)
print("Extent:", collection.extent.to_dict())

tests = [
    ("Chennai bbox, flood period",
     [80.0, 12.7, 80.5, 13.4],
     "2023-12-01/2024-01-15"),

    ("Chennai bbox, wider period",
     [80.0, 12.7, 80.5, 13.4],
     "2023-01-01/2024-12-31"),

    ("Larger regional bbox, flood period",
     [79.0, 12.0, 81.0, 14.0],
     "2023-12-01/2024-01-15"),
]

for name, bbox, dates in tests:
    print(f"\n{name}")

    search = client.search(
        collections=["sentinel-1-rtc"],
        bbox=bbox,
        datetime=dates,
        max_items=20,
    )

    items = list(search.items())

    print("Candidates:", len(items))

    for item in items[:5]:
        print(
            item.id,
            item.datetime,
            item.properties.get("sat:orbit_state"),
            item.properties.get("sat:relative_orbit"),
        )