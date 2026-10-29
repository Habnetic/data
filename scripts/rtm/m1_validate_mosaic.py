"""
Habnetic | Phase 4 M1-P04b
Validate the AHN5 Rotterdam mosaic against all 28 source tiles.

Checks:
    - Identical raster window dimensions
    - Identical valid-data masks
    - Exact equality of valid elevation values

Output:
    runs/rtm_m1_citywide/ahn5_5m_mosaic_integrity.csv

Run:
    python scripts/rtm/m1_validate_mosaic.py
"""

from pathlib import Path
import logging

import numpy as np
import pandas as pd
import rasterio

from rasterio.windows import from_bounds


ROOT = Path(__file__).resolve().parents[2]

MANIFEST = (
    ROOT
    / "runs/rtm_m1_citywide/"
    "ahn5_5m_tile_manifest_buffered.csv"
)

SOURCE_DIR = (
    ROOT
    / "raw/RTM/terrain/ahn/ahn5_dtm_5m"
)

MOSAIC = (
    ROOT
    / "processed/RTM/derived/"
    "ahn5_dtm_5m_rtm_mosaic.tif"
)

OUTPUT = (
    ROOT
    / "runs/rtm_m1_citywide/"
    "ahn5_5m_mosaic_integrity.csv"
)


def validate_tile(source_path, mosaic):
    """Compare an original raster against its mosaic window."""

    with rasterio.open(source_path) as src:

        if src.crs != mosaic.crs:
            raise ValueError("CRS mismatch")

        if not np.allclose(src.res, mosaic.res):
            raise ValueError("Resolution mismatch")

        window = from_bounds(
            *src.bounds,
            transform=mosaic.transform,
        ).round_offsets().round_lengths()

        source = src.read(1, masked=True)

        merged = mosaic.read(
            1,
            window=window,
            masked=True,
        )

        if source.shape != merged.shape:
            raise ValueError(
                f"Shape mismatch: {source.shape} vs {merged.shape}"
            )

        source_mask = np.ma.getmaskarray(source)
        merged_mask = np.ma.getmaskarray(merged)

        masks_identical = np.array_equal(
            source_mask,
            merged_mask,
        )

        valid = ~source_mask & ~merged_mask

        if valid.any():
            max_difference = float(
                np.max(
                    np.abs(
                        source.data[valid]
                        - merged.data[valid]
                    )
                )
            )
        else:
            max_difference = np.nan

        source_valid = int((~source_mask).sum())
        mosaic_valid = int((~merged_mask).sum())

        passed = (
            masks_identical
            and source_valid == mosaic_valid
            and (
                max_difference == 0.0
                or (
                    source_valid == 0
                    and mosaic_valid == 0
                )
            )
        )

        return {
            "filename": source_path.name,
            "source_valid_pixels": source_valid,
            "mosaic_valid_pixels": mosaic_valid,
            "masks_identical": masks_identical,
            "max_difference_m": max_difference,
            "passed": passed,
        }


def main():
    """Validate every source tile."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    manifest = pd.read_csv(MANIFEST)

    assert len(manifest) == 28
    assert manifest["filename"].is_unique

    records = []

    with rasterio.open(MOSAIC) as mosaic:

        assert mosaic.nodata == -9999.0
        assert np.allclose(mosaic.res, (5.0, 5.0))

        for index, filename in enumerate(
            manifest["filename"],
            start=1,
        ):

            logging.info(
                "[%s/%s] %s",
                index,
                len(manifest),
                filename,
            )

            source_path = SOURCE_DIR / filename

            if not source_path.exists():
                raise FileNotFoundError(source_path)

            result = validate_tile(
                source_path,
                mosaic,
            )

            records.append(result)

    df = pd.DataFrame(records)

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(OUTPUT, index=False)

    print("\n=== HABNETIC M1-P04b ===")
    print("COMPLETE MOSAIC INTEGRITY")
    print("=========================")

    print("Tiles validated:", len(df))

    print(
        "Tests passed:",
        int(df["passed"].sum()),
    )

    print(
        "Tests failed:",
        int((~df["passed"]).sum()),
    )

    print(
        "Identical masks:",
        int(df["masks_identical"].sum()),
    )

    print("\n=== RESULTS ===")

    print(
        df[
            [
                "filename",
                "source_valid_pixels",
                "mosaic_valid_pixels",
                "max_difference_m",
                "passed",
            ]
        ].to_string(index=False)
    )

    print("\nSaved:", OUTPUT)

    if not df["passed"].all():
        raise SystemExit(
            "FAILED: Mosaic differs from source data."
        )

    print("\nRESULT: PASS")


if __name__ == "__main__":
    main()