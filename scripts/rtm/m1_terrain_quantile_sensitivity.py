"""
Habnetic | Phase 4 M1-P03
Neighbourhood quantile sensitivity.

Compare P25 and P50 neighbourhood references
across 5 m and 0.5 m AHN5 terrain data.

Run from the data repository:
    python scripts/rtm/m1_terrain_quantile_sensitivity.py
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

INPUT = RUN_DIR / "terrain_resolution_comparison.csv"

OUTPUT = RUN_DIR / "terrain_quantile_sensitivity.csv"

BUILDINGS = ROOT / "processed/RTM/derived/buildings_rtm.gpkg"

RASTERS = {
    "5m": ROOT / (
        "raw/RTM/terrain/ahn/"
        "ahn5_dtm_5m/2023_M5_37HN1.TIF"
    ),
    "05m": ROOT / (
        "raw/RTM/terrain/ahn/"
        "ahn5_dtm_50cm/2023_M_37HN1.TIF"
    ),
}


def extract_quantiles(src, geometry):
    """Extract P25 and P50 from valid terrain cells."""

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

    valid = (
        ~outside
        & ~np.ma.getmaskarray(data)
        & np.isfinite(data.data)
    )

    values = data.data[valid]

    if len(values) < 20:
        return np.nan, np.nan

    return (
        float(np.percentile(values, 25)),
        float(np.percentile(values, 50)),
    )


def main():
    previous = pd.read_csv(INPUT)

    assert len(previous) == 200
    assert previous["bldg_id"].is_unique

    buildings = gpd.read_file(
        BUILDINGS,
        layer="buildings_rtm",
        bbox=(90000, 431250, 95000, 437500),
    )

    buildings = buildings[
        buildings["bldg_id"].isin(previous["bldg_id"])
    ].copy()

    assert len(buildings) == 200
    assert buildings["bldg_id"].is_unique
    assert buildings.crs.to_epsg() == 28992

    results = []

    for resolution, path in RASTERS.items():

        with rasterio.open(path) as src:

            for _, building in buildings.iterrows():

                footprint = building.geometry

                ring = (
                    footprint.buffer(100)
                    .difference(footprint.buffer(20))
                )

                p25, p50 = extract_quantiles(src, ring)

                results.append({
                    "bldg_id": building["bldg_id"],
                    "resolution": resolution,
                    "neighbourhood_p25": p25,
                    "neighbourhood_p50": p50,
                })

    quantiles = pd.DataFrame(results)

    wide = quantiles.pivot(
        index="bldg_id",
        columns="resolution",
        values=[
            "neighbourhood_p25",
            "neighbourhood_p50",
        ],
    )

    wide.columns = [
        f"{stat}_{resolution}"
        for stat, resolution in wide.columns
    ]

    wide = wide.reset_index()

    df = previous.merge(
        wide,
        on="bldg_id",
        validate="one_to_one",
    )

    # Check that the new P50 extraction reproduces
    # the existing experiment.
    for resolution in ("5m", "05m"):

        error = (
            df[f"neighbourhood_p50_{resolution}"]
            - df[f"neighbourhood_z_{resolution}"]
        ).abs()

        assert error.max() < 1e-4, (
            f"P50 reproducibility failure: {resolution}"
        )

        # Candidate A: local median minus neighbourhood P50.
        df[f"T50_{resolution}"] = (
            df[f"local_z_{resolution}"]
            - df[f"neighbourhood_p50_{resolution}"]
        )

        # Candidate B: local median minus neighbourhood P25.
        df[f"T25_{resolution}"] = (
            df[f"local_z_{resolution}"]
            - df[f"neighbourhood_p25_{resolution}"]
        )

    print("\n=== M1-P03 QUANTILE SENSITIVITY ===")

    for candidate in ("T50", "T25"):

        a = df[f"{candidate}_5m"]
        b = df[f"{candidate}_05m"]

        valid = a.notna() & b.notna()
        delta = (b[valid] - a[valid]).abs()

        print(f"\n=== {candidate} ===")
        print("Valid comparisons:", valid.sum())
        print("Median absolute difference:", round(delta.median(), 4))
        print("P95 absolute difference:", round(delta.quantile(.95), 4))
        print("Maximum absolute difference:", round(delta.max(), 4))
        print("Spearman correlation:", round(a.corr(b, method="spearman"), 4))

    print("\n=== BUILDING 920749 ===")

    columns = [
        "bldg_id",
        "T50_5m",
        "T50_05m",
        "T25_5m",
        "T25_05m",
    ]

    print(
        df[df["bldg_id"] == 920749][columns]
        .round(4)
        .to_string(index=False)
    )

    df.to_csv(OUTPUT, index=False)

    print("\nSaved:", OUTPUT)


if __name__ == "__main__":
    main()