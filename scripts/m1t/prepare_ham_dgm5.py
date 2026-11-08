r"""Prepare auditable 5 m terrain tiles for Hamburg M1-T.

Source of truth: unchanged original DGM1/DGM-W files. No mosaicking in this step.
Run from the Bayesian repo:
  & ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\prepare_ham_dgm5.py --mode pilot
"""

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.windows import Window
from rasterio.transform import Affine

ZIP_HH = "raw/HAM/terrain/lgv_dgm1/dgm1_hh_2022-04-30.zip"
ZIP_HH_SHA256 = "32b8d624af3000aa8257205b8701d6389b2a08d6c41a8b78850e6c6863be94f2"
SH_DIR = "processed/HAM/derived/dgm1_sh_1m"
NI_TIF = "raw/HAM/terrain/lgln_ni_dgm1/dgm1_32_552_5924_1_ni_2025.tif"
NI_SHA256 = "695acc10fe4bc04079df8d59629ab04c7e7380bcab6f63360a6f5f9201794a37"
WSV_DIR = "raw/HAM/terrain/wsv_dgmw_2022"
WSV_SHA256 = "b6582f0a656276b33ba4b76a8ae040f6491b85b3376a769cb917d67e32915538"
PILOT_HH = {
    "dgm1_32_555_5938_1_hh_2022.tif",
    "dgm1_32_556_5938_1_hh_2022.tif",
    "dgm1_32_553_5924_1_hh_2022.tif",
}
SH_NAMES = [
    "dgm1_32_555_5939_1_sh_2021.tif",
    "dgm1_32_556_5939_1_sh_2021.tif",
]
WSV_TILE_BOUNDS = (463000, 5979000, 464000, 5980000)  # building 1 plus both rings


def file_sha256(path):
    """Return SHA-256 digest for an existing file, streaming its contents."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_hash(path, expected):
    actual = file_sha256(path)
    if actual.lower() != expected.lower():
        raise ValueError("Source checksum mismatch for {}: {}".format(path, actual))
    return actual


def aggregate_5m(source, minimum_valid_fraction=1.0):
    """Return (elevation, 1m-valid-fraction) from an aligned 1m raster block.

    Strict mode (1.0) requires all 25 source pixels in each output cell.
    Values of -9999 are invalid even if the declared raster mask omitted them.
    Input must be row/column aligned to the 5m target grid.
    """
    if not 0 < minimum_valid_fraction <= 1:
        raise ValueError("minimum_valid_fraction must lie in (0, 1]")
    pixels = np.ma.asarray(source)
    if pixels.ndim != 2 or pixels.shape[0] % 5 or pixels.shape[1] % 5:
        raise ValueError("Source block dimensions must be divisible by five")

    data = np.asarray(pixels.data)
    metadata_mask = np.ma.getmaskarray(pixels)
    valid = (~metadata_mask) & np.isfinite(data) & (data != -9999.0)

    if valid.any():
        vmin = float(data[valid].min())
        vmax = float(data[valid].max())
        if vmin < -1000 or vmax > 2000:
            raise ValueError("Suspicious unmasked elevations: [{}, {}] m".format(vmin, vmax))

    nrows, ncols = data.shape
    counts = valid.reshape(nrows // 5, 5, ncols // 5, 5).sum(axis=(1, 3))
    sums = np.where(valid, data, 0.0).reshape(
        nrows // 5, 5, ncols // 5, 5
    ).sum(axis=(1, 3), dtype=np.float64)

    fractions = (counts / 25.0).astype("float32")
    accepted = counts >= math.ceil(25 * minimum_valid_fraction - 1e-10)
    elevations = np.full(counts.shape, -9999.0, dtype="float32")
    np.divide(sums, counts, out=elevations, where=accepted, casting="unsafe")
    return elevations, fractions


def validate_grid(src, region=None):
    if src.crs is None or src.crs.to_epsg() != 25832:
        raise ValueError("Expected EPSG:25832: {}".format(src.name))
    if src.count != 1:
        raise ValueError("Expected one elevation band: {}".format(src.name))
    t = src.transform
    if not (abs(t.a - 1.0) < 1e-6 and abs(t.e + 1.0) < 1e-6
            and abs(t.b) < 1e-8 and abs(t.d) < 1e-8):
        raise ValueError("Expected north-up 1m grid: {}".format(src.name))
    if region is None:
        region = Window(0, 0, src.width, src.height)
    if (region.width % 5 or region.height % 5
            or region.col_off % 5 or region.row_off % 5):
        raise ValueError("Read window is not 5m aligned")
    wt = src.window_transform(region)
    if (abs(wt.c / 5 - round(wt.c / 5)) > 1e-5
            or abs(wt.f / 5 - round(wt.f / 5)) > 1e-5):
        raise ValueError("Raster origin is not aligned to global 5m grid")
    return region, wt


def output_profile(transform, width, height, datatype, nodata):
    return dict(
        driver="GTiff", width=width, height=height, count=1,
        crs="EPSG:25832", transform=transform, dtype=datatype,
        nodata=nodata, compress="deflate", predictor=3,
        tiled=True, blockxsize=256, blockysize=256,
    )


def convert_source(src, destination, minimum_fraction, chunk_rows=250, region=None):
    """Downsample in aligned source strips and write elevation + validity rasters."""
    region, native_transform = validate_grid(src, region)
    if chunk_rows % 5:
        raise ValueError("chunk_rows must be divisible by 5")

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fraction_file = destination.with_name(destination.stem + "_valid_fraction.tif")
    rows5, cols5 = int(region.height) // 5, int(region.width) // 5
    transform5 = Affine(5.0, 0.0, native_transform.c,
                        0.0, -5.0, native_transform.f)
    assert rows5 * 5 == region.height and cols5 * 5 == region.width

    stats = dict(native_pixels=0, declared_mask_pixels=0,
                 unmasked_minus_9999_pixels=0, valid_native_pixels=0,
                 accepted_5m_cells=0, partial_5m_cells=0, empty_5m_cells=0)
    with rasterio.open(destination, "w", **output_profile(
            transform5, cols5, rows5, "float32", -9999.0)) as elev_dst:
        with rasterio.open(fraction_file, "w", **output_profile(
                transform5, cols5, rows5, "float32", None)) as frac_dst:
            for offset in range(0, int(region.height), chunk_rows):
                height = min(chunk_rows, int(region.height) - offset)
                source_window = Window(region.col_off, region.row_off + offset,
                                       region.width, height)
                block = src.read(1, window=source_window, masked=True)
                data, mask = np.asarray(block.data), np.ma.getmaskarray(block)
                invalid_sentinel = (data == -9999.0) & ~mask
                valid = (~mask) & np.isfinite(data) & (data != -9999.0)
                stats["native_pixels"] += int(data.size)
                stats["declared_mask_pixels"] += int(mask.sum())
                stats["unmasked_minus_9999_pixels"] += int(invalid_sentinel.sum())
                stats["valid_native_pixels"] += int(valid.sum())

                elevation, fraction = aggregate_5m(block, minimum_fraction)
                stats["accepted_5m_cells"] += int((elevation != -9999.0).sum())
                stats["partial_5m_cells"] += int(((fraction > 0) & (fraction < 1)).sum())
                stats["empty_5m_cells"] += int((fraction == 0).sum())
                write_window = Window(0, offset // 5, cols5, height // 5)
                elev_dst.write(elevation, 1, window=write_window)
                frac_dst.write(fraction, 1, window=write_window)

    with rasterio.open(destination) as check:
        if check.width != cols5 or check.height != rows5 or check.res != (5.0, 5.0):
            raise RuntimeError("Output raster geometry validation failed")
    return dict(
        elevation_path=str(destination), elevation_sha256=file_sha256(destination),
        fraction_path=str(fraction_file), fraction_sha256=file_sha256(fraction_file),
        **stats
    )


def selected_hh_tiles(z, mode):
    tiles = sorted(n for n in z.namelist() if n.lower().endswith(".tif"))
    if len(tiles) != 880 or len(set(Path(n).name.lower() for n in tiles)) != 880:
        raise ValueError("Expected 880 uniquely named Hamburg source TIFFs")
    if mode == "pilot":
        tiles = [n for n in tiles if Path(n).name in PILOT_HH]
        if len(tiles) != len(PILOT_HH):
            raise ValueError("Pilot Hamburg tiles were not found")
    return tiles


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("pilot", "all"), default="pilot")
    parser.add_argument("--min-source-fraction", type=float, default=1.0)
    parser.add_argument("--force", action="store_true",
                        help="Permit overwriting existing derived rasters")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    hh_path = root / ZIP_HH
    sh_paths = [root / SH_DIR / name for name in SH_NAMES]
    ni_path = root / NI_TIF
    wsv_matches = list((root / WSV_DIR).glob("*Scharhoern*.tif"))
    if len(wsv_matches) != 1:
        raise ValueError("Expected exactly one Scharhoern WSV GeoTIFF")
    wsv_path = wsv_matches[0]
    assert_hash(hh_path, ZIP_HH_SHA256)
    assert_hash(ni_path, NI_SHA256)
    assert_hash(wsv_path, WSV_SHA256)
    sh_manifest = root / "runs/ham_m1_citywide/qa/sh_dgm1_conversion_manifest.json"
    if not sh_manifest.is_file():
        raise FileNotFoundError("Expected Schleswig-Holstein conversion manifest: {}".format(sh_manifest))
    sh_records = json.loads(sh_manifest.read_text(encoding="utf-8-sig"))["records"]
    known_sh_hashes = {Path(entry["output"]).name: entry["output_sha256"]
                       for entry in sh_records}
    for path in sh_paths:
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.name not in known_sh_hashes:
            raise ValueError("SH source missing from conversion manifest: {}".format(path.name))
        assert_hash(path, known_sh_hashes[path.name])

    folder = (root / "processed/HAM/derived" /
              ("dgm5_pilot" if args.mode == "pilot" else "dgm5_tiles"))
    folder.mkdir(parents=True, exist_ok=True)
    manifest = root / "runs/ham_m1_citywide/qa" / (
        "ham_dgm5_pilot_manifest.json" if args.mode == "pilot"
        else "ham_dgm5_citywide_manifest.json")
    manifest.parent.mkdir(parents=True, exist_ok=True)
    if manifest.exists() and not args.force:
        raise FileExistsError("Manifest exists; use --force to rerun: {}".format(manifest))

    records = []

    def process(src, category, basename, provenance, window=None):
        destination = folder / category / (basename.replace(".tif", "_5m.tif"))
        fraction_path = destination.with_name(destination.stem + "_valid_fraction.tif")
        if not args.force and (destination.exists() or fraction_path.exists()):
            raise FileExistsError("Derived raster already exists: {}".format(destination))
        result = convert_source(src, destination, args.min_source_fraction,
                                region=window)
        result["source"] = provenance
        result["source_filename"] = basename
        result["elevation_path"] = Path(result["elevation_path"]).relative_to(root).as_posix()
        result["fraction_path"] = Path(result["fraction_path"]).relative_to(root).as_posix()
        records.append(result)
        print("{}: accepted {:,} 5m cells; unmasked -9999: {:,}".format(
            basename, result["accepted_5m_cells"],
            result["unmasked_minus_9999_pixels"]))

    with ZipFile(hh_path) as z:
        tiles = selected_hh_tiles(z, args.mode)
        for i, member in enumerate(tiles, 1):
            with MemoryFile(z.read(member)) as mem:
                with mem.open() as src:
                    process(src, "HH", Path(member).name, "LGV_HH_2022")
            if args.mode == "all" and i % 50 == 0:
                print("Hamburg source tiles processed: {}/{}".format(i, len(tiles)))

    for path in sh_paths:
        with rasterio.open(path) as src:
            process(src, "SH", path.name, "LVERMGEO_SH_2021")

    with rasterio.open(ni_path) as src:
        process(src, "NI", ni_path.name, "LGLN_NI_2025")

    with rasterio.open(wsv_path) as src:
        # Only the aligned 1km square needed for Hamburg building 1.
        west, south, east, north = WSV_TILE_BOUNDS
        t = src.transform
        col = round((west - t.c) / t.a)
        row = round((north - t.f) / t.e)
        window = Window(col, row, east - west, north - south)
        if (col < 0 or row < 0 or col + window.width > src.width
                or row + window.height > src.height):
            raise ValueError("WSV Scharhoern 1km window outside raster")
        process(src, "WSV", "dgmw_32_463_5979_1_wsv_2022.tif",
                "WSV_DGMW_2022_SCHARHOERN", window)

    record = dict(
        phase="M1-T", city="HAM", mode=args.mode, generated_utc=datetime.now(
            timezone.utc).isoformat(), target_resolution_m=5,
        method="masked mean of 25 aligned 1m source pixels",
        acceptance_rule="source valid fraction >= {}".format(args.min_source_fraction),
        explicit_unmasked_invalid_value=-9999.0,
        input_archive_sha256=ZIP_HH_SHA256,
        supplemental_ni_sha256=NI_SHA256,
        supplemental_wsv_sha256=WSV_SHA256,
        warning="Geometric and source-fraction preparation only; no citywide building QA or source-datum equivalence established.",
        count=len(records), tiles=records,
    )
    manifest.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("\nHAMBURG DGM5 {} PREPARATION: PASS".format(args.mode.upper()))
    print("Tiles processed:", len(records))
    print("Total unmasked HH -9999:", sum(
        r["unmasked_minus_9999_pixels"] for r in records if r["source"] == "LGV_HH_2022"))
    print("Manifest:", manifest)
    print("Derived rasters:", folder)


if __name__ == "__main__":
    main()
