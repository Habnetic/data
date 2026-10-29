"""
Habnetic | Phase 4 M1-P04c
Regression test: mosaic versus original 200-building pilot.

Checks:
    - Identical building IDs
    - T50 reproduction
    - T25 reproduction
    - Local and neighbourhood coverage reproduction

Run:
    python scripts/rtm/m1_validate_pilot_mosaic.py
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio

from rasterio.mask import raster_geometry_mask
from shapely.geometry import mapping


ROOT = Path(__file__).resolve().parents[2]

RUN_DIR = ROOT / "runs/rtm_m1_terrain_pilot"

PILOT = RUN_DIR / "relative_elevation_20_100m.csv"

QUANTILES = RUN_DIR / "terrain_quantile_sensitivity.csv"

BUILDINGS = ROOT / "processed/RTM/derived/buildings_rtm.gpkg"

MOSAIC = (
    ROOT
    / "processed/RTM/derived/"
    "ahn5_dtm_5m_rtm_mosaic.tif"
)

OUTPUT = RUN_DIR / "mosaic_pilot_regression.csv"

MIN_VALID_PIXELS = 20
TOLERANCE = 1e-4


def terrain_stats(src, geometry):
    """Extract median, P25, counts and coverage."""

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

    values = data.data[valid]

    count = int(valid.sum())
    total = int(inside.sum())

    coverage = count / total if total else 0.0

    if count < MIN_VALID_PIXELS:
        return np.nan, np.nan, count, coverage

    return (
        float(np.median(values)),
        float(np.percentile(values, 25)),
        count,
        coverage,
    )


def main():
    pilot = pd.read_csv(PILOT)
    quantiles = pd.read_csv(QUANTILES)

    assert len(pilot) == 200
    assert pilot["bldg_id"].is_unique
    assert quantiles["bldg_id"].is_unique

    buildings = gpd.read_file(
        BUILDINGS,
        layer="buildings_rtm",
        bbox=(90000, 431250, 95000, 437500),
    )

    buildings = buildings[
        buildings["bldg_id"].isin(pilot["bldg_id"])
    ].copy()

    assert len(buildings) == 200
    assert buildings["bldg_id"].is_unique
    assert buildings.crs.to_epsg() == 28992

    records = []

    with rasterio.open(MOSAIC) as src:

        assert src.nodata == -9999.0

        for _, building in buildings.iterrows():

            footprint = building.geometry

            local_ring = (
                footprint.buffer(20)
                .difference(footprint)
            )

            neighbourhood_ring = (
                footprint.buffer(100)
                .difference(footprint.buffer(20))
            )

            local_p50, _, local_n, local_cov = terrain_stats(
                src, local_ring
            )

            neighbour_p50, neighbour_p25, neighbour_n, neighbour_cov = (
                terrain_stats(src, neighbourhood_ring)
            )

            records.append({
                "bldg_id": building["bldg_id"],
                "T50_mosaic": local_p50 - neighbour_p50,
                "T25_mosaic": local_p50 - neighbour_p25,
                "local_coverage_mosaic": local_cov,
                "neighbourhood_coverage_mosaic": neighbour_cov,
                "local_pixels_mosaic": local_n,
                "neighbourhood_pixels_mosaic": neighbour_n,
            })

    results = pd.DataFrame(records)

    results = results.merge(
        pilot[
            [
                "bldg_id",
                "relative_z",
                "local_coverage",
                "neighbourhood_coverage",
                "local_pixels",
                "neighbourhood_pixels",
            ]
        ],
        on="bldg_id",
        validate="one_to_one",
    )

    results = results.merge(
        quantiles[["bldg_id", "T25_5m"]],
        on="bldg_id",
        validate="one_to_one",
    )

    results["T50_error"] = (
        results["T50_mosaic"] - results["relative_z"]
    ).abs()

    results["T25_error"] = (
        results["T25_mosaic"] - results["T25_5m"]
    ).abs()

    print("\n=== HABNETIC M1-P04c ===")
    print("MOSAIC PILOT REGRESSION")
    print("=======================")

    print("Buildings:", len(results))

    print(
        "Maximum T50 difference:",
        results["T50_error"].max(),
    )

    print(
        "Maximum T25 difference:",
        results["T25_error"].max(),
    )

    checks = {
        "T50": results["T50_error"].max() < TOLERANCE,
        "T25": results["T25_error"].max() < TOLERANCE,
        "Local coverage": np.allclose(
            results["local_coverage_mosaic"],
            results["local_coverage"],
            atol=1e-10,
        ),
        "Neighbourhood coverage": np.allclose(
            results["neighbourhood_coverage_mosaic"],
            results["neighbourhood_coverage"],
            atol=1e-10,
        ),
        "Local pixel counts": (
            results["local_pixels_mosaic"]
            == results["local_pixels"]
        ).all(),
        "Neighbourhood pixel counts": (
            results["neighbourhood_pixels_mosaic"]
            == results["neighbourhood_pixels"]
        ).all(),
    }

    print("\n=== VALIDATION ===")

    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")

    results.to_csv(OUTPUT, index=False)

    print("\nSaved:", OUTPUT)

    if not all(checks.values()):
        raise SystemExit("REGRESSION TEST FAILED")

    print("\nRESULT: PASS")


if __name__ == "__main__":
    main()