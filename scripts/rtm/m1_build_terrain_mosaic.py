"""
Habnetic | Phase 4 M1-P04b
Build the Rotterdam AHN5 5 m terrain mosaic.

Inputs:
    - Buffered AHN5 tile manifest
    - 28 validated AHN5 5 m DTM tiles

Output:
    processed/RTM/derived/ahn5_dtm_5m_rtm_mosaic.tif

Run:
    python scripts/rtm/m1_build_terrain_mosaic.py

The mosaic preserves source elevation values and NoData.
No interpolation or terrain resampling is performed.
"""

from contextlib import ExitStack
from pathlib import Path
import logging

import numpy as np
import pandas as pd
import rasterio

from rasterio.merge import merge


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

OUTPUT = (
    ROOT
    / "processed/RTM/derived/"
    "ahn5_dtm_5m_rtm_mosaic.tif"
)


def main() -> None:
    """Merge validated terrain tiles into one raster."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    manifest = pd.read_csv(MANIFEST)

    if len(manifest) != 28:
        raise ValueError("Expected 28 AHN5 tiles")

    if not manifest["filename"].is_unique:
        raise ValueError("Duplicate tile filenames")

    paths = [
        SOURCE_DIR / filename
        for filename in manifest["filename"]
    ]

    for path in paths:
        if not path.exists():
            raise FileNotFoundError(path)

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if OUTPUT.exists():
        raise FileExistsError(
            f"Mosaic already exists: {OUTPUT}"
        )

    temporary = OUTPUT.with_name(
        OUTPUT.stem + ".partial.tif"
    )

    if temporary.exists():
        temporary.unlink()

    print("\n=== HABNETIC M1-P04b ===")
    print("AHN5 5 m ROTTERDAM MOSAIC")
    print("=========================")
    print("Source tiles:", len(paths))

    try:
        with ExitStack() as stack:

            sources = [
                stack.enter_context(rasterio.open(path))
                for path in paths
            ]

            reference = sources[0]

            for src in sources:

                if src.crs != reference.crs:
                    raise ValueError(
                        "Source rasters have different CRS"
                    )

                if not np.allclose(
                    src.res,
                    (5.0, 5.0),
                ):
                    raise ValueError(
                        "Unexpected raster resolution"
                    )

                if src.count != 1:
                    raise ValueError(
                        "Expected single-band raster"
                    )

                if src.dtypes[0] != "float32":
                    raise ValueError(
                        "Expected float32 elevation data"
                    )

                if src.nodata != reference.nodata:
                    raise ValueError(
                        "Inconsistent NoData values"
                    )

            logging.info(
                "Source metadata verified"
            )

            logging.info(
                "Building mosaic..."
            )

            merge(
                sources,
                method="first",
                nodata=-9999.0,
                dst_path=str(temporary),
                dst_kwds={
                    "compress": "deflate",
                    "predictor": 3,
                    "tiled": True,
                    "BIGTIFF": "IF_SAFER",
                },
            )

        # Validate the written mosaic before publishing.
        with rasterio.open(temporary) as src:

            assert src.count == 1
            assert src.dtypes[0] == "float32"
            assert np.allclose(src.res, (5.0, 5.0))
            assert src.nodata is not None

            print("\n=== MOSAIC METADATA ===")

            print("CRS:", src.crs)
            print("Resolution:", src.res)
            print("Width:", src.width)
            print("Height:", src.height)
            print("Bounds:", src.bounds)
            print("NoData:", src.nodata)

        temporary.replace(OUTPUT)

    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise

    size_mb = OUTPUT.stat().st_size / (1024 ** 2)

    print("\n=== RESULT ===")
    print("Mosaic created successfully")
    print("File size (MB):", round(size_mb, 2))
    print("Output:", OUTPUT)


if __name__ == "__main__":
    main()