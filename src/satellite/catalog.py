"""
catalog.py

Reusable STAC catalogue/search utilities for Sentinel imagery.

Responsibilities
----------------
- Connect to STAC APIs.
- Load and validate the project AOI.
- Search imagery using AOI intersection.
- Filter imagery by date.
- Retrieve candidate scenes before applying local filters.
- Apply Sentinel-2 cloud-cover filtering locally.
- Apply Sentinel-1 SAR compatibility filtering locally.
- Normalize STAC Items into a common SatelliteScene model.
- Track the STAC provider that supplied each scene.

Important
---------
This module searches satellite catalogues only.

It does NOT download imagery.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import geopandas as gpd
from pystac import Item
from pystac_client import Client

from src.core.config import AOI_FILE, CRS_WGS84
from src.core.logger import get_logger
from src.core.validation import validate_geodataframe


logger = get_logger(__name__)

# ---------------------------------------------------------------------
# Planetary Computer 
# ---------------------------------------------------------------------

PLANETARY_COMPUTER_STAC_URL = (
    "https://planetarycomputer.microsoft.com/api/stac/v1"
)

PLANETARY_COMPUTER_PROVIDER = "planetary-computer"

PLANETARY_COMPUTER_SENTINEL1_COLLECTION = "sentinel-1-rtc"

# ---------------------------------------------------------------------
# STAC providers
# ---------------------------------------------------------------------

EARTH_SEARCH_STAC_URL = (
    "https://earth-search.aws.element84.com/v1"
)

EARTH_SEARCH_PROVIDER = "earth-search"


# ---------------------------------------------------------------------
# STAC collections
# ---------------------------------------------------------------------

SENTINEL2_COLLECTION = "sentinel-2-c1-l2a"
SENTINEL1_COLLECTION = "sentinel-1-grd"


# ---------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------

DEFAULT_SENTINEL2_CLOUD_COVER = 80.0

DEFAULT_SENTINEL1_ACQUISITION_MODE = "IW"

DEFAULT_SENTINEL1_POLARIZATIONS = (
    "VV",
    "VH",
)


# ---------------------------------------------------------------------
# Normalized scene model
# ---------------------------------------------------------------------

@dataclass
class SatelliteScene:
    """
    Standard metadata representation for a satellite scene.

    The goal of this model is to prevent downstream code from
    depending directly on provider-specific STAC Item structures.
    """

    item_id: str
    collection: str
    provider: str

    datetime: str | None

    cloud_cover: float | None

    bbox: list[float] | None

    platform: str | None
    constellation: str | None

    acquisition_mode: str | None
    polarizations: list[str]

    orbit_state: str | None
    relative_orbit: int | None

    assets: dict[str, str]

    stac_url: str | None

    def to_dict(self) -> dict[str, Any]:
        """
        Convert scene metadata to a JSON-serializable dictionary.
        """
        return asdict(self)


# ---------------------------------------------------------------------
# AOI handling
# ---------------------------------------------------------------------

def load_aoi() -> gpd.GeoDataFrame:
    """
    Load and validate the configured project AOI.

    Returns
    -------
    geopandas.GeoDataFrame
        Validated AOI.
    """
    logger.info(
        "Loading satellite-search AOI: %s",
        AOI_FILE,
    )

    if not AOI_FILE.exists():
        raise FileNotFoundError(
            f"AOI file does not exist: {AOI_FILE}"
        )

    aoi = gpd.read_file(
        AOI_FILE
    )

    validate_geodataframe(
        aoi,
        dataset_name="Satellite search AOI",
        expected_crs=CRS_WGS84,
        allowed_geometry_types={
            "Polygon",
            "MultiPolygon",
        },
    )

    return aoi


def get_aoi_geometry(
    aoi: gpd.GeoDataFrame,
) -> dict[str, Any]:
    """
    Convert the project AOI into a single GeoJSON geometry.

    STAC APIs normally expect intersection geometries in WGS84.

    Parameters
    ----------
    aoi:
        Project AOI.

    Returns
    -------
    dict
        GeoJSON geometry.
    """
    if aoi.crs is None:
        raise ValueError(
            "AOI does not have a CRS."
        )

    if (
        aoi.crs.to_string().lower()
        != CRS_WGS84.lower()
    ):
        logger.info(
            "Reprojecting AOI from %s to %s",
            aoi.crs,
            CRS_WGS84,
        )

        aoi = aoi.to_crs(
            CRS_WGS84
        )

    geometry = aoi.geometry.union_all()

    if geometry.is_empty:
        raise ValueError(
            "AOI geometry is empty."
        )

    return geometry.__geo_interface__


# ---------------------------------------------------------------------
# STAC connection
# ---------------------------------------------------------------------

def open_catalog(
    stac_url: str,
    provider: str,
) -> Client:
    """
    Connect to a STAC API.

    Planetary Computer uses its signing modifier so returned
    asset URLs can be accessed later during download.
    """
    logger.info(
        "Opening STAC catalogue | provider=%s | url=%s",
        provider,
        stac_url,
    )

    if provider == PLANETARY_COMPUTER_PROVIDER:
        import planetary_computer

        catalog = Client.open(
            stac_url,
            modifier=planetary_computer.sign_inplace,
        )

    else:
        catalog = Client.open(
            stac_url
        )

    logger.info(
        "Connected to STAC catalogue | provider=%s | title=%s",
        provider,
        catalog.title or stac_url,
    )

    return catalog


# ---------------------------------------------------------------------
# STAC metadata helpers
# ---------------------------------------------------------------------

def _extract_asset_urls(
    item: Item,
) -> dict[str, str]:
    """
    Return STAC asset names and URLs.
    """
    return {
        asset_name: asset.href
        for asset_name, asset
        in item.assets.items()
        if asset.href
    }


def _get_relative_orbit(
    properties: dict[str, Any],
) -> int | None:
    """
    Extract a relative orbit number from common STAC properties.

    Different STAC catalogues occasionally expose the same
    information using slightly different property names.
    """
    value = (
        properties.get(
            "sat:relative_orbit"
        )
        or properties.get(
            "sat:relative_orbit_number"
        )
        or properties.get(
            "s1:relative_orbit"
        )
    )

    if value is None:
        return None

    try:
        return int(
            value
        )

    except (TypeError, ValueError):
        logger.warning(
            "Unable to convert relative orbit to integer: %s",
            value,
        )

        return None


def _get_acquisition_mode(
    properties: dict[str, Any],
) -> str | None:
    """
    Extract SAR acquisition/instrument mode.
    """
    value = (
        properties.get(
            "sar:instrument_mode"
        )
        or properties.get(
            "s1:instrument_mode"
        )
    )

    if value is None:
        return None

    return str(
        value
    ).upper()


def _get_polarizations(
    properties: dict[str, Any],
) -> list[str]:
    """
    Extract SAR polarizations.
    """
    values = (
        properties.get(
            "sar:polarizations"
        )
        or properties.get(
            "s1:polarizations"
        )
        or []
    )

    if isinstance(
        values,
        str,
    ):
        values = [
            values
        ]

    return [
        str(value).upper()
        for value in values
    ]


# ---------------------------------------------------------------------
# Metadata normalization
# ---------------------------------------------------------------------

def normalize_item(
    item: Item,
    provider: str,
) -> SatelliteScene:
    """
    Convert a provider-specific STAC Item into SatelliteScene.

    Parameters
    ----------
    item:
        PySTAC Item.

    provider:
        Provider from which the item was retrieved.

    Returns
    -------
    SatelliteScene
        Normalized scene metadata.
    """
    properties = item.properties

    # -------------------------------------------------------------
    # Cloud cover
    # -------------------------------------------------------------

    cloud_cover_value = properties.get(
        "eo:cloud_cover"
    )

    cloud_cover: float | None = None

    if cloud_cover_value is not None:
        try:
            cloud_cover = float(
                cloud_cover_value
            )

        except (TypeError, ValueError):
            logger.warning(
                "Invalid cloud-cover value | item=%s | value=%s",
                item.id,
                cloud_cover_value,
            )

    # -------------------------------------------------------------
    # Datetime
    # -------------------------------------------------------------

    datetime_value = (
        item.datetime.isoformat()
        if item.datetime is not None
        else properties.get(
            "datetime"
        )
    )

    # -------------------------------------------------------------
    # SAR metadata
    # -------------------------------------------------------------

    acquisition_mode = (
        _get_acquisition_mode(
            properties
        )
    )

    polarizations = (
        _get_polarizations(
            properties
        )
    )

    # -------------------------------------------------------------
    # Final normalized model
    # -------------------------------------------------------------

    return SatelliteScene(
        item_id=item.id,

        collection=(
            item.collection_id
            or ""
        ),

        provider=provider,

        datetime=datetime_value,

        cloud_cover=cloud_cover,

        bbox=(
            list(item.bbox)
            if item.bbox is not None
            else None
        ),

        platform=properties.get(
            "platform"
        ),

        constellation=properties.get(
            "constellation"
        ),

        acquisition_mode=acquisition_mode,

        polarizations=polarizations,

        orbit_state=properties.get(
            "sat:orbit_state"
        ),

        relative_orbit=(
            _get_relative_orbit(
                properties
            )
        ),

        assets=(
            _extract_asset_urls(
                item
            )
        ),

        stac_url=(
            item.get_self_href()
        ),
    )


# ---------------------------------------------------------------------
# Sentinel-2 local cloud filtering
# ---------------------------------------------------------------------

def filter_by_cloud_cover(
    items: list[Item],
    max_cloud_cover: float,
) -> list[Item]:
    """
    Filter optical STAC Items locally using eo:cloud_cover.

    Candidate scenes are intentionally retrieved from STAC first.
    Filtering locally makes it easy to distinguish:

    - no catalogue coverage
    - scenes rejected because of cloud cover

    Parameters
    ----------
    items:
        Candidate STAC Items.

    max_cloud_cover:
        Maximum allowed cloud-cover percentage.

    Returns
    -------
    list[Item]
        Cloud-filtered scenes.
    """
    if not 0 <= max_cloud_cover <= 100:
        raise ValueError(
            "max_cloud_cover must be between 0 and 100."
        )

    filtered_items: list[Item] = []

    missing_cloud_count = 0

    for item in items:

        cloud_value = item.properties.get(
            "eo:cloud_cover"
        )

        if cloud_value is None:
            missing_cloud_count += 1
            continue

        try:
            cloud_cover = float(
                cloud_value
            )

        except (TypeError, ValueError):
            logger.warning(
                "Skipping item with non-numeric cloud cover | "
                "item=%s | value=%s",
                item.id,
                cloud_value,
            )

            continue

        if cloud_cover <= max_cloud_cover:
            filtered_items.append(
                item
            )

    if missing_cloud_count:
        logger.info(
            "%s candidate items contained no eo:cloud_cover",
            missing_cloud_count,
        )

    logger.info(
        "%s items remain after local cloud-cover filter <= %.1f%%",
        len(filtered_items),
        max_cloud_cover,
    )

    return filtered_items


# ---------------------------------------------------------------------
# Sentinel-1 local compatibility filtering
# ---------------------------------------------------------------------

def filter_sentinel1_items(
    items: list[Item],
    acquisition_mode: str = DEFAULT_SENTINEL1_ACQUISITION_MODE,
    required_polarizations: tuple[str, ...] = (
        DEFAULT_SENTINEL1_POLARIZATIONS
    ),
    orbit_state: str | None = None,
    relative_orbit: int | None = None,
) -> list[Item]:
    """
    Filter Sentinel-1 scenes for flood-analysis compatibility.

    Local filters
    -------------
    - acquisition mode
    - polarization
    - optional orbit direction
    - optional relative orbit

    Parameters
    ----------
    items:
        Candidate Sentinel-1 scenes.

    acquisition_mode:
        SAR instrument mode.

        Default: IW

    required_polarizations:
        Required SAR polarization channels.

        Default: VV + VH

    orbit_state:
        Optional orbit direction.

        Typical values:
        - ascending
        - descending

    relative_orbit:
        Optional relative orbit number.

    Returns
    -------
    list[Item]
        Compatible Sentinel-1 scenes.
    """
    filtered_items: list[Item] = []

    required = {
        polarization.upper()
        for polarization
        in required_polarizations
    }

    for item in items:

        properties = item.properties

        # ---------------------------------------------------------
        # Acquisition mode
        # ---------------------------------------------------------

        item_mode = (
            _get_acquisition_mode(
                properties
            )
        )

        if item_mode is None:
            logger.debug(
                "Skipping Sentinel-1 item without acquisition mode: %s",
                item.id,
            )

            continue

        if (
            item_mode
            != acquisition_mode.upper()
        ):
            continue

        # ---------------------------------------------------------
        # Polarization
        # ---------------------------------------------------------

        item_polarizations = set(
            _get_polarizations(
                properties
            )
        )

        if not required.issubset(
            item_polarizations
        ):
            continue

        # ---------------------------------------------------------
        # Orbit state
        # ---------------------------------------------------------

        item_orbit_state = (
            properties.get(
                "sat:orbit_state"
            )
        )

        if orbit_state is not None:

            if item_orbit_state is None:
                continue

            if (
                str(
                    item_orbit_state
                ).lower()
                != orbit_state.lower()
            ):
                continue

        # ---------------------------------------------------------
        # Relative orbit
        # ---------------------------------------------------------

        item_relative_orbit = (
            _get_relative_orbit(
                properties
            )
        )

        if relative_orbit is not None:

            if (
                item_relative_orbit
                != relative_orbit
            ):
                continue

        filtered_items.append(
            item
        )

    logger.info(
        "%s Sentinel-1 items remain after SAR compatibility filtering",
        len(filtered_items),
    )

    return filtered_items


# ---------------------------------------------------------------------
# Generic STAC candidate search
# ---------------------------------------------------------------------

def search_stac_items(
    collection: str,
    start_date: str,
    end_date: str,
    max_items: int,
    stac_url: str,
    provider: str,
) -> list[Item]:
    """
    Retrieve STAC candidate items using AOI and date only.

    Sensor-specific filtering should be performed after this function.

    Parameters
    ----------
    collection:
        STAC collection ID.

    start_date:
        YYYY-MM-DD.

    end_date:
        YYYY-MM-DD.

    max_items:
        Maximum number of candidate items.

    stac_url:
        STAC API endpoint.

    provider:
        Provider name.

    Returns
    -------
    list[Item]
        Candidate STAC Items.
    """
    if max_items <= 0:
        raise ValueError(
            "max_items must be greater than zero."
        )

    if start_date > end_date:
        raise ValueError(
            "start_date must be earlier than or equal to end_date."
        )

    aoi = load_aoi()

    geometry = get_aoi_geometry(
        aoi
    )

    catalog = open_catalog(
        stac_url=stac_url,
        provider=provider,
    )

    logger.info(
        "Searching STAC | "
        "provider=%s | "
        "collection=%s | "
        "dates=%s/%s | "
        "max_items=%s",
        provider,
        collection,
        start_date,
        end_date,
        max_items,
    )

    search = catalog.search(
        collections=[
            collection
        ],
        intersects=geometry,
        datetime=(
            f"{start_date}/{end_date}"
        ),
        max_items=max_items,
    )

    items = list(
        search.items()
    )

    logger.info(
        "STAC search returned %s candidate items "
        "before local filtering | provider=%s",
        len(items),
        provider,
    )

    return items


# ---------------------------------------------------------------------
# Generic normalized catalogue search
# ---------------------------------------------------------------------

def search_catalog(
    collection: str,
    start_date: str,
    end_date: str,
    max_cloud_cover: float | None = None,
    max_items: int = 100,
    stac_url: str = EARTH_SEARCH_STAC_URL,
    provider: str = EARTH_SEARCH_PROVIDER,
) -> list[SatelliteScene]:
    """
    Generic STAC search returning normalized scenes.

    Cloud filtering is optional and performed locally.

    This function is primarily useful for optical imagery such
    as Sentinel-2.
    """
    items = search_stac_items(
        collection=collection,
        start_date=start_date,
        end_date=end_date,
        max_items=max_items,
        stac_url=stac_url,
        provider=provider,
    )

    if max_cloud_cover is not None:

        items = filter_by_cloud_cover(
            items,
            max_cloud_cover=max_cloud_cover,
        )

    scenes = [
        normalize_item(
            item,
            provider=provider,
        )
        for item in items
    ]

    scenes.sort(
        key=lambda scene: (
            scene.datetime or "",
            scene.cloud_cover
            if scene.cloud_cover is not None
            else 999.0,
        )
    )

    logger.info(
        "Returning %s normalized scenes | provider=%s",
        len(scenes),
        provider,
    )

    return scenes


# ---------------------------------------------------------------------
# Sentinel-2 search
# ---------------------------------------------------------------------

def search_sentinel2(
    start_date: str,
    end_date: str,
    max_cloud_cover: float = DEFAULT_SENTINEL2_CLOUD_COVER,
    max_items: int = 100,
    stac_url: str = EARTH_SEARCH_STAC_URL,
    provider: str = EARTH_SEARCH_PROVIDER,
) -> list[SatelliteScene]:
    """
    Search Sentinel-2 Collection-1 Level-2A imagery.

    Search workflow
    ---------------
    STAC server:
        - collection
        - AOI
        - date

    Local:
        - eo:cloud_cover

    Default cloud threshold is 80 percent because useful flood-event
    optical imagery may occur under substantial cloud cover.
    """
    logger.info(
        "Starting Sentinel-2 search | "
        "provider=%s | "
        "dates=%s/%s | "
        "cloud<=%.1f%%",
        provider,
        start_date,
        end_date,
        max_cloud_cover,
    )

    return search_catalog(
        collection=SENTINEL2_COLLECTION,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=max_cloud_cover,
        max_items=max_items,
        stac_url=stac_url,
        provider=provider,
    )


def search_sentinel2_unfiltered(
    start_date: str,
    end_date: str,
    max_items: int = 100,
    stac_url: str = EARTH_SEARCH_STAC_URL,
    provider: str = EARTH_SEARCH_PROVIDER,
) -> list[SatelliteScene]:
    """
    Search Sentinel-2 without cloud filtering.

    Useful for diagnostics and scene inspection.
    """
    logger.info(
        "Starting unfiltered Sentinel-2 search | "
        "provider=%s | dates=%s/%s",
        provider,
        start_date,
        end_date,
    )

    return search_catalog(
        collection=SENTINEL2_COLLECTION,
        start_date=start_date,
        end_date=end_date,
        max_cloud_cover=None,
        max_items=max_items,
        stac_url=stac_url,
        provider=provider,
    )


# ---------------------------------------------------------------------
# Sentinel-1 search
# ---------------------------------------------------------------------

def search_sentinel1(
    start_date: str,
    end_date: str,
    max_items: int = 100,
    acquisition_mode: str = DEFAULT_SENTINEL1_ACQUISITION_MODE,
    required_polarizations: tuple[str, ...] = (
        DEFAULT_SENTINEL1_POLARIZATIONS
    ),
    orbit_state: str | None = None,
    relative_orbit: int | None = None,
    collection: str =  SENTINEL1_COLLECTION,
    stac_url: str = EARTH_SEARCH_STAC_URL,
    provider: str = EARTH_SEARCH_PROVIDER,
) -> list[SatelliteScene]:
    """
    Search Sentinel-1 GRD imagery.

    Sentinel-1 is SAR, so cloud-cover filtering is intentionally
    not used.

    Candidate scenes are filtered locally by:

    - acquisition mode
    - required polarizations
    - optional orbit direction
    - optional relative orbit

    STAC provider and URL are configurable so another Sentinel-1
    catalogue can be introduced without changing downstream code.
    """
    logger.info(
        "Starting Sentinel-1 search | "
        "provider=%s | "
        "dates=%s/%s | "
        "mode=%s | "
        "polarizations=%s | "
        "orbit=%s | "
        "relative_orbit=%s",
        provider,
        start_date,
        end_date,
        acquisition_mode,
        required_polarizations,
        orbit_state,
        relative_orbit,
    )

    items = search_stac_items(
        collection=collection,
        start_date=start_date,
        end_date=end_date,
        max_items=max_items,
        stac_url=stac_url,
        provider=provider,
    )

    items = filter_sentinel1_items(
        items,
        acquisition_mode=acquisition_mode,
        required_polarizations=(
            required_polarizations
        ),
        orbit_state=orbit_state,
        relative_orbit=relative_orbit,
    )

    scenes = [
        normalize_item(
            item,
            provider=provider,
        )
        for item in items
    ]

    scenes.sort(
        key=lambda scene: (
            scene.datetime or "",
            scene.orbit_state or "",
            scene.relative_orbit
            if scene.relative_orbit is not None
            else -1,
        )
    )

    logger.info(
        "Returning %s normalized Sentinel-1 scenes | provider=%s",
        len(scenes),
        provider,
    )

    return scenes


# ---------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------

def print_search_results(
    scenes: list[SatelliteScene],
) -> None:
    """
    Print human-readable satellite search results.
    """
    if not scenes:

        print(
            "No matching scenes found."
        )

        return

    print(
        f"\nFound {len(scenes)} scene(s):\n"
    )

    for index, scene in enumerate(
        scenes,
        start=1,
    ):

        cloud_text = (
            f"{scene.cloud_cover:.2f}%"
            if scene.cloud_cover is not None
            else "N/A"
        )

        polarization_text = (
            ", ".join(
                scene.polarizations
            )
            if scene.polarizations
            else "N/A"
        )

        print(
            f"{index}. {scene.item_id}\n"
            f"   Provider:       {scene.provider}\n"
            f"   Collection:     {scene.collection}\n"
            f"   Datetime:       {scene.datetime}\n"
            f"   Platform:       {scene.platform}\n"
            f"   Mode:           {scene.acquisition_mode}\n"
            f"   Polarizations:  {polarization_text}\n"
            f"   Orbit:          {scene.orbit_state}\n"
            f"   Relative orbit: {scene.relative_orbit}\n"
            f"   Cloud:          {cloud_text}\n"
            f"   Assets:         {len(scene.assets)}\n"
        )


def print_search_summary(
    scenes: list[SatelliteScene],
) -> None:
    """
    Print a concise search summary.
    """
    print(
        "\nSatellite Search Summary"
    )

    print(
        "------------------------"
    )

    print(
        f"Scenes: {len(scenes)}"
    )

    if not scenes:
        return

    providers = sorted(
        {
            scene.provider
            for scene in scenes
        }
    )

    print(
        f"Providers: {', '.join(providers)}"
    )

    cloud_values = [
        scene.cloud_cover
        for scene in scenes
        if scene.cloud_cover is not None
    ]

    if cloud_values:

        print(
            f"Minimum cloud cover: {min(cloud_values):.2f}%"
        )

        print(
            f"Maximum cloud cover: {max(cloud_values):.2f}%"
        )

        print(
            "Average cloud cover: "
            f"{sum(cloud_values) / len(cloud_values):.2f}%"
        )

    orbit_states = sorted(
        {
            scene.orbit_state
            for scene in scenes
            if scene.orbit_state
        }
    )

    if orbit_states:

        print(
            f"Orbit states: {', '.join(orbit_states)}"
        )

    relative_orbits = sorted(
        {
            scene.relative_orbit
            for scene in scenes
            if scene.relative_orbit is not None
        }
    )

    if relative_orbits:

        print(
            "Relative orbits: "
            + ", ".join(
                str(value)
                for value
                in relative_orbits
            )
        )


def search_sentinel1_planetary_computer(
    start_date: str,
    end_date: str,
    max_items: int = 100,
    acquisition_mode: str = DEFAULT_SENTINEL1_ACQUISITION_MODE,
    required_polarizations: tuple[str, ...] = (
        DEFAULT_SENTINEL1_POLARIZATIONS
    ),
    orbit_state: str | None = None,
    relative_orbit: int | None = None,
) -> list[SatelliteScene]:
    """
    Search Sentinel-1 RTC imagery using Microsoft Planetary Computer.
    """
    logger.info(
        "Starting Sentinel-1 Planetary Computer search"
    )

    return search_sentinel1(
        start_date=start_date,
        end_date=end_date,
        max_items=max_items,
        acquisition_mode=acquisition_mode,
        required_polarizations=required_polarizations,
        orbit_state=orbit_state,
        relative_orbit=relative_orbit,
        collection=PLANETARY_COMPUTER_SENTINEL1_COLLECTION,
        stac_url=PLANETARY_COMPUTER_STAC_URL,
        provider=PLANETARY_COMPUTER_PROVIDER,
    )


# ---------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------

def main() -> None:
    """Run Sentinel-1 Planetary Computer smoke test."""

    logger.info(
        "Running Sentinel-1 Planetary Computer smoke test"
    )

    scenes = search_sentinel1_planetary_computer(
        start_date="2023-12-01",
        end_date="2024-01-15",
        max_items=100,
        acquisition_mode="IW",
        required_polarizations=("VV", "VH"),
    )

    print_search_results(
        scenes
    )

    print_search_summary(
        scenes
    )

    logger.info(
        "Sentinel-1 Planetary Computer smoke test completed | scenes=%s",
        len(scenes),
    )


if __name__ == "__main__":
    main()