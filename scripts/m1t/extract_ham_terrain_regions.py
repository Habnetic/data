"""Route Hamburg buildings to validated regional DGM5 mosaics.

Reuses extract_terrain.py:extract_building without changing any statistical
or geometric definitions. Designed for the Habnetic/data repository.

Commands (from Habnetic/resilient-housing-bayes):
    & ..\\data\\.venv\\Scripts\\python.exe ..\\data\\scripts\\m1t\\extract_ham_terrain_regions.py --mode pilot-mainland
    & ..\\data\\.venv\\Scripts\\python.exe ..\\data\\scripts\\m1t\\extract_ham_terrain_regions.py --mode pilot-boundary
    & ..\\data\\.venv\\Scripts\\python.exe ..\\data\\scripts\\m1t\\extract_ham_terrain_regions.py --mode pilot-western
    & ..\\data\\.venv\\Scripts\\python.exe ..\\data\\scripts\\m1t\\extract_ham_terrain_regions.py --mode all
"""

import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
import logging
from pathlib import Path
import platform
import subprocess
import sys

import geopandas as gpd
import pandas as pd
import rasterio
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[2]
CORE_FILE = Path(__file__).with_name("extract_terrain.py")
MAINLAND_RASTER = ROOT / "processed/HAM/derived/ham_dgm5_mainland_mosaic.tif"
WESTERN_RASTER = ROOT / "processed/HAM/derived/ham_dgm5_western_islands_mosaic.tif"
MAINLAND_SOURCE_IDS = ROOT / "processed/HAM/derived/ham_dgm5_mainland_mosaic_source_id.tif"
WESTERN_SOURCE_IDS = ROOT / "processed/HAM/derived/ham_dgm5_western_islands_mosaic_source_id.tif"
COVERAGE_CSV = ROOT / "runs/ham_m1_citywide/qa/ham_tile_coverage_candidates.csv"
OUTPUT_BASE = ROOT / "runs/ham_m1_citywide"
EXPECTED_POPULATION = 341530
LOGGER = logging.getLogger("habnetic.m1t.ham")


def file_sha256(path: Path) -> str:
    """Hash a file without loading it into RAM."""
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_core():
    """Load the existing frozen-definition extraction implementation."""
    if not CORE_FILE.is_file():
        raise FileNotFoundError(CORE_FILE)
    spec = importlib.util.spec_from_file_location("habnetic_m1t_shared", str(CORE_FILE))
    if spec is None or spec.loader is None:
        raise ImportError("Cannot import shared M1-T extractor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for symbol in ("CITY_CONFIG", "load_buildings", "check_raster", "extract_building"):
        if not hasattr(module, symbol):
            raise RuntimeError("Shared extractor missing: " + symbol)
    return module


def region_for_geometry(geom) -> str:
    """Select mainland or western source in the large gap between both areas."""
    if geom is None or geom.is_empty:
        raise ValueError("Missing building geometry")
    x = geom.centroid.x
    if x < 500000:
        return "western_islands"
    if x > 540000:
        return "mainland"
    raise ValueError("Building lies between the two documented Hamburg clusters")


def select_buildings(buildings: gpd.GeoDataFrame, mode: str, pilot_count: int) -> gpd.GeoDataFrame:
    """Deterministic pilots and population-preserving full selection."""
    if mode == "all":
        return buildings.copy()
    if mode == "pilot-mainland":
        mask = buildings.geometry.centroid.x > 540000
        result = buildings.loc[mask].head(pilot_count).copy()
    elif mode == "pilot-western":
        mask = buildings.geometry.centroid.x < 500000
        western = buildings.loc[mask]
        result = western.head(pilot_count).copy()
        # Make sure our Scharhoern control building is in this pilot.
        sch = western.loc[western["bldg_id"].astype(str) == "1"]
        if len(sch) != 1:
            raise ValueError("Scharhoern control building ID=1 was not found")
        if "1" not in set(result["bldg_id"].astype(str)):
            result = pd.concat([result.iloc[:-1], sch], axis=0)
    elif mode == "pilot-boundary":
        if not COVERAGE_CSV.is_file():
            raise FileNotFoundError(COVERAGE_CSV)
        qa = pd.read_csv(COVERAGE_CSV, dtype={"bldg_id": str})
        ids = set(qa.loc[qa["minimum_tile_coverage"] < 0.99, "bldg_id"])
        if len(ids) != 27:
            raise ValueError("Expected 27 boundary IDs; found {}".format(len(ids)))
        result = buildings.loc[buildings["bldg_id"].astype(str).isin(ids)].copy()
        if len(result) != 27:
            raise ValueError("Expected 27 selected boundary buildings, got {}".format(len(result)))
    else:
        raise ValueError("Unknown mode: " + mode)
    if result.empty:
        raise ValueError("Selection is empty")
    if result["bldg_id"].astype(str).duplicated().any():
        raise ValueError("Duplicate building identifiers in selection")
    return result


def verify_source_id_grid(elevation: rasterio.io.DatasetReader, source_ids: Path) -> None:
    """Check source provenance aligns with the elevation mosaic."""
    if not source_ids.is_file():
        raise FileNotFoundError(source_ids)
    with rasterio.open(source_ids) as src:
        if (src.crs != elevation.crs or src.transform != elevation.transform
                or src.width != elevation.width or src.height != elevation.height):
            raise ValueError("Source ID / elevation mosaic grid mismatch: " + str(source_ids))


def git_commit(root: Path) -> str:
    """Return source-repository commit, or an explicit unavailable marker."""
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            universal_newlines=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def run(mode: str, pilot_count: int, batch_size: int, output_dir=None) -> None:
    """Extract exactly the shared T50/T25 measures using two mosaics."""
    if pilot_count < 1 or batch_size < 1:
        raise ValueError("pilot-count and batch-size must be positive")

    core = load_core()
    conf = core.CITY_CONFIG["HAM"]
    buildings_path = ROOT / conf["buildings"]
    if not buildings_path.is_file():
        raise FileNotFoundError(buildings_path)
    LOGGER.info("Reading Hamburg buildings: %s", buildings_path)
    buildings = core.load_buildings(buildings_path, conf)
    if len(buildings) != EXPECTED_POPULATION:
        raise ValueError("Expected 341530 buildings, got {}".format(len(buildings)))
    if buildings.crs is None or buildings.crs.to_epsg() != 25832:
        raise ValueError("Unexpected building CRS: {}".format(buildings.crs))
    if buildings["bldg_id"].astype(str).duplicated().any():
        raise ValueError("Duplicated IDs in building source")

    selected = select_buildings(buildings, mode, pilot_count)
    destination = Path(output_dir) if output_dir else OUTPUT_BASE / (
        "terrain_batches" if mode == "all" else "terrain_" + mode.replace("-", "_")
    )
    destination.mkdir(parents=True, exist_ok=True)
    if list(destination.glob("terrain_*.parquet")) or (destination / "extraction_run_manifest.json").exists():
        raise FileExistsError(
            "Output already contains extraction results. Refusing to overwrite: " + str(destination)
        )

    raster_paths = {"mainland": MAINLAND_RASTER, "western_islands": WESTERN_RASTER}
    source_id_paths = {"mainland": MAINLAND_SOURCE_IDS, "western_islands": WESTERN_SOURCE_IDS}
    for region, path in raster_paths.items():
        if not path.is_file():
            raise FileNotFoundError("Missing {} elevation mosaic: {}".format(region, path))

    records_meta = []
    with ExitStack() as stack:
        rasters = {name: stack.enter_context(rasterio.open(path))
                   for name, path in raster_paths.items()}
        extents = {name: box(*src.bounds) for name, src in rasters.items()}
        for region, src in rasters.items():
            core.check_raster(src, conf)
            verify_source_id_grid(src, source_id_paths[region])

        LOGGER.info("M1-T HAM %s: %s buildings", mode, len(selected))
        for start in range(0, len(selected), batch_size):
            end = min(start + batch_size, len(selected))
            batch = selected.iloc[start:end]
            output_rows = []
            for _, row in batch.iterrows():
                region = region_for_geometry(row.geometry)
                if not extents[region].covers(row.geometry):
                    raise ValueError("Building outside selected mosaic: {}".format(row["bldg_id"]))
                result = core.extract_building(
                    rasters[region], row["bldg_id"], row.geometry, extents[region]
                )
                if not isinstance(result, dict):
                    raise TypeError("Shared extract_building must return a dictionary")
                result["terrain_region"] = region
                output_rows.append(result)
            out_path = destination / "terrain_{:06d}_{:06d}.parquet".format(start, end - 1)
            pd.DataFrame(output_rows).to_parquet(out_path, index=False)
            records_meta.append({
                "path": out_path.relative_to(ROOT).as_posix(),
                "start": start, "end_exclusive": end,
                "count": len(output_rows),
                "sha256": file_sha256(out_path),
            })
            LOGGER.info("Batch %s/%s saved: %s", end, len(selected), out_path.name)

    manifest = {
        "project": "Habnetic", "city": "HAM", "phase": "M1-T",
        "mode": mode, "created_utc": datetime.now(timezone.utc).isoformat(),
        "population": EXPECTED_POPULATION, "selected_buildings": len(selected),
        "selection_order": "Original validated building GeoPackage order; filters preserve order",
        "batch_size": batch_size,
        "method": "Reuse unmodified extract_terrain.py:extract_building for all rings and T50/T25",
        "source_repo_commit": git_commit(ROOT),
        "python_version": platform.python_version(),
        "geopandas_version": gpd.__version__,
        "pandas_version": pd.__version__,
        "rasterio_version": rasterio.__version__,
        "buildings": {"path": buildings_path.relative_to(ROOT).as_posix(),
                      "sha256": file_sha256(buildings_path)},
        "shared_extractor_sha256": file_sha256(CORE_FILE),
        "regional_router_sha256": file_sha256(Path(__file__).resolve()),
        "rasters": {
            region: {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": file_sha256(path),
                "source_id_path": source_id_paths[region].relative_to(ROOT).as_posix(),
                "source_id_sha256": file_sha256(source_id_paths[region]),
            }
            for region, path in raster_paths.items()
        },
        "source_attribution_note": "Per-pixel provider IDs remain in source_id mosaics; terrain_region identifies geographic mosaic only.",
        "outputs": records_meta,
    }
    manifest_path = destination / "extraction_run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("\nHAMBURG M1-T EXTRACTION:", mode.upper(), "PASS")
    print("Selected buildings:", len(selected))
    print("Batches:", len(records_meta))
    print("Output:", destination)
    print("Manifest:", manifest_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("pilot-mainland", "pilot-boundary", "pilot-western", "all"), required=True)
    parser.add_argument("--pilot-count", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run(args.mode, args.pilot_count, args.batch_size, args.output_dir)


if __name__ == "__main__":
    main()
