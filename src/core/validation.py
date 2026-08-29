"""
validation.py

Reusable validation helpers for GeoDataFrames and tabular datasets.

The validation functions check:
- dataset type
- emptiness
- CRS
- required columns
- geometry column
- null and empty geometries
- invalid geometries
- permitted geometry types
"""

from __future__ import annotations

from collections.abc import Iterable

import geopandas as gpd
import pandas as pd

from src.core.logger import get_logger


logger = get_logger(__name__)


class DataValidationError(ValueError):
    """Raised when a dataset fails a required validation check."""


def validate_required_columns(
    dataframe: pd.DataFrame,
    required_columns: Iterable[str],
    dataset_name: str = "dataset",
) -> bool:
    """
    Confirm that a DataFrame contains all required columns.

    Parameters
    ----------
    dataframe:
        DataFrame or GeoDataFrame to validate.

    required_columns:
        Column names that must exist.

    dataset_name:
        Human-readable dataset name used in log messages.

    Returns
    -------
    bool
        True when all required columns are present.

    Raises
    ------
    DataValidationError
        If one or more required columns are missing.
    """
    required = set(required_columns)
    existing = set(dataframe.columns)

    missing = sorted(required - existing)

    if missing:
        raise DataValidationError(
            f"{dataset_name} is missing required columns: {missing}"
        )

    logger.info(
        "%s contains all required columns: %s",
        dataset_name,
        sorted(required),
    )

    return True


def validate_crs(
    geodataframe: gpd.GeoDataFrame,
    expected_crs: str | None = None,
    dataset_name: str = "dataset",
) -> bool:
    """
    Confirm that a GeoDataFrame has a CRS.

    When expected_crs is provided, the function also verifies that the
    GeoDataFrame uses the expected CRS.
    """
    if geodataframe.crs is None:
        raise DataValidationError(
            f"{dataset_name} does not have a coordinate reference system."
        )

    if expected_crs is not None:
        actual_crs = geodataframe.crs.to_string()

        if actual_crs.lower() != expected_crs.lower():
            raise DataValidationError(
                f"{dataset_name} has CRS {actual_crs}, "
                f"but expected {expected_crs}."
            )

    logger.info(
        "%s CRS validation passed: %s",
        dataset_name,
        geodataframe.crs,
    )

    return True


def validate_geometry_column(
    geodataframe: gpd.GeoDataFrame,
    dataset_name: str = "dataset",
) -> bool:
    """Confirm that the GeoDataFrame has an active geometry column."""
    try:
        geometry_name = geodataframe.geometry.name
    except (AttributeError, ValueError) as exc:
        raise DataValidationError(
            f"{dataset_name} does not have an active geometry column."
        ) from exc

    if geometry_name not in geodataframe.columns:
        raise DataValidationError(
            f"{dataset_name} geometry column '{geometry_name}' is missing."
        )

    logger.info(
        "%s geometry column validation passed: %s",
        dataset_name,
        geometry_name,
    )

    return True


def validate_geometry_types(
    geodataframe: gpd.GeoDataFrame,
    allowed_geometry_types: Iterable[str],
    dataset_name: str = "dataset",
) -> bool:
    """
    Confirm that all non-null geometries use permitted geometry types.
    """
    allowed = set(allowed_geometry_types)

    actual = set(
        geodataframe.loc[
            geodataframe.geometry.notna(),
            geodataframe.geometry.name,
        ].geom_type.dropna()
    )

    unsupported = sorted(actual - allowed)

    if unsupported:
        raise DataValidationError(
            f"{dataset_name} contains unsupported geometry types: "
            f"{unsupported}. Allowed types: {sorted(allowed)}"
        )

    logger.info(
        "%s geometry type validation passed: %s",
        dataset_name,
        sorted(actual),
    )

    return True


def validate_geodataframe(
    geodataframe: gpd.GeoDataFrame,
    dataset_name: str = "dataset",
    expected_crs: str | None = None,
    required_columns: Iterable[str] | None = None,
    allowed_geometry_types: Iterable[str] | None = None,
    allow_empty_dataset: bool = False,
    allow_null_geometries: bool = False,
    allow_empty_geometries: bool = False,
    allow_invalid_geometries: bool = False,
) -> dict[str, int | str | list[str]]:
    """
    Run a complete validation on a GeoDataFrame.

    Parameters
    ----------
    geodataframe:
        GeoDataFrame to validate.

    dataset_name:
        Name used in logs and error messages.

    expected_crs:
        Expected CRS, such as ``EPSG:4326``.

    required_columns:
        Columns that must exist.

    allowed_geometry_types:
        Permitted geometry types.

    allow_empty_dataset:
        Whether zero-row GeoDataFrames are permitted.

    allow_null_geometries:
        Whether null geometries are permitted.

    allow_empty_geometries:
        Whether empty Shapely geometries are permitted.

    allow_invalid_geometries:
        Whether invalid geometries are permitted.

    Returns
    -------
    dict
        Validation summary.
    """
    if not isinstance(geodataframe, gpd.GeoDataFrame):
        raise DataValidationError(
            f"{dataset_name} must be a GeoDataFrame, "
            f"not {type(geodataframe).__name__}."
        )

    if geodataframe.empty and not allow_empty_dataset:
        raise DataValidationError(
            f"{dataset_name} contains no features."
        )

    validate_geometry_column(
        geodataframe,
        dataset_name=dataset_name,
    )

    validate_crs(
        geodataframe,
        expected_crs=expected_crs,
        dataset_name=dataset_name,
    )

    if required_columns:
        validate_required_columns(
            geodataframe,
            required_columns=required_columns,
            dataset_name=dataset_name,
        )

    if allowed_geometry_types:
        validate_geometry_types(
            geodataframe,
            allowed_geometry_types=allowed_geometry_types,
            dataset_name=dataset_name,
        )

    null_geometry_count = int(geodataframe.geometry.isna().sum())

    if null_geometry_count > 0 and not allow_null_geometries:
        raise DataValidationError(
            f"{dataset_name} contains "
            f"{null_geometry_count} null geometries."
        )

    non_null_geometry = geodataframe.geometry.dropna()

    empty_geometry_count = int(non_null_geometry.is_empty.sum())

    if empty_geometry_count > 0 and not allow_empty_geometries:
        raise DataValidationError(
            f"{dataset_name} contains "
            f"{empty_geometry_count} empty geometries."
        )

    invalid_geometry_count = int((~non_null_geometry.is_valid).sum())

    if invalid_geometry_count > 0 and not allow_invalid_geometries:
        raise DataValidationError(
            f"{dataset_name} contains "
            f"{invalid_geometry_count} invalid geometries."
        )

    geometry_types = sorted(
        geodataframe.geometry.dropna().geom_type.unique().tolist()
    )

    summary: dict[str, int | str | list[str]] = {
        "dataset": dataset_name,
        "feature_count": len(geodataframe),
        "crs": geodataframe.crs.to_string(),
        "geometry_types": geometry_types,
        "null_geometry_count": null_geometry_count,
        "empty_geometry_count": empty_geometry_count,
        "invalid_geometry_count": invalid_geometry_count,
    }

    logger.info(
        "%s validation passed | Features: %s | "
        "Null: %s | Empty: %s | Invalid: %s",
        dataset_name,
        len(geodataframe),
        null_geometry_count,
        empty_geometry_count,
        invalid_geometry_count,
    )

    return summary


def validate_dataframe(
    dataframe: pd.DataFrame,
    dataset_name: str = "dataset",
    required_columns: Iterable[str] | None = None,
    allow_empty_dataset: bool = False,
) -> dict[str, int | str]:
    """
    Validate a standard Pandas DataFrame.
    """
    if not isinstance(dataframe, pd.DataFrame):
        raise DataValidationError(
            f"{dataset_name} must be a DataFrame, "
            f"not {type(dataframe).__name__}."
        )

    if dataframe.empty and not allow_empty_dataset:
        raise DataValidationError(
            f"{dataset_name} contains no records."
        )

    if required_columns:
        validate_required_columns(
            dataframe,
            required_columns=required_columns,
            dataset_name=dataset_name,
        )

    summary: dict[str, int | str] = {
        "dataset": dataset_name,
        "record_count": len(dataframe),
        "column_count": len(dataframe.columns),
    }

    logger.info(
        "%s tabular validation passed | Records: %s | Columns: %s",
        dataset_name,
        len(dataframe),
        len(dataframe.columns),
    )

    return summary