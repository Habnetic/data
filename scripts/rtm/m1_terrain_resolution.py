"""
Habnetic | Phase 4 M1-P02
AHN5 Terrain Resolution Sensitivity

Compare relative elevation at 5 m and 0.5 m resolution
for exactly the same 200 Rotterdam buildings.

Input:
    AHN5 0.5 m DTM
    AHN5 5 m DTM
    Existing M1 terrain pilot CSV
    Rotterdam building geometries

Output:
    runs/rtm_m1_terrain_pilot/
        terrain_resolution_comparison.csv

Run:
    python scripts/rtm/m1_terrain_resolution.py

Scientific status:
    Exploratory measurement-resolution comparison.
    No Bayesian inference or empirical flood validation.
"""

from pathlib import Path
import logging

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio

from pyproj import CRS
from rasterio.mask import raster_geometry_mask
from shapely.geometry import mapping


# ============================================================
# CONFIGURATION
# ============================================================

DATA_ROOT = Path(__file__).resolve().parents[2]

BUILDINGS = (
    DATA_ROOT
    / "processed/RTM/derived/buildings_rtm.gpkg"
)

RASTER_5M = (
    DATA_ROOT
    / "raw/RTM/terrain/ahn/"
    "ahn5_dtm_5m/2023_M5_37HN1.TIF"
)

RASTER_05M = (
    DATA_ROOT
    / "raw/RTM/terrain/ahn/"
    "ahn5_dtm_50cm/2023_M_37HN1.TIF"
)

RUN_DIR = (
    DATA_ROOT
    / "runs/rtm_m1_terrain_pilot"
)

PILOT_CSV = (
    RUN_DIR / "relative_elevation_20_100m.csv"
)

OUTPUT_CSV = (
    RUN_DIR / "terrain_resolution_comparison.csv"
)

LOCAL_M = 20
NEIGHBOURHOOD_M = 100
MIN_VALID_PIXELS = 20


# ============================================================
# TERRAIN MEASUREMENT
# ============================================================

def terrain_stats(src, geometry):
    """Calculate median elevation and raster coverage."""

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
        count / total if total > 0 else 0.0
    )

    return median, count, coverage


def calculate_relative_elevation(src, footprint):
    """Calculate building-level local relative elevation."""

    local_ring = (
        footprint.buffer(LOCAL_M)
        .difference(footprint)
    )

    neighbourhood_ring = (
        footprint.buffer(NEIGHBOURHOOD_M)
        .difference(footprint.buffer(LOCAL_M))
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

    return {
        "relative_z_05m": relative_z,
        "local_z_05m": local_z,
        "neighbourhood_z_05m": neighbour_z,
        "local_pixels_05m": local_n,
        "neighbourhood_pixels_05m": neighbour_n,
        "local_coverage_05m": local_cov,
        "neighbourhood_coverage_05m": neighbour_cov,
    }


# ============================================================
# EXPERIMENT
# ============================================================

def run_comparison():
    """Compare terrain measurements for existing pilot buildings."""

    pilot = pd.read_csv(PILOT_CSV)

    assert len(pilot) == 200
    assert pilot["bldg_id"].is_unique

    logging.info(
        "Loaded %s original pilot buildings",
        len(pilot),
    )

    with rasterio.open(RASTER_5M) as coarse, \
         rasterio.open(RASTER_05M) as fine:

        # Confirm identical geographical extent.
        assert np.allclose(
            tuple(coarse.bounds),
            tuple(fine.bounds),
        )

        assert np.allclose(
            coarse.res,
            (5.0, 5.0),
        )

        assert np.allclose(
            fine.res,
            (0.5, 0.5),
        )

        for raster in (coarse, fine):
            crs = CRS.from_user_input(raster.crs)

            horizontal = (
                crs.sub_crs_list[0]
                if crs.is_compound
                else crs
            )

            assert horizontal.to_epsg() == 28992

        logging.info(
            "Raster extent and coordinate systems verified"
        )

        buildings = gpd.read_file(
            BUILDINGS,
            layer="buildings_rtm",
            bbox=fine.bounds,
        )

        buildings = buildings[
            buildings["bldg_id"].isin(
                pilot["bldg_id"]
            )
        ].copy()

        assert buildings.crs.to_epsg() == 28992
        assert len(buildings) == len(pilot)
        assert buildings["bldg_id"].is_unique

        logging.info(
            "Matched %s building geometries",
            len(buildings),
        )

        results = []

        for _, building in buildings.iterrows():

            values = calculate_relative_elevation(
                fine,
                building.geometry,
            )

            values["bldg_id"] = building["bldg_id"]

            results.append(values)

    fine_results = pd.DataFrame(results)

    comparison = pilot.merge(
        fine_results,
        on="bldg_id",
        how="inner",
        validate="one_to_one",
    )

    assert len(comparison) == 200

    # Original pilot columns correspond to the 5 m raster.
    comparison = comparison.rename(
        columns={
            "relative_z": "relative_z_5m",
            "local_z": "local_z_5m",
            "neighbourhood_z": "neighbourhood_z_5m",
            "local_coverage": "local_coverage_5m",
            "neighbourhood_coverage":
                "neighbourhood_coverage_5m",
        }
    )

    comparison["difference_m"] = (
        comparison["relative_z_05m"]
        - comparison["relative_z_5m"]
    )

    comparison["abs_difference_m"] = (
        comparison["difference_m"].abs()
    )

    # A sign reversal means the relative elevation
    # changes from positive to negative or vice versa.
    valid = comparison[
        ["relative_z_5m", "relative_z_05m"]
    ].notna().all(axis=1)

    comparison["sign_changed"] = False

    comparison.loc[valid, "sign_changed"] = (
        np.sign(
            comparison.loc[valid, "relative_z_5m"]
        )
        != np.sign(
            comparison.loc[valid, "relative_z_05m"]
        )
    )

    return comparison


# ============================================================
# REPORT
# ============================================================

def report_results(df):
    """Report resolution sensitivity statistics."""

    valid = df.dropna(
        subset=[
            "relative_z_5m",
            "relative_z_05m",
        ]
    )

    print("\n======================================")
    print("HABNETIC | M1-P02 RESOLUTION COMPARISON")
    print("======================================")

    print("\n=== DATA AVAILABILITY ===")

    print("Buildings:", len(df))
    print("Valid comparisons:", len(valid))
    print(
        "Missing 0.5 m measurements:",
        df["relative_z_05m"].isna().sum(),
    )

    print("\n=== RESOLUTION DIFFERENCES ===")

    if valid.empty:
        print("No valid paired comparisons.")
        return

    print(
        "Mean difference (m):",
        round(valid["difference_m"].mean(), 4),
    )

    print(
        "Median absolute difference (m):",
        round(valid["abs_difference_m"].median(), 4),
    )

    print(
        "95th percentile absolute difference (m):",
        round(
            valid["abs_difference_m"].quantile(0.95),
            4,
        ),
    )

    print(
        "Maximum absolute difference (m):",
        round(valid["abs_difference_m"].max(), 4),
    )

    print(
        "Pearson correlation:",
        round(
            valid["relative_z_5m"].corr(
                valid["relative_z_05m"]
            ),
            4,
        ),
    )

    print(
        "Spearman correlation:",
        round(
            valid["relative_z_5m"].corr(
                valid["relative_z_05m"],
                method="spearman",
            ),
            4,
        ),
    )

    print(
        "Sign changes:",
        int(valid["sign_changed"].sum()),
    )

    print("\n=== COVERAGE COMPARISON ===")

    print(
        df[
            [
                "local_coverage_5m",
                "local_coverage_05m",
                "neighbourhood_coverage_5m",
                "neighbourhood_coverage_05m",
            ]
        ].describe().to_string()
    )

    print("\n=== LARGEST DIFFERENCES ===")

    columns = [
        "bldg_id",
        "relative_z_5m",
        "relative_z_05m",
        "difference_m",
        "local_coverage_05m",
    ]

    print(
        valid.nlargest(
            10,
            "abs_difference_m",
        )[columns].to_string(index=False)
    )


# ============================================================
# MAIN
# ============================================================

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    comparison = run_comparison()

    report_results(comparison)

    RUN_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    comparison.to_csv(
        OUTPUT_CSV,
        index=False,
    )

    logging.info(
        "Saved comparison: %s",
        OUTPUT_CSV,
    )


if __name__ == "__main__":
    main()