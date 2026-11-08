"""Build the Donostia M1-T 5 m DTM mosaic from official CNIG MDT05 sheets.

Run from any working directory:
    python scripts/m1t/build_don_mdt05_mosaic.py

Inputs: two previously acquired, immutable CNIG MDT05 sheets 0064/0040.
Outputs: clipped GeoTIFF mosaic, machine-readable manifest, provenance Markdown.

Scientific method: preserve elevation pixel values, 5 m grid, and source NoData.
The overlapping sheet 0064 has first priority; 0040 fills any NoData.
No resampling, interpolation, or geophysical correction is applied.
"""

import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
import logging
import math
from pathlib import Path
from typing import Dict, List, Tuple

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import raster_geometry_mask
from rasterio.merge import merge
from rasterio.windows import from_bounds
from shapely.geometry import mapping

DATA_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = DATA_ROOT / "raw" / "DON" / "terrain" / "cnig_mdt05"
SOURCE_NAMES = (
    "PNOA_MDT05_ETRS89_HU30_0064_LID.tif",
    "PNOA_MDT05_ETRS89_HU30_0040_LID.tif",
)
OUT_RASTER = DATA_ROOT / "processed" / "DON" / "derived" / "mdt05_don_5m_mosaic.tif"
OUT_MANIFEST = DATA_ROOT / "runs" / "don_m1_citywide" / "mdt05_mosaic_manifest.json"
OUT_PROVENANCE = DATA_ROOT / "docs" / "provenance" / "DON_MDT05_Mosaic.md"
BUILDINGS = DATA_ROOT / "processed" / "DON" / "derived" / "buildings_don.gpkg"

# The verified Phase 3 study-population bounding box plus 100 m.
AOI = (574351.982459101, 4785931.96049428, 589589.417160402, 4798637.86387985)
RES_M = 5.0
EXPECTED_CRS = 25830
EXPECTED_NODATA = -32767.0
TARGETED_IDS = {"198406", "200663", "196441"}
SOURCE_PAGE = "https://centrodedescargas.cnig.es/CentroDescargas/modelo-digital-terreno-mdt05-primera-cobertura"
ATTRIBUTION = "Obra derivada de MDT05-cob1 2008-2015 CC-BY 4.0 scne.es"
LOG = logging.getLogger("habnetic.m1t.don")


def sha256_file(path: Path) -> str:
    """Compute file integrity hash without loading the file into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snap_outward(bounds: Tuple[float, float, float, float],
                 x_origin: float, y_origin: float,
                 resolution: float = RES_M) -> Tuple[float, float, float, float]:
    """Expand bounds outward onto an existing north-up raster grid."""
    west, south, east, north = bounds
    left = x_origin + math.floor((west - x_origin) / resolution) * resolution
    right = x_origin + math.ceil((east - x_origin) / resolution) * resolution
    top = y_origin - math.floor((y_origin - north) / resolution) * resolution
    bottom = y_origin - math.ceil((y_origin - south) / resolution) * resolution
    return (left, bottom, right, top)


def validate_sources(sources) -> None:
    """Reject incompatible CRS, grid, resolution, bands, or NoData."""
    reference = sources[0]
    if reference.crs is None or reference.crs.to_epsg() != EXPECTED_CRS:
        raise ValueError("Source CRS is not EPSG:25830")

    for src in sources:
        if src.crs != reference.crs:
            raise ValueError("Input CRS mismatch")
        if src.count != 1:
            raise ValueError("Expected single-band terrain raster")
        if not np.allclose(src.res, (RES_M, RES_M)):
            raise ValueError("Unexpected pixel resolution")
        if not (abs(src.transform.b) < 1e-12 and abs(src.transform.d) < 1e-12
                and np.isclose(src.transform.a, RES_M)
                and np.isclose(src.transform.e, -RES_M)):
            raise ValueError("Expected north-up 5 m grid")
        if src.nodata != EXPECTED_NODATA:
            raise ValueError("Unexpected NoData; investigate source before mosaicking")
        if not np.issubdtype(np.dtype(src.dtypes[0]), np.floating):
            raise ValueError("Elevation raster is not floating-point")
        offsets = (
            (src.transform.c - reference.transform.c) / RES_M,
            (src.transform.f - reference.transform.f) / RES_M,
        )
        if any(abs(value - round(value)) > 1e-6 for value in offsets):
            raise ValueError("Input rasters are not on the same pixel grid")
        LOG.info("Source validated: %s | %s | %s | %s", Path(src.name).name,
                 src.crs, src.res, src.bounds)


def overlapping_cell_qa(sources) -> Dict[str, float]:
    """Quantify elevation agreement where the two source tiles overlap."""
    a, b = sources
    bounds = (
        max(a.bounds.left, b.bounds.left),
        max(a.bounds.bottom, b.bounds.bottom),
        min(a.bounds.right, b.bounds.right),
        min(a.bounds.top, b.bounds.top),
    )
    if bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
        return {"overlap_valid_comparisons": 0, "note": "no overlap"}

    arrays = []
    for src in sources:
        window = from_bounds(*bounds, transform=src.transform)
        window = window.round_offsets().round_lengths()
        arrays.append(src.read(1, window=window, masked=True))
    if arrays[0].shape != arrays[1].shape:
        raise ValueError("Overlap windows have mismatched shapes")

    valid = (
        ~np.ma.getmaskarray(arrays[0]) &
        ~np.ma.getmaskarray(arrays[1]) &
        np.isfinite(arrays[0].data) &
        np.isfinite(arrays[1].data)
    )
    difference = np.abs(arrays[0].data[valid].astype(float)
                        - arrays[1].data[valid].astype(float))
    stats = {
        "overlap_bounds": list(bounds),
        "overlap_valid_comparisons": int(difference.size),
    }
    if difference.size:
        stats.update({
            "absolute_difference_median_m": float(np.median(difference)),
            "absolute_difference_p95_m": float(np.percentile(difference, 95)),
            "absolute_difference_max_m": float(np.max(difference)),
            "fraction_over_0p5m": float(np.mean(difference > 0.5)),
            "fraction_over_1m": float(np.mean(difference > 1.0)),
        })
    return stats


def targeted_ring_qa(raster_path: Path) -> List[Dict[str, object]]:
    """Verify valid elevation data for three original boundary buildings."""
    gdf = gpd.read_file(BUILDINGS)
    subset = gdf[gdf["bldg_id"].astype(str).isin(TARGETED_IDS)]
    if len(subset) != 3 or gdf["bldg_id"].duplicated().any():
        raise ValueError("Expected unique IDs for three targeted buildings")

    result = []
    with rasterio.open(raster_path) as src:
        if src.crs != gdf.crs:
            raise ValueError("Buildings and mosaic CRS differ")
        for _, building in subset.iterrows():
            footprint = building.geometry
            local20 = footprint.buffer(20)
            rings = {
                "local": local20.difference(footprint),
                "neighbourhood": footprint.buffer(100).difference(local20),
            }
            for name, ring in rings.items():
                outside, _, window = raster_geometry_mask(
                    src, [mapping(ring)], crop=True
                )
                data = src.read(1, window=window, masked=True)
                inside = ~outside
                valid = (
                    inside & ~np.ma.getmaskarray(data) &
                    np.isfinite(data.data)
                )
                count = int(valid.sum())
                total = int(inside.sum())
                result.append({
                    "bldg_id": str(building["bldg_id"]),
                    "ring": name,
                    "valid_pixels": count,
                    "pixels_in_ring": total,
                    "valid_fraction": count / total if total else 0.0,
                })
                if count < 20 or count != total:
                    raise ValueError(
                        "Incomplete targeted ring after merge: {} {} ({}/{})"
                        .format(building["bldg_id"], name, count, total)
                    )
    return result


def create_mosaic(output: Path, sources, bounds) -> Dict[str, object]:
    """Write an AOI-clipped, tiled GeoTIFF without changing elevation values."""
    if output.exists():
        raise FileExistsError("Refusing to overwrite existing mosaic: {}".format(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".partial.tif")
    if temporary.exists():
        raise FileExistsError("Partial mosaic exists; investigate before retry: {}".format(temporary))

    merged, transform = merge(
        sources, bounds=bounds, res=(RES_M, RES_M),
        nodata=EXPECTED_NODATA, method="first"
    )
    if merged.shape[0] != 1 or merged.dtype != np.dtype("float32"):
        raise ValueError("Unexpected merged raster shape or dtype")

    pixels = merged[0]
    valid = np.isfinite(pixels) & (pixels != EXPECTED_NODATA)
    profile = {
        "driver": "GTiff", "width": pixels.shape[1],
        "height": pixels.shape[0], "count": 1,
        "dtype": "float32", "crs": sources[0].crs,
        "transform": transform, "nodata": EXPECTED_NODATA,
        "tiled": True, "blockxsize": 256, "blockysize": 256,
        "compress": "deflate", "predictor": 3, "BIGTIFF": "IF_SAFER",
    }
    try:
        with rasterio.open(temporary, "w", **profile) as dst:
            dst.write(merged)
            dst.update_tags(
                provider="IGN / CNIG", product="MDT05 first coverage",
                attribution=ATTRIBUTION,
                source_sheets="0064 first, 0040 second",
                operations="aligned grid, AOI crop, first-valid merge; no interpolation",
            )
        with rasterio.open(temporary) as result:
            if result.crs != sources[0].crs or result.count != 1:
                raise ValueError("Written raster metadata mismatch")
            if not np.allclose(result.res, (RES_M, RES_M)):
                raise ValueError("Written raster has wrong resolution")
            if result.nodata != EXPECTED_NODATA:
                raise ValueError("Written raster NoData mismatch")
            if tuple(result.bounds) != tuple(bounds):
                raise ValueError("Written raster bounds mismatch")
        qa = targeted_ring_qa(temporary)
        temporary.replace(output)
    finally:
        if temporary.exists():
            temporary.unlink()
    return {
        "bounds": list(bounds),
        "width": int(pixels.shape[1]),
        "height": int(pixels.shape[0]),
        "nodata": EXPECTED_NODATA,
        "valid_pixel_fraction_in_bounding_rectangle": float(np.mean(valid)),
        "targeted_building_qa": qa,
    }


def write_metadata(manifest: Dict[str, object]) -> None:
    OUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    OUT_PROVENANCE.parent.mkdir(parents=True, exist_ok=True)
    OUT_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    seam = manifest["seam_qa"]
    text = """# Donostia | M1-T MDT05 mosaic provenance

- **Status:** AOI-clipped mosaic built; full citywide per-building pixel QA pending.
- **Generated (UTC):** {generated}
- **Provider:** Instituto Geografico Nacional / Centro Nacional de Informacion Geografica (IGN/CNIG).
- **Dataset:** MDT05 first coverage, 5 m, ETRS89 UTM zone 30N (EPSG:25830).
- **Source catalogue:** {source_page}
- **Source sheets, merge priority:** 0064 then 0040.
- **Year listed in catalogue:** 2012 for both sheets (source-vintage metadata; not acquisition date).
- **Licence / attribution for derived product:** {attribution}
- **Operations:** Extracted 5 m cells over the buffered Phase 3 study rectangle; preserved source values and NoData (-32767); no resampling or gap filling. First valid pixel takes priority in overlaps.
- **Mosaic:** `processed/DON/derived/mdt05_don_5m_mosaic.tif`
- **Mosaic SHA-256:** `{mosaic_hash}`
- **Source 0064 SHA-256:** `{source0}`
- **Source 0040 SHA-256:** `{source1}`
- **Overlapping valid-cell comparisons:** {overlap_count}
- **Median absolute overlap difference (m):** {overlap_median}
- **Max absolute overlap difference (m):** {overlap_max}
- **Three original edge buildings:** All six targeted terrain rings contain valid elevation pixels. This does **not** establish full citywide valid-pixel coverage or source accuracy over water.
- **Machine-readable report:** `runs/don_m1_citywide/mdt05_mosaic_manifest.json`
- **Acquisition log:** `runs/don_m1_citywide/mdt05_source_manifest.json` and `docs/provenance/DON_MDT05_Source.md`.

**Caution:** Topographic measurements remain descriptive features from an older lidar-derived DTM. Coastal interpolated surfaces and disagreements between tile vintages can limit reliability. The frozen Rotterdam scientific definitions are unchanged.
""".format(
        generated=manifest["timestamp_utc"],
        source_page=SOURCE_PAGE, attribution=ATTRIBUTION,
        mosaic_hash=manifest["output"]["sha256"],
        source0=manifest["sources"][0]["sha256"],
        source1=manifest["sources"][1]["sha256"],
        overlap_count=seam.get("overlap_valid_comparisons"),
        overlap_median=seam.get("absolute_difference_median_m", "N/A"),
        overlap_max=seam.get("absolute_difference_max_m", "N/A"),
    )
    OUT_PROVENANCE.write_text(text, encoding="utf-8")


def main() -> None:
    """Validate two MDT05 tiles, create clipped mosaic and provenance."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inspect-only", action="store_true",
                        help="Validate source metadata and overlap without writing mosaic")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    paths = [SRC_DIR / name for name in SOURCE_NAMES]
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)

    with ExitStack() as stack:
        sources = [stack.enter_context(rasterio.open(p)) for p in paths]
        validate_sources(sources)
        bounds = snap_outward(AOI, sources[0].transform.c, sources[0].transform.f)
        for x, y in ((AOI[0], AOI[1]), (AOI[2], AOI[3])):
            if not (bounds[0] <= x <= bounds[2] and bounds[1] <= y <= bounds[3]):
                raise AssertionError("Clipped mosaic bounds do not cover AOI")
        for i in range(2):
            src = sources[i]
            LOG.info("Input %s: nodata=%s, dtype=%s, bounds=%s",
                     i + 1, src.nodata, src.dtypes[0], src.bounds)
        seam = overlapping_cell_qa(sources)
        LOG.info("Seam comparison: %s", seam)
        if seam.get("fraction_over_1m", 0) > 0.01:
            LOG.warning("More than 1%% of overlapping pixels disagree by >1m; review seam")
        LOG.info("Buffered AOI: %s; snapped mosaic bounds: %s", AOI, bounds)
        if args.inspect_only:
            LOG.info("Inspect-only successful. No outputs written")
            return
        detail = create_mosaic(OUT_RASTER, sources, bounds)

    manifest = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "study_area": "DON",
        "crs": "EPSG:25830",
        "resolution_m": RES_M,
        "source_catalogue": SOURCE_PAGE,
        "attribution": ATTRIBUTION,
        "sources": [
            {"path": str(p.relative_to(DATA_ROOT)),
             "size_bytes": p.stat().st_size, "sha256": sha256_file(p)}
            for p in paths
        ],
        "seam_qa": seam,
        "output": {
            "path": str(OUT_RASTER.relative_to(DATA_ROOT)),
            "size_bytes": OUT_RASTER.stat().st_size,
            "sha256": sha256_file(OUT_RASTER),
            **detail,
        },
        "scientific_scope": "terrain preprocessing only; building-wide pixel QA still pending",
    }
    write_metadata(manifest)
    LOG.info("Mosaic created: %s", OUT_RASTER)
    LOG.info("Mosaic SHA-256: %s", manifest["output"]["sha256"])
    LOG.info("Targeted ring checks: %s", detail["targeted_building_qa"])
    LOG.info("Manifest: %s", OUT_MANIFEST)
    LOG.info("Provenance: %s", OUT_PROVENANCE)


if __name__ == "__main__":
    main()
