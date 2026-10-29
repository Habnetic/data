"""
Habnetic | Phase 4 M1
Rotterdam AHN5 Terrain Pilot

Purpose
-------
Evaluate the feasibility of extracting local relative elevation
for Rotterdam buildings using AHN5 bare-earth terrain data.

Method
------
1. Select 200 buildings from the test raster extent.
2. Calculate median terrain elevation within 0–20 m of each footprint.
3. Calculate median terrain elevation within 20–100 m.
4. Compute relative elevation.
5. Report data coverage and extreme observations.
6. Export results as CSV.

This is an exploratory terrain-data quality experiment.
It does not modify the Phase 3 baseline or perform Bayesian inference.
"""

from pathlib import Path
import logging

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio

from pyproj import CRS
from rasterio.mask import raster_geometry_mask
from shapely.geometry import box, mapping


# ============================================================
# 1. CONFIGURATION
# ============================================================

SEED = 20261029
SAMPLE_SIZE = 200

LOCAL_BUFFER_M = 20
NEIGHBOURHOOD_BUFFER_M = 100

MIN_VALID_PIXELS = 20

# Resolve paths relative to this script:
# data/scripts/rtm/m1_terrain_pilot.py

DATA_ROOT = Path(__file__).resolve().parents[2]

RASTER_PATH = (
    DATA_ROOT
    / "raw"
    / "RTM"
    / "terrain"
    / "ahn"
    / "ahn5_dtm_5m"
    / "2023_M5_37HN1.TIF"
)

BUILDINGS_PATH = (
    DATA_ROOT
    / "processed"
    / "RTM"
    / "derived"
    / "buildings_rtm.gpkg"
)

OUTPUT_DIR = (
    DATA_ROOT
    / "runs"
    / "rtm_m1_terrain_pilot"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "relative_elevation_20_100m.csv"
)


# ============================================================
# 2. TERRAIN EXTRACTION
# ============================================================

def terrain_stats(src, geometry):
    """
    Calculate median terrain elevation and valid-pixel coverage.

    Returns
    -------
    median : float
        Median valid ground elevation in metres.
    count : int
        Number of valid raster pixels.
    coverage : float
        Fraction of raster pixels containing valid measurements.
    """

    outside, _, window = raster_geometry_mask(
        src,
        [mapping(geometry)],
        crop=True,
    )

    data = src.read(
        1,
        window=window,
        masked=True,
    )

    inside = ~outside

    valid = (
        inside
        & ~np.ma.getmaskarray(data)
        & np.isfinite(data.data)
    )

    count = int(valid.sum())
    total = int(inside.sum())

    median = (
        float(np.median(data.data[valid]))
        if count >= MIN_VALID_PIXELS
        else np.nan
    )

    coverage = (
        count / total
        if total > 0
        else 0.0
    )

    return median, count, coverage


# ============================================================
# 3. PILOT EXPERIMENT
# ============================================================

def run_pilot() -> pd.DataFrame:
    """Extract relative elevation for a reproducible building sample."""

    if not RASTER_PATH.exists():
        raise FileNotFoundError(RASTER_PATH)

    if not BUILDINGS_PATH.exists():
        raise FileNotFoundError(BUILDINGS_PATH)

    logging.info("Starting M1 terrain pilot")

    with rasterio.open(RASTER_PATH) as src:

        # Verify horizontal CRS compatibility.
        raster_crs = CRS.from_user_input(src.crs)

        horizontal_crs = (
            raster_crs.sub_crs_list[0]
            if raster_crs.is_compound
            else raster_crs
        )

        if horizontal_crs.to_epsg() != 28992:
            raise ValueError(
                f"Unexpected raster horizontal CRS: {horizontal_crs}"
            )

        buildings = gpd.read_file(
            BUILDINGS_PATH,
            layer="buildings_rtm",
            bbox=src.bounds,
        )

        if buildings.crs.to_epsg() != 28992:
            raise ValueError(
                f"Unexpected building CRS: {buildings.crs}"
            )

        # Avoid incomplete neighbourhoods at raster boundaries.
        interior = box(*src.bounds).buffer(
            -(NEIGHBOURHOOD_BUFFER_M + 5)
        )

        buildings = buildings[
            buildings.geometry.within(interior)
            & buildings.geometry.notna()
            & ~buildings.geometry.is_empty
        ].copy()

        logging.info(
            "Eligible buildings: %s",
            len(buildings),
        )

        if buildings.empty:
            raise ValueError(
                "No buildings available inside the test raster."
            )

        sample = buildings.sample(
            n=min(SAMPLE_SIZE, len(buildings)),
            random_state=SEED,
        )

        logging.info(
            "Selected %s buildings",
            len(sample),
        )

        results = []

        for _, building in sample.iterrows():

            footprint = building.geometry

            # Local terrain: 0–20 m outside the building.
            local_ring = (
                footprint.buffer(LOCAL_BUFFER_M)
                .difference(footprint)
            )

            # Neighbourhood terrain: 20–100 m from footprint.
            neighbourhood_ring = (
                footprint.buffer(NEIGHBOURHOOD_BUFFER_M)
                .difference(
                    footprint.buffer(LOCAL_BUFFER_M)
                )
            )

            local_z, local_n, local_cov = terrain_stats(
                src,
                local_ring,
            )

            neighbour_z, neighbour_n, neighbour_cov = terrain_stats(
                src,
                neighbourhood_ring,
            )

            relative_z = (
                local_z - neighbour_z
                if np.isfinite(local_z)
                and np.isfinite(neighbour_z)
                else np.nan
            )

            results.append({
                "bldg_id": building["bldg_id"],
                "local_z": local_z,
                "neighbourhood_z": neighbour_z,
                "relative_z": relative_z,
                "local_pixels": local_n,
                "neighbourhood_pixels": neighbour_n,
                "local_coverage": local_cov,
                "neighbourhood_coverage": neighbour_cov,
            })

    return pd.DataFrame(results)


# ============================================================
# 4. RESULTS
# ============================================================

def report_results(df: pd.DataFrame) -> None:
    """Display pilot statistics and extreme observations."""

    print("\n===================================")
    print("HABNETIC | M1 TERRAIN FEATURE PILOT")
    print("===================================")

    print("\n=== SAMPLE ===")

    print("Buildings tested:", len(df))

    print(
        "Usable relative elevations:",
        df["relative_z"].notna().sum(),
    )

    print(
        "Missing relative elevations:",
        df["relative_z"].isna().sum(),
    )

    print("\n=== RELATIVE ELEVATION (METRES) ===")

    print(
        df["relative_z"].describe(
            percentiles=[0.05, 0.50, 0.95]
        ).to_string()
    )

    print("\n=== DATA QUALITY ===")

    print(
        df[
            [
                "local_pixels",
                "neighbourhood_pixels",
                "local_coverage",
                "neighbourhood_coverage",
            ]
        ].describe().to_string()
    )

    columns = [
        "bldg_id",
        "local_z",
        "neighbourhood_z",
        "relative_z",
        "local_pixels",
        "local_coverage",
    ]

    print("\n=== LOWEST RELATIVE ELEVATIONS ===")

    print(
        df.nsmallest(5, "relative_z")[
            columns
        ].to_string(index=False)
    )

    print("\n=== HIGHEST RELATIVE ELEVATIONS ===")

    print(
        df.nlargest(5, "relative_z")[
            columns
        ].to_string(index=False)
    )


# ============================================================
# 5. EXECUTION
# ============================================================

def main() -> None:
    """Execute and export the terrain pilot."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    df = run_pilot()

    report_results(df)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    logging.info(
        "Pilot results saved to %s",
        OUTPUT_FILE,
    )


if __name__ == "__main__":
    main()