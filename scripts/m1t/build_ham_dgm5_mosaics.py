"""Build auditable Hamburg M1-T 5 m mosaics from the frozen 884-tile preparation.

Version 0.1.1: reconcile known LGV and neighbouring-state overlapping footprints.
Per cell prefer valid Hamburg LGV elevations; fill LGV nodata with valid
Schleswig-Holstein or Niedersachsen elevations. Preserve per-pixel provenance.

Run from anywhere:
  python scripts/m1t/build_ham_dgm5_mosaics.py --inspect-only
  python scripts/m1t/build_ham_dgm5_mosaics.py

Elevation, valid-source-pixel fraction and source ID are stored separately.
Never overwrite an existing output unless --force is explicitly supplied.
"""

import argparse
import hashlib
import json
from collections import Counter
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.windows import Window

RESOLUTION = 5.0
TILE_METRES = 1000
SOURCE_IDS = {
    "LGV_HH_2022": 1,
    "LVERMGEO_SH_2021": 2,
    "LGLN_NI_2025": 3,
    "WSV_DGMW_2022_SCHARHOERN": 4,
}
SOURCE_NAMES = {value: key for key, value in SOURCE_IDS.items()}
MANIFEST = "runs/ham_m1_citywide/qa/ham_dgm5_citywide_manifest.json"
OUTPUT_ROOT = "processed/HAM/derived"


@dataclass(frozen=True)
class Tile:
    elevation: Path
    fraction: Path
    provenance: str
    bounds: Tuple[int, int, int, int]
    width: int
    height: int
    region: str
    original_manifest_entry: dict


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def grid_coord(value: float, resolution: int) -> int:
    rounded = round(value)
    if abs(value - rounded) > 0.01 or rounded % resolution:
        raise ValueError("Not aligned to {} m grid: {}".format(resolution, value))
    return rounded


def inspect_tiles(root: Path, entries: list) -> Dict[str, List[Tile]]:
    """Validate input grid geometry and source IDs without reading full rasters."""
    regions = {"mainland": [], "western_islands": []}
    footprints = {}
    filenames = set()
    for entry in entries:
        provenance = entry.get("source")
        if provenance not in SOURCE_IDS:
            raise ValueError("Unknown source identity: {}".format(provenance))
        elevation = root / entry["elevation_path"]
        fraction = root / entry["fraction_path"]
        if not elevation.is_file() or not fraction.is_file():
            raise FileNotFoundError("Missing elevation or fraction raster: {}".format(elevation))
        if elevation in filenames:
            raise ValueError("Repeated elevation path: {}".format(elevation))
        filenames.add(elevation)
        with rasterio.open(elevation) as src, rasterio.open(fraction) as valid:
            if (src.crs is None or src.crs.to_epsg() != 25832 or
                    valid.crs is None or valid.crs.to_epsg() != 25832):
                raise ValueError("Unexpected CRS: {}".format(elevation.name))
            if (src.count != 1 or valid.count != 1 or
                    src.res != (5.0, 5.0) or valid.res != (5.0, 5.0) or
                    src.transform != valid.transform or
                    (src.width, src.height) != (valid.width, valid.height)):
                raise ValueError("Grid mismatch: {}".format(elevation.name))
            if src.nodata != -9999.0 or src.dtypes[0] != "float32":
                raise ValueError("Invalid elevation specification: {}".format(elevation.name))
            if valid.dtypes[0] != "float32":
                raise ValueError("Invalid valid-fraction datatype: {}".format(fraction.name))
            left = grid_coord(src.bounds.left, TILE_METRES)
            bottom = grid_coord(src.bounds.bottom, TILE_METRES)
            right = grid_coord(src.bounds.right, TILE_METRES)
            top = grid_coord(src.bounds.top, TILE_METRES)
            if right - left != TILE_METRES or top - bottom != TILE_METRES:
                raise ValueError("Expected an aligned 1-km tile: {}".format(elevation.name))
            if src.width != 200 or src.height != 200:
                raise ValueError("Expected 200x200 cells at 5 m: {}".format(elevation.name))
            region = "western_islands" if right <= 500000 else "mainland"
            if left < 500000 < right:
                raise ValueError("Tile crosses the western/mainland split")
            if provenance == "WSV_DGMW_2022_SCHARHOERN" and region != "western_islands":
                raise ValueError("WSV Scharhoern tile assigned to mainland")
            if provenance in ("LVERMGEO_SH_2021", "LGLN_NI_2025") and region != "mainland":
                raise ValueError("Supplementary mainland tile assigned west")
            key = (left, bottom)
            previous = footprints.setdefault(key, set())
            if provenance in previous:
                raise ValueError("Duplicate same-source footprint at {}: {}".format(key, provenance))
            combined = previous | {provenance}
            allowed_overlaps = (
                {"LGV_HH_2022", "LVERMGEO_SH_2021"},
                {"LGV_HH_2022", "LGLN_NI_2025"},
            )
            if len(combined) > 1 and combined not in allowed_overlaps:
                raise ValueError("Unapproved overlapping source footprints at {}: {}".format(key, sorted(combined)))
            previous.add(provenance)
            regions[region].append(Tile(
                elevation=elevation, fraction=fraction, provenance=provenance,
                bounds=(left, bottom, right, top), width=200, height=200,
                region=region, original_manifest_entry=entry))
    if not all(regions.values()):
        raise ValueError("Both mainland and western island regions must be present")
    for tiles in regions.values():
        tiles.sort(key=lambda t: (t.bounds[0], t.bounds[1]))
    return regions


def region_bounds(tiles: List[Tile]) -> Tuple[int, int, int, int]:
    return (min(t.bounds[0] for t in tiles), min(t.bounds[1] for t in tiles),
            max(t.bounds[2] for t in tiles), max(t.bounds[3] for t in tiles))


def filenames(output_root: Path, region: str) -> dict:
    prefix = output_root / ("ham_dgm5_{}_mosaic".format(region))
    return {
        "elevation": prefix.with_suffix(".tif"),
        "valid_fraction": prefix.with_name(prefix.name + "_valid_fraction.tif"),
        "source_id": prefix.with_name(prefix.name + "_source_id.tif"),
    }


def output_profile(region_box: tuple, dtype: str, nodata, predictor: int):
    left, bottom, right, top = region_box
    return dict(
        driver="GTiff", width=(right - left) // 5, height=(top - bottom) // 5,
        count=1, crs="EPSG:25832", transform=from_origin(left, top, 5, 5),
        dtype=dtype, nodata=nodata, compress="deflate", predictor=predictor,
        tiled=True, blockxsize=256, blockysize=256, BIGTIFF="IF_SAFER",
    )


def initialize(dst, fill, dtype, chunk_rows=256):
    for row in range(0, dst.height, chunk_rows):
        height = min(chunk_rows, dst.height - row)
        dst.write(np.full((height, dst.width), fill, dtype=dtype), 1,
                  window=Window(0, row, dst.width, height))


def load_cell_values(tile: Tile) -> Tuple[np.ndarray, np.ndarray]:
    with rasterio.open(tile.elevation) as src, rasterio.open(tile.fraction) as fsrc:
        elevation = src.read(1)
        fraction = fsrc.read(1)
    if not np.isfinite(elevation).all() or not np.isfinite(fraction).all():
        raise ValueError("Nonfinite 5m grid values: {}".format(tile.elevation.name))
    if np.any((fraction < 0) | (fraction > 1)):
        raise ValueError("Invalid native-source fractions: {}".format(tile.elevation.name))
    good = elevation != -9999.0
    if np.any(good != (fraction == 1.0)):
        raise ValueError("Strict aggregation inconsistency: {}".format(tile.elevation.name))
    if good.any() and (elevation[good].min() < -1000 or elevation[good].max() > 2000):
        raise ValueError("Suspicious accepted elevation: {}".format(tile.elevation.name))
    return elevation, fraction


def combine_footprint(tiles: List[Tile]):
    """Compose coincident tiles by valid-pixel preference, retaining source IDs.

    The Hamburg LGV source is first preference where its 5 m elevation is
    valid. Supplementary sources only supply a value where the preferred
    source has no accepted elevation. An invalid cell retains the provider
    with the highest source-valid fraction (metadata only, no imputation).
    """
    tiles = sorted(tiles, key=lambda t: SOURCE_IDS[t.provenance])
    selected_elev = np.full((200, 200), -9999.0, dtype="float32")
    selected_fraction = np.zeros((200, 200), dtype="float32")
    selected_source = np.zeros((200, 200), dtype="uint8")
    filled_from_secondary = 0
    pairwise = []
    for i, tile in enumerate(tiles):
        elevation, fraction = load_cell_values(tile)
        good = elevation != -9999.0
        existing_good = selected_elev != -9999.0
        if i == 0:
            selected_elev[:] = elevation
            selected_fraction[:] = fraction
            selected_source[:] = SOURCE_IDS[tile.provenance]
            continue
        both_valid = good & existing_good
        if both_valid.any():
            differences = np.abs(elevation[both_valid].astype("float64") -
                                 selected_elev[both_valid].astype("float64"))
            pairwise.append({
                "base_source": SOURCE_NAMES[int(selected_source[both_valid][0])],
                "supplementary_source": tile.provenance,
                "both_valid_cells": int(both_valid.sum()),
                "median_abs_difference_m": float(np.median(differences)),
                "p95_abs_difference_m": float(np.percentile(differences, 95)),
                "max_abs_difference_m": float(np.max(differences)),
            })
        fill = good & ~existing_good
        selected_elev[fill] = elevation[fill]
        selected_fraction[fill] = fraction[fill]
        selected_source[fill] = SOURCE_IDS[tile.provenance]
        filled_from_secondary += int(fill.sum())
        # Still-invalid cells carry their best measured source-valid fraction.
        remain_invalid = (selected_elev == -9999.0)
        better_fraction = remain_invalid & (fraction > selected_fraction)
        selected_fraction[better_fraction] = fraction[better_fraction]
        selected_source[better_fraction] = SOURCE_IDS[tile.provenance]
    if np.any((selected_elev != -9999.0) != (selected_fraction == 1.0)):
        raise RuntimeError("Overlapping footprint violates strict 25/25 aggregation")
    return selected_elev, selected_fraction, selected_source, filled_from_secondary, pairwise


def build_region(tiles: List[Tile], output_paths: dict, overwrite: bool = False) -> dict:
    box = region_bounds(tiles)
    for path in output_paths.values():
        if path.exists() and not overwrite:
            raise FileExistsError("Output exists (use --force): {}".format(path))
        path.parent.mkdir(parents=True, exist_ok=True)
    by_footprint = {}
    for tile in tiles:
        by_footprint.setdefault((tile.bounds[0], tile.bounds[1]), []).append(tile)
    overlaps = [k for k, group in by_footprint.items() if len(group) > 1]
    cell_counts = Counter()
    valid_counts = Counter()
    overlap_records = []
    with ExitStack() as stack:
        elev_dst = stack.enter_context(rasterio.open(
            output_paths["elevation"], "w", **output_profile(box, "float32", -9999.0, 3)))
        frac_dst = stack.enter_context(rasterio.open(
            output_paths["valid_fraction"], "w", **output_profile(box, "float32", None, 3)))
        src_dst = stack.enter_context(rasterio.open(
            output_paths["source_id"], "w", **output_profile(box, "uint8", 0, 2)))
        initialize(elev_dst, -9999.0, "float32")
        initialize(frac_dst, 0.0, "float32")
        initialize(src_dst, 0, "uint8")
        for i, (key, group) in enumerate(sorted(by_footprint.items()), 1):
            elevation, fraction, source_ids, filled, comparisons = combine_footprint(group)
            left, bottom = key
            top = bottom + TILE_METRES
            x = (left - box[0]) // 5
            y = (box[3] - top) // 5
            window = Window(x, y, 200, 200)
            elev_dst.write(elevation, 1, window=window)
            frac_dst.write(fraction, 1, window=window)
            src_dst.write(source_ids, 1, window=window)
            if len(group) > 1:
                overlap_records.append({
                    "footprint_lower_left_epsg25832": [left, bottom],
                    "source_priority_order": [t.provenance for t in sorted(group, key=lambda t: SOURCE_IDS[t.provenance])],
                    "supplementary_valid_cells_used": filled,
                    "both_valid_comparisons": comparisons,
                })
            for source_id in np.unique(source_ids):
                if source_id == 0:
                    continue
                label = SOURCE_NAMES[int(source_id)]
                selection = source_ids == source_id
                cell_counts[label] += int(selection.sum())
                valid_counts[label] += int((selection & (elevation != -9999.0)).sum())
            if i % 100 == 0:
                print("  {}: {:,}/{:,} unique source footprints".format(
                    tiles[0].region, i, len(by_footprint)))
    # Independently inspect the completed mosaic for invalid source assignment.
    actual_source = Counter()
    actual_valid = Counter()
    with rasterio.open(output_paths["elevation"]) as elev, rasterio.open(
            output_paths["valid_fraction"]) as frac, rasterio.open(
            output_paths["source_id"]) as src:
        for row in range(0, src.height, 256):
            height = min(256, src.height - row)
            window = Window(0, row, src.width, height)
            ids = src.read(1, window=window)
            values = elev.read(1, window=window)
            fractions = frac.read(1, window=window)
            if np.any((ids == 0) & (values != -9999.0)):
                raise RuntimeError("Elevation exists outside source coverage")
            if np.any((values != -9999.0) != (fractions == 1.0)):
                raise RuntimeError("Mosaic strict elevation/valid-fraction mismatch")
            if not np.isfinite(fractions).all() or np.any((fractions < 0) | (fractions > 1)):
                raise RuntimeError("Invalid source validity fractions in mosaic")
            for source_id in np.unique(ids):
                if source_id == 0:
                    continue
                if int(source_id) not in SOURCE_NAMES:
                    raise RuntimeError("Unknown source ID in output")
                label = SOURCE_NAMES[int(source_id)]
                selected = ids == source_id
                actual_source[label] += int(selected.sum())
                actual_valid[label] += int((selected & (values != -9999.0)).sum())
    if cell_counts != actual_source or valid_counts != actual_valid:
        raise RuntimeError("Mosaic cell inventory differs from input tile composition")
    files = {name: {"path": str(path), "sha256": sha256(path),
                    "size_bytes": path.stat().st_size}
             for name, path in output_paths.items()}
    return dict(bounds_epsg25832=list(box), width=(box[2] - box[0]) // 5,
                height=(box[3] - box[1]) // 5,
                tile_count=len(tiles), unique_footprints=len(by_footprint),
                overlapping_footprints=len(overlaps), overlap_resolution=overlap_records,
                source_tiles=dict(Counter(t.provenance for t in tiles)),
                source_cells=dict(cell_counts), valid_elevation_cells=dict(valid_counts),
                files=files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspect-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    manifest_path = root / MANIFEST
    data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    entries = data["tiles"]
    expected_sources = {
        "LGV_HH_2022": 880,
        "LVERMGEO_SH_2021": 2,
        "LGLN_NI_2025": 1,
        "WSV_DGMW_2022_SCHARHOERN": 1,
    }
    observed_sources = dict(Counter(r.get("source") for r in entries))
    if len(entries) != 884 or observed_sources != expected_sources:
        raise ValueError("Unexpected source inventory: {}".format(observed_sources))
    if data.get("target_resolution_m") != 5 or "1.0" not in data.get("acceptance_rule", ""):
        raise ValueError("Expected strict 5m input manifest (native fraction >= 1.0)")
    regions = inspect_tiles(root, entries)
    all_paths = {region: filenames(root / OUTPUT_ROOT, region) for region in regions}
    print("\nHAMBURG M1-T MOSAIC INVENTORY")
    print("Source entries:", len(entries))
    for region, tiles in regions.items():
        footprint_counts = Counter((t.bounds[0], t.bounds[1]) for t in tiles)
        overlap_sites = [key for key, count in footprint_counts.items() if count > 1]
        print(region, "tiles:", len(tiles), "unique footprints:", len(footprint_counts),
              "overlap footprints:", len(overlap_sites),
              "bounds:", region_bounds(tiles),
              "sources:", dict(Counter(t.provenance for t in tiles)))
        for key in sorted(overlap_sites):
            overlapping = [t for t in tiles if (t.bounds[0], t.bounds[1]) == key]
            providers = [t.provenance for t in overlapping]
            print("  shared source footprint:", key, "providers:", providers)
            if args.inspect_only:
                _, _, selected, supplemented, comparisons = combine_footprint(overlapping)
                counts = {SOURCE_NAMES[int(v)]: int((selected == v).sum())
                          for v in np.unique(selected) if v != 0}
                print("    selected 5m source-cell counts:", counts,
                      "supplementary accepted fills:", supplemented)
                for item in comparisons:
                    print("    both-valid comparison:", item)
    if args.inspect_only:
        print("\nREAD-ONLY MOSAIC INSPECTION: PASS")
        return
    for region, paths in all_paths.items():
        for path in paths.values():
            if path.exists() and not args.force:
                raise FileExistsError("Output exists (use --force): {}".format(path))
    results = {}
    for region, tiles in regions.items():
        print("\nBuilding", region, "mosaic ...")
        results[region] = build_region(tiles, all_paths[region], overwrite=args.force)
    # Simplify absolute paths in persisted machine-readable report.
    for result in results.values():
        for item in result["files"].values():
            item["path"] = Path(item["path"]).relative_to(root).as_posix()
    output = root / "runs/ham_m1_citywide/qa/ham_dgm5_mosaic_manifest.json"
    if output.exists() and not args.force:
        raise FileExistsError("Mosaic manifest already exists: {}".format(output))
    result = dict(city="HAM", phase="M1-T", created_utc=datetime.now(
        timezone.utc).isoformat(), source_manifest=MANIFEST,
        source_manifest_sha256=sha256(manifest_path),
        source_id_meanings={str(k): v for k, v in SOURCE_NAMES.items()},
        mosaic_rule=("Merge approved LGV/SH or LGV/NI overlapping 1-km tiles at 5-m cell level: "
                     "valid LGV takes precedence; supplementary fills LGV nodata; "
                     "invalid cells retain best source-valid fraction; per-cell provider ID is recorded"),
        elevation_nodata=-9999.0, valid_fraction_unknown_outside_tile=0.0,
        horizontal_crs="EPSG:25832", target_resolution_m=5,
        strict_native_1m_valid_fraction=1.0, regions=results)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("\nHAMBURG DGM5 MOSAICS: PASS")
    print("Mosaic regions:", len(results))
    print("Manifest:", output)


if __name__ == "__main__":
    main()
