"""
base_data_report.py

Creates a Markdown report summarizing the Chennai base-data pipeline.
"""



from __future__ import annotations

import json
from datetime import datetime, timezone

from src.core.config import (
    DATA_OUTPUTS_DIR,
    DATA_SUMMARY_FILE,
    METADATA_FILE
)
from src.core.logger import get_logger


logger = get_logger(__name__)


BASE_DATA_REPORT_FILE = DATA_OUTPUTS_DIR / "base_data_report.md"

def load_json(path):

    """Load JSON from disk."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)

def build_report() -> str:
    """Build the complete Markdown report as a string."""
    metadata = load_json(METADATA_FILE)
    summary = load_json(DATA_SUMMARY_FILE)

    generated_at = datetime.now(timezone.utc).isoformat()

    lines = [
        "# Chennai Flood GeoAI — Base Data Report",
        "",
        f"Generated: {generated_at}",
        "",
        "## Overview",
        "",
        f"- City: {summary['city']}",
        f"- AOI features: {summary['datasets']['aoi']}",
        f"- Road segments: {summary['datasets']['roads']}",
        f"- Buildings: {summary['datasets']['buildings']}",
        f"- Drainage features: {summary['datasets']['drainage']}",
        f"- Rainfall records: {summary['datasets']['rainfall']}",
        "",
        "## Dataset Details",
        "",
    ]

    for key, dataset in metadata["datasets"].items():
        lines.extend(
            [
                f"### {dataset['dataset']}",
                "",
                f"- Exists: {dataset.get('exists')}",
                f"- File: `{dataset.get('path')}`",
                f"- File size: {dataset.get('file_size_mb', 0)} MB",
            ]
        )

        if "feature_count" in dataset:
            lines.extend(
                [
                    f"- Feature count: {dataset['feature_count']}",
                    f"- CRS: {dataset.get('crs')}",
                    f"- Geometry types: {dataset.get('geometry_types')}",
                    f"- Null geometries: {dataset.get('null_geometry_count')}",
                    f"- Empty geometries: {dataset.get('empty_geometry_count')}",
                    f"- Invalid geometries: {dataset.get('invalid_geometry_count')}",
                    f"- Bounding box: {dataset.get('bounding_box')}",
                ]
            )

        if "record_count" in dataset:
            lines.extend(
                [
                    f"- Record count: {dataset['record_count']}",
                    f"- Columns: {dataset.get('columns')}",
                    f"- Null values: {dataset.get('null_value_count')}",
                ]
            )

        lines.append("")

    lines.extend(
        [
            "## Pipeline Status",
            "",
            "- Base data download: completed",
            "- Validation: completed",
            "- Metadata generation: completed",
            "- Interactive visualization: completed",
            "",
        ]
    )

    return "\n".join(lines)


def save_report(report: str) -> None:
    """Save the Markdown report."""
    BASE_DATA_REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    BASE_DATA_REPORT_FILE.write_text(
        report,
        encoding="utf-8",
    )

    logger.info(
        "Base-data report saved: %s",
        BASE_DATA_REPORT_FILE,
    )


def main() -> None:
    """Generate the base-data Markdown report."""
    logger.info("Generating base-data report")

    report = build_report()
    save_report(report)

    logger.info("Base-data report generation completed")


if __name__ == "__main__":
    main()