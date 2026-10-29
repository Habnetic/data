"""
Habnetic | Phase 4 M1-P04f
Export a reproducible spatial QA sample.

Inputs:
    terrain_features_m1_5m.parquet
    buildings_rtm.gpkg

Output:
    terrain_spatial_qa_sample.gpkg

Run:
    python scripts/rtm/m1_export_spatial_qa.py
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RUN_DIR = ROOT / "runs/rtm_m1_citywide"

TERRAIN = RUN_DIR / "terrain_features_m1_5m.parquet"

BUILDINGS = (
    ROOT / "processed/RTM/derived/buildings_rtm.gpkg"
)

OUTPUT = RUN_DIR / "terrain_spatial_qa_sample.gpkg"

SEED = 20261029


def select_sample(
    df: pd.DataFrame,
    count: int,
    category: str,
    random: bool = False,
) -> pd.DataFrame:
    """Select and label QA observations."""

    if random:
        selected = df.sample(
            n=min(count, len(df)),
            random_state=SEED,
        )
    else:
        selected = df.head(count)

    result = selected.copy()
    result["qa_group"] = category

    return result


def main() -> None:

    df = pd.read_parquet(TERRAIN)

    assert len(df) == 221324
    assert df["bldg_id"].is_unique

    measured = df["terrain_measured"]

    positive = df[
        measured & (df["T50"] > 3)
    ].sort_values("T50", ascending=False)

    negative = df[
        measured & (df["T50"] < -3)
    ].sort_values("T50")

    missing_zero = df[
        ~measured
        & (df["local_valid_pixels"] == 0)
    ]

    missing_partial = df[
        ~measured
        & (df["local_valid_pixels"] > 0)
        & (df["local_valid_pixels"] < 20)
    ]

    low_coverage = df[
        measured
        & (df["T50"].abs() <= 3)
        & (
            (df["local_coverage"] < 0.25)
            | (df["neighbourhood_coverage"] < 0.25)
        )
    ]

    controls = df[
        measured
        & (df["T50"].abs() < 0.1)
        & (df["local_coverage"] >= 0.75)
        & (df["neighbourhood_coverage"] >= 0.75)
    ]

    samples = [
        select_sample(positive, 6, "extreme_positive"),
        select_sample(negative, 6, "extreme_negative"),
        select_sample(missing_zero, 5, "missing_zero"),
        select_sample(
            missing_partial,
            5,
            "missing_partial",
        ),
        select_sample(
            low_coverage,
            6,
            "low_coverage",
            random=True,
        ),
        select_sample(
            controls,
            8,
            "control",
            random=True,
        ),
    ]

    sample = pd.concat(
        samples,
        ignore_index=True,
    ).drop_duplicates("bldg_id")

    buildings = gpd.read_file(
        BUILDINGS,
        layer="buildings_rtm",
    )

    assert buildings.crs.to_epsg() == 28992
    assert buildings["bldg_id"].is_unique

    geometry = buildings[
        ["bldg_id", "geometry"]
    ].copy()

    spatial = geometry.merge(
        sample,
        on="bldg_id",
        how="inner",
        validate="one_to_one",
    )

    assert len(spatial) == len(sample)

    if OUTPUT.exists():
        raise FileExistsError(
            f"QA file already exists: {OUTPUT}"
        )

    spatial.to_file(
        OUTPUT,
        layer="terrain_qa",
        driver="GPKG",
    )

    print("\n=== HABNETIC M1-P04f ===")
    print("SPATIAL QUALITY SAMPLE")
    print("======================")

    print("Buildings selected:", len(spatial))
    print("CRS:", spatial.crs)

    print("\n=== SAMPLE CATEGORIES ===")

    print(
        spatial["qa_group"]
        .value_counts()
        .to_string()
    )

    print("\nOutput:")
    print(OUTPUT)


if __name__ == "__main__":
    main()