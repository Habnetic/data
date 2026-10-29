"""
Habnetic | Phase 4 M1-P04d
Consolidate and validate Rotterdam terrain measurements.

Run:
    python scripts/rtm/m1_consolidate_terrain.py

Inputs:
    runs/rtm_m1_citywide/terrain_batches/*.parquet
    processed/RTM/derived/buildings_rtm.gpkg
    runs/rtm_m1_terrain_pilot/mosaic_pilot_regression.csv

Output:
    runs/rtm_m1_citywide/terrain_features_m1_5m.parquet
"""

from pathlib import Path
import re
import sqlite3

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RUN_DIR = ROOT / "runs/rtm_m1_citywide"

BATCH_DIR = RUN_DIR / "terrain_batches"

BUILDINGS = (
    ROOT / "processed/RTM/derived/buildings_rtm.gpkg"
)

PILOT = (
    ROOT / "runs/rtm_m1_terrain_pilot/"
    "mosaic_pilot_regression.csv"
)

OUTPUT = RUN_DIR / "terrain_features_m1_5m.parquet"

EXPECTED = 221324
BATCH_SIZE = 1000


def validate_batches(paths):
    """Check contiguous, non-overlapping batch ranges."""

    expected_start = 0

    for path in paths:

        match = re.fullmatch(
            r"terrain_(\d{6})_(\d{6})\.parquet",
            path.name,
        )

        if match is None:
            raise ValueError(f"Invalid batch filename: {path.name}")

        start, end = map(int, match.groups())

        if start != expected_start:
            raise ValueError(
                f"Batch gap or overlap at {path.name}"
            )

        expected_start = end + 1

    assert expected_start == EXPECTED, (
        f"Batch coverage ends at {expected_start}, "
        f"expected {EXPECTED}"
    )


def main():

    print("\n=== HABNETIC M1-P04d ===")
    print("CITYWIDE TERRAIN CONSOLIDATION")
    print("================================")

    paths = sorted(
        BATCH_DIR.glob("terrain_*.parquet")
    )

    print("\nBatch files:", len(paths))

    assert len(paths) == 222, (
        f"Expected 222 batches, found {len(paths)}"
    )

    validate_batches(paths)

    # Read and combine existing results.
    frames = [pd.read_parquet(path) for path in paths]

    df = pd.concat(
        frames,
        ignore_index=True,
    )

    del frames

    print("\n=== DATA INTEGRITY ===")

    print("Rows:", len(df))
    print("Unique building IDs:", df["bldg_id"].nunique())

    assert len(df) == EXPECTED
    assert df["bldg_id"].is_unique
    assert df["bldg_id"].notna().all()

    # Verify identifiers against the authoritative
    # Rotterdam building geometry dataset.
    with sqlite3.connect(BUILDINGS) as connection:

        source_ids = pd.read_sql_query(
            "SELECT bldg_id FROM buildings_rtm",
            connection,
        )["bldg_id"]

    assert len(source_ids) == EXPECTED
    assert source_ids.is_unique

    assert set(df["bldg_id"]) == set(source_ids), (
        "Terrain IDs differ from source building IDs"
    )

    print("Source building ID agreement: PASS")

    # Basic numerical integrity.
    measured = df["terrain_measured"].astype(bool)

    expected_measured = (
        (df["local_valid_pixels"] >= 20)
        & (df["neighbourhood_valid_pixels"] >= 20)
    )

    assert (measured == expected_measured).all()

    assert df["local_coverage"].between(0, 1).all()
    assert df["neighbourhood_coverage"].between(0, 1).all()

    for prefix in ("local", "neighbourhood"):

        valid_pixels = df[f"{prefix}_valid_pixels"]
        total_pixels = df[f"{prefix}_total_pixels"]
        coverage = df[f"{prefix}_coverage"]

        assert (valid_pixels >= 0).all()
        assert (total_pixels > 0).all()
        assert (valid_pixels <= total_pixels).all()

        assert np.allclose(
            coverage,
            valid_pixels / total_pixels,
            atol=1e-12,
        )

    valid = df.loc[measured]

    assert np.isfinite(valid["T50"]).all()
    assert np.isfinite(valid["T25"]).all()

    assert (
        valid["T25"] >= valid["T50"] - 1e-6
    ).all()

    assert df.loc[~measured, ["T50", "T25"]].isna().all().all()

    # Reproduce the validated 200-building experiment.
    pilot = pd.read_csv(PILOT)

    comparison = df.merge(
        pilot[
            [
                "bldg_id",
                "T50_mosaic",
                "T25_mosaic",
            ]
        ],
        on="bldg_id",
        how="inner",
        validate="one_to_one",
    )

    assert len(comparison) == 200

    assert np.allclose(
        comparison["T50"],
        comparison["T50_mosaic"],
        atol=1e-6,
        rtol=0,
    )

    assert np.allclose(
        comparison["T25"],
        comparison["T25_mosaic"],
        atol=1e-6,
        rtol=0,
    )

    print("200-building pilot agreement: PASS")

    print("\n=== MEASUREMENT AVAILABILITY ===")

    n_measured = int(measured.sum())
    n_missing = int((~measured).sum())

    print("Total buildings:", len(df))
    print("Measured:", n_measured)
    print("Missing:", n_missing)

    print(
        "Measurement availability (%):",
        round(100 * n_measured / len(df), 3),
    )

    print("\n=== TERRAIN DISTRIBUTIONS ===")

    print(
        df[["T50", "T25"]]
        .describe(
            percentiles=[0.05, 0.5, 0.95, 0.99]
        )
        .round(4)
        .to_string()
    )

    print("\n=== COVERAGE DISTRIBUTIONS ===")

    print(
        df[
            [
                "local_coverage",
                "neighbourhood_coverage",
            ]
        ]
        .describe(
            percentiles=[0.05, 0.5, 0.95]
        )
        .round(4)
        .to_string()
    )

    print("\n=== EXTREME VALUES ===")

    print("T50 < -3 m:", int((df["T50"] < -3).sum()))
    print("T50 > +3 m:", int((df["T50"] > 3).sum()))

    print("\n=== MEASUREMENT COVERAGE FLAGS ===")

    for threshold in (0.25, 0.50, 0.75):

        count = int((
            measured
            & (
                (df["local_coverage"] < threshold)
                | (df["neighbourhood_coverage"] < threshold)
            )
        ).sum())

        print(
            f"Measured buildings with either coverage < {threshold:.0%}:",
            count,
        )

    # Write only after validation passes.
    temporary = OUTPUT.with_suffix(".partial.parquet")

    df.to_parquet(
        temporary,
        index=False,
    )

    temporary.replace(OUTPUT)

    print("\n=== RESULT ===")
    print("VALIDATION: PASS")
    print("Saved:", OUTPUT)


if __name__ == "__main__":
    main()