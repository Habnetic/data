"""
Habnetic | Phase 4 M1-P04c
Rotterdam building-level terrain extraction.

Generates T50 and T25 from the validated AHN5 5 m mosaic.

Inputs
------
processed/RTM/derived/buildings_rtm.gpkg
processed/RTM/derived/ahn5_dtm_5m_rtm_mosaic.tif

Outputs
-------
runs/rtm_m1_citywide/terrain_batches/*.parquet

Usage
-----
Pilot:
    python scripts/rtm/m1_extract_terrain_citywide.py --limit 1000

Full extraction:
    python scripts/rtm/m1_extract_terrain_citywide.py --all

Processing is deterministic and uses resumable batches.
No missing terrain values are imputed.
"""

import argparse
import logging
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio

from rasterio.mask import raster_geometry_mask
from shapely.geometry import mapping


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

BUILDINGS = (
    ROOT / "processed/RTM/derived/buildings_rtm.gpkg"
)

MOSAIC = (
    ROOT / "processed/RTM/derived/"
    "ahn5_dtm_5m_rtm_mosaic.tif"
)

OUTPUT_DIR = (
    ROOT / "runs/rtm_m1_citywide/terrain_batches"
)

LOCAL_BUFFER_M = 20
NEIGHBOURHOOD_BUFFER_M = 100

MIN_VALID_PIXELS = 20
BATCH_SIZE = 1000

EXPECTED_BUILDINGS = 221324


# ============================================================
# TERRAIN MEASUREMENTS
# ============================================================

def terrain_stats(src, geometry):
    """Return elevation quantiles, pixel counts and coverage."""

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
        return {
            "p50": np.nan,
            "p25": np.nan,
            "valid_pixels": count,
            "total_pixels": total,
            "coverage": coverage,
        }

    return {
        "p50": float(np.median(values)),
        "p25": float(np.percentile(values, 25)),
        "valid_pixels": count,
        "total_pixels": total,
        "coverage": coverage,
    }


def extract_building(src, bldg_id, footprint):
    """Extract relative terrain elevation for one building."""

    local_ring = (
        footprint.buffer(LOCAL_BUFFER_M)
        .difference(footprint)
    )

    neighbourhood_ring = (
        footprint.buffer(NEIGHBOURHOOD_BUFFER_M)
        .difference(
            footprint.buffer(LOCAL_BUFFER_M)
        )
    )

    local = terrain_stats(src, local_ring)

    neighbourhood = terrain_stats(
        src,
        neighbourhood_ring,
    )

    local_z = local["p50"]
    neighbourhood_z50 = neighbourhood["p50"]
    neighbourhood_z25 = neighbourhood["p25"]

    return {
        "bldg_id": bldg_id,

        "local_z_50": local_z,
        "neighbourhood_z_50": neighbourhood_z50,
        "neighbourhood_z_25": neighbourhood_z25,

        "T50": local_z - neighbourhood_z50,
        "T25": local_z - neighbourhood_z25,

        "local_valid_pixels": local["valid_pixels"],
        "local_total_pixels": local["total_pixels"],
        "local_coverage": local["coverage"],

        "neighbourhood_valid_pixels":
            neighbourhood["valid_pixels"],

        "neighbourhood_total_pixels":
            neighbourhood["total_pixels"],

        "neighbourhood_coverage":
            neighbourhood["coverage"],

        "terrain_measured": bool(
            np.isfinite(local_z)
            and np.isfinite(neighbourhood_z50)
            and np.isfinite(neighbourhood_z25)
        ),
    }


# ============================================================
# DATA LOADING
# ============================================================

def load_buildings():
    """Load and deterministically order Rotterdam buildings."""

    buildings = gpd.read_file(
        BUILDINGS,
        layer="buildings_rtm",
    )

    if buildings.crs.to_epsg() != 28992:
        raise ValueError("Unexpected building CRS")

    if len(buildings) != EXPECTED_BUILDINGS:
        raise ValueError(
            "Unexpected building count: {}".format(
                len(buildings)
            )
        )

    if buildings["bldg_id"].isna().any():
        raise ValueError("Missing building identifiers")

    if not buildings["bldg_id"].is_unique:
        raise ValueError("Duplicate building identifiers")

    buildings = buildings.sort_values(
        "bldg_id",
        kind="mergesort",
    ).reset_index(drop=True)

    return buildings


# ============================================================
# BATCH PROCESSING
# ============================================================

def process_batch(src, batch, start_index, end_index):
    """Process and save one deterministic building batch."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = (
        "terrain_{:06d}_{:06d}.parquet".format(
            start_index,
            end_index - 1,
        )
    )

    destination = OUTPUT_DIR / filename

    if destination.exists():

        existing = pd.read_parquet(destination)

        if (
            len(existing) == len(batch)
            and existing["bldg_id"].is_unique
            and existing["bldg_id"].tolist()
                == batch["bldg_id"].tolist()
        ):
            logging.info(
                "Reusing validated batch: %s",
                filename,
            )
            return existing

        raise ValueError(
            "Existing batch failed validation: {}".format(
                destination
            )
        )

    records = []

    for index, building in batch.iterrows():

        if building.geometry is None or building.geometry.is_empty:
            raise ValueError(
                "Missing geometry for building {}".format(
                    building["bldg_id"]
                )
            )

        result = extract_building(
            src,
            building["bldg_id"],
            building.geometry,
        )

        records.append(result)

    result = pd.DataFrame(records)

    if len(result) != len(batch):
        raise ValueError("Batch row count mismatch")

    if not result["bldg_id"].is_unique:
        raise ValueError("Duplicate output identifiers")

    temporary = destination.with_suffix(".partial.parquet")

    result.to_parquet(
        temporary,
        index=False,
    )

    temporary.replace(destination)

    logging.info(
        "Saved %s | measured: %s/%s",
        filename,
        int(result["terrain_measured"].sum()),
        len(result),
    )

    return result


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "--limit",
        type=int,
        help="Process the first N buildings",
    )

    group.add_argument(
        "--all",
        action="store_true",
        help="Process every Rotterdam building",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    buildings = load_buildings()

    if not args.all:
        if args.limit <= 0:
            raise ValueError("--limit must be positive")

        buildings = buildings.iloc[:args.limit].copy()

    print("\n=== HABNETIC M1-P04c ===")
    print("CITYWIDE TERRAIN EXTRACTION")
    print("===========================")

    print("Buildings selected:", len(buildings))
    print("Batch size:", BATCH_SIZE)
    print("Raster:", MOSAIC.name)

    with rasterio.open(MOSAIC) as src:

        if src.nodata != -9999.0:
            raise ValueError("Unexpected mosaic NoData")

        if not np.allclose(src.res, (5.0, 5.0)):
            raise ValueError("Unexpected mosaic resolution")

        for start in range(0, len(buildings), BATCH_SIZE):

            end = min(
                start + BATCH_SIZE,
                len(buildings),
            )

            batch = buildings.iloc[start:end]

            logging.info(
                "Processing buildings %s to %s",
                start + 1,
                end,
            )

            process_batch(
                src,
                batch,
                start,
                end,
            )

    print("\n=== EXTRACTION COMPLETE ===")
    print("Buildings selected:", len(buildings))
    print("Output directory:", OUTPUT_DIR)


if __name__ == "__main__":
    main()