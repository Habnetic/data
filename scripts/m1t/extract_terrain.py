"""Habnetic M1-T: reusable 5 m building-level terrain extraction.

Frozen Rotterdam definitions:
    local ring: footprint.buffer(20 m) minus footprint
    neighbourhood ring: footprint.buffer(100 m) minus footprint.buffer(20 m)
    T50 = median(local) - median(neighbourhood)
    T25 = median(local) - p25(neighbourhood)

M1-T portability QA adds >= 99% *geometric* ring coverage. This is not
part of the frozen Rotterdam M1 scientific specification.

Run from Habnetic/data root using its geospatial environment:
    .venv/Scripts/python.exe scripts/m1t/extract_terrain.py --city DON --limit 100
    .venv/Scripts/python.exe scripts/m1t/extract_terrain.py --city DON --all
    .venv/Scripts/python.exe scripts/m1t/extract_terrain.py --city RTM --limit 100
"""

import argparse
import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import raster_geometry_mask
from shapely.geometry import box, mapping

ROOT = Path(__file__).resolve().parents[2]
LOCAL_BUFFER_M = 20.0
NEIGHBOURHOOD_BUFFER_M = 100.0
MIN_VALID_PIXELS = 20
MIN_GEOMETRIC_COVERAGE = 0.99
BATCH_SIZE = 1000

CITY_CONFIG = {
    "DON": {
        "buildings": "processed/DON/derived/buildings_don.gpkg",
        "mosaic": "processed/DON/derived/mdt05_don_5m_mosaic.tif",
        "n_buildings": 7755,
        "epsg": 25830,
        "output_prefix": "runs/don_m1_citywide",
    },
    "HAM": {
        "buildings": "processed/HAM/derived/buildings_ham.gpkg",
        "mosaic": "processed/HAM/derived/ham_dtm_5m_mosaic.tif",
        "n_buildings": 341530,
        "epsg": 25832,
        "output_prefix": "runs/ham_m1_citywide",
    },
    "RTM": {
        "buildings": "processed/RTM/derived/buildings_rtm.gpkg",
        "mosaic": "processed/RTM/derived/ahn5_dtm_5m_rtm_mosaic.tif",
        "n_buildings": 221324,
        "epsg": 28992,
        "output_prefix": "runs/rtm_m1t_regression",
    },
}


def sha256_file(path):
    """Calculate a reproducible file checksum without loading entire file."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def terrain_stats(src, geometry, raster_extent):
    """Return ring quantiles and distinct geometric / valid-pixel coverage."""
    if geometry.is_empty or geometry.area <= 0:
        raise ValueError("Invalid ring geometry: empty or zero area")
    geometric_coverage = float(
        min(1.0, max(0.0, geometry.intersection(raster_extent).area / geometry.area))
    )
    result = {
        "p50": np.nan,
        "p25": np.nan,
        "valid_pixels": 0,
        "total_pixels": 0,
        "coverage": 0.0,
        "geometric_coverage": geometric_coverage,
    }
    if geometric_coverage <= 0.0:
        return result

    # Preserve the frozen Rotterdam masking semantics (pixel centre inclusion).
    outside, _, window = raster_geometry_mask(src, [mapping(geometry)], crop=True)
    data = src.read(1, window=window, masked=True)
    inside = ~outside
    valid = (
        inside
        & ~np.ma.getmaskarray(data)
        & np.isfinite(data.data)
    )
    values = data.data[valid]
    count = int(valid.sum())
    total = int(inside.sum())
    result.update({
        "valid_pixels": count,
        "total_pixels": total,
        "coverage": count / total if total else 0.0,
    })
    # An incomplete raster ring may otherwise appear 100%-valid by counting
    # only the pixels inside the raster. Reject such measurements explicitly.
    if count >= MIN_VALID_PIXELS and geometric_coverage >= MIN_GEOMETRIC_COVERAGE:
        result["p50"] = float(np.median(values))
        result["p25"] = float(np.percentile(values, 25))
    return result


def extract_building(src, bldg_id, footprint, raster_extent):
    """Calculate frozen T50/T25 definitions with new portability QA flags."""
    if footprint is None or footprint.is_empty or not footprint.is_valid:
        raise ValueError("Invalid footprint for building {}".format(bldg_id))
    local_20 = footprint.buffer(LOCAL_BUFFER_M)
    local_ring = local_20.difference(footprint)
    neighbourhood_ring = footprint.buffer(NEIGHBOURHOOD_BUFFER_M).difference(local_20)
    local = terrain_stats(src, local_ring, raster_extent)
    neighbourhood = terrain_stats(src, neighbourhood_ring, raster_extent)
    l50, n50, n25 = local["p50"], neighbourhood["p50"], neighbourhood["p25"]
    measured = bool(np.isfinite(l50) and np.isfinite(n50) and np.isfinite(n25))
    return {
        "bldg_id": bldg_id,
        "local_z_50": l50,
        "neighbourhood_z_50": n50,
        "neighbourhood_z_25": n25,
        "T50": l50 - n50,
        "T25": l50 - n25,
        "local_valid_pixels": local["valid_pixels"],
        "local_total_pixels": local["total_pixels"],
        "local_coverage": local["coverage"],
        "neighbourhood_valid_pixels": neighbourhood["valid_pixels"],
        "neighbourhood_total_pixels": neighbourhood["total_pixels"],
        "neighbourhood_coverage": neighbourhood["coverage"],
        "local_geometric_coverage": local["geometric_coverage"],
        "neighbourhood_geometric_coverage": neighbourhood["geometric_coverage"],
        "terrain_measured": measured,
    }


def load_buildings(path, config):
    """Read the verified Phase 3 population in a stable building-ID order."""
    buildings = gpd.read_file(str(path))
    if buildings.crs is None or buildings.crs.to_epsg() != config["epsg"]:
        raise ValueError("Unexpected building CRS: {}".format(buildings.crs))
    if len(buildings) != config["n_buildings"]:
        raise ValueError("Unexpected building count: {}".format(len(buildings)))
    if "bldg_id" not in buildings.columns:
        raise ValueError("Missing bldg_id")
    if buildings["bldg_id"].isna().any() or not buildings["bldg_id"].is_unique:
        raise ValueError("Missing or duplicate building identifiers")
    return buildings.sort_values("bldg_id", kind="mergesort").reset_index(drop=True)


def check_raster(src, config):
    """Validate the metric DTM CRS, including Rotterdam's RD New + NAP.

    Frozen RTM AHN5 uses EPSG:7415 (compound CRS): EPSG:28992 horizontal
    plus EPSG:5709 vertical. Pixel coordinates remain RD New metres.
    Accept that exact known compound CRS without changing/reprojecting the raster.
    Other cities retain strict horizontal CRS checks.
    """
    raster_epsg = src.crs.to_epsg() if src.crs is not None else None
    allowed_epsg = {config["epsg"]}
    if config["epsg"] == 28992:
        allowed_epsg.add(7415)  # Amersfoort / RD New + NAP height
    if raster_epsg not in allowed_epsg:
        raise ValueError(
            "Raster CRS mismatch: {} (EPSG {}); allowed EPSG {}".format(
                src.crs, raster_epsg, sorted(allowed_epsg)
            )
        )
    if raster_epsg == 7415:
        logging.info(
            "Accepting Rotterdam compound CRS EPSG:7415 "
            "(horizontal EPSG:28992 + NAP height EPSG:5709)"
        )
    if src.count != 1 or not np.allclose(src.res, (5.0, 5.0), rtol=0, atol=1e-8):
        raise ValueError("Expected single-band 5 m DTM")
    if src.nodata is None:
        raise ValueError("Raster NoData must be defined")
    if src.transform.b != 0 or src.transform.d != 0:
        raise ValueError("Rotated rasters are not supported")


def ensure_run_manifest(destination, city, buildings_path, mosaic_path):
    """Prevent silently reusing batches after inputs or settings change."""
    destination.mkdir(parents=True, exist_ok=True)
    manifest_path = destination / "extraction_run_manifest.json"
    identity = {
        "city": city,
        "buildings_file": str(buildings_path.resolve()),
        "buildings_sha256": sha256_file(buildings_path),
        "raster_file": str(mosaic_path.resolve()),
        "raster_sha256": sha256_file(mosaic_path),
        "script_sha256": sha256_file(Path(__file__)),
        "local_buffer_m": LOCAL_BUFFER_M,
        "neighbourhood_buffer_m": NEIGHBOURHOOD_BUFFER_M,
        "min_valid_pixels": MIN_VALID_PIXELS,
        "min_geometric_coverage": MIN_GEOMETRIC_COVERAGE,
        "batch_size": BATCH_SIZE,
    }
    if manifest_path.exists():
        prior = json.loads(manifest_path.read_text(encoding="utf-8"))
        prior_identity = {key: prior[key] for key in identity}
        if prior_identity != identity:
            raise RuntimeError(
                "Input/code/parameter change detected in resumable output. "
                "Start in a fresh output directory; do not mix runs."
            )
    else:
        if list(destination.glob("terrain_*.parquet")):
            raise RuntimeError("Existing batches without a manifest: refusing reuse")
        identity["created_at_utc"] = datetime.now(timezone.utc).isoformat()
        manifest_path.write_text(json.dumps(identity, indent=2), encoding="utf-8")
    return manifest_path


def process_batch(src, batch, start, end, destination, raster_extent):
    filename = "terrain_{:06d}_{:06d}.parquet".format(start, end - 1)
    output = destination / filename
    if output.exists():
        existing = pd.read_parquet(str(output))
        if (
            len(existing) == len(batch)
            and existing["bldg_id"].is_unique
            and existing["bldg_id"].tolist() == batch["bldg_id"].tolist()
        ):
            logging.info("Reusing validated batch: %s", filename)
            return
        raise RuntimeError("Corrupt or incompatible existing batch: {}".format(output))

    records = []
    for _, row in batch.iterrows():
        records.append(extract_building(src, row["bldg_id"], row.geometry, raster_extent))
    result = pd.DataFrame.from_records(records)
    if len(result) != len(batch) or not result["bldg_id"].is_unique:
        raise AssertionError("Unexpected batch output")
    temporary = output.with_suffix(".partial.parquet")
    result.to_parquet(str(temporary), index=False)
    temporary.replace(output)
    logging.info("Saved %s | measured %s/%s", filename, int(result.terrain_measured.sum()), len(result))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city", required=True, choices=sorted(CITY_CONFIG))
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--limit", type=int)
    selection.add_argument("--all", action="store_true")
    parser.add_argument("--raster", type=Path, default=None, help="Optional override after validated raster preparation")
    parser.add_argument("--output-dir", type=Path, default=None, help="Optional isolated output location")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    conf = CITY_CONFIG[args.city]
    buildings_path = ROOT / conf["buildings"]
    raster_path = args.raster if args.raster is not None else ROOT / conf["mosaic"]
    if not buildings_path.is_file() or not raster_path.is_file():
        raise FileNotFoundError("Missing buildings or DTM: {}, {}".format(buildings_path, raster_path))
    if not args.all and (args.limit is None or args.limit <= 0):
        parser.error("--limit must be positive")
    suffix = "terrain_batches" if args.all else "terrain_pilot"
    destination = args.output_dir or ROOT / conf["output_prefix"] / suffix
    buildings = load_buildings(buildings_path, conf)
    if not args.all:
        buildings = buildings.iloc[:args.limit].copy()
    if len(buildings) == 0:
        raise ValueError("No buildings selected")
    with rasterio.open(str(raster_path)) as src:
        check_raster(src, conf)
        raster_extent = box(*src.bounds)
        manifest = ensure_run_manifest(destination, args.city, buildings_path, raster_path)
        logging.info("M1-T %s: %s buildings | raster %s", args.city, len(buildings), raster_path.name)
        for start in range(0, len(buildings), BATCH_SIZE):
            end = min(start + BATCH_SIZE, len(buildings))
            process_batch(src, buildings.iloc[start:end], start, end, destination, raster_extent)
    logging.info("Complete | output %s | manifest %s", destination, manifest)


if __name__ == "__main__":
    main()
