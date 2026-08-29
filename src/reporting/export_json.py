# Export final flood risk output as JSON/GeoJSON

def export_flood_summary_json(summary_data: dict, output_path: str):
    """Export flood risk assessment summary to JSON."""
    import json

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    print(f"Saved flood summary JSON to: {output_path}")
