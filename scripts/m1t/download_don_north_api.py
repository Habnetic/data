#!/usr/bin/env python3
"""Download an official 5 m CNIG/IDEE MDT05 north-edge patch for DON M1-T.

The source is the Spanish National Cartographic System OGC API-Coverages
collection EL.ElevationGridCoverage_25830_5_PB (first LiDAR coverage).

This is a DIFFERENT download distribution from the existing 0064 CNIG sheet.
It is preserved separately and never silently substituted for the sheet.

Python 3.8+ with rasterio, numpy, geopandas, shapely.
Run from any working directory; paths derive from this file's location.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import logging
from math import ceil, floor
from pathlib import Path
import shutil
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import geometry_mask
from rasterio.merge import merge
from shapely.geometry import box, mapping
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
BASE_RASTER = ROOT / "raw/DON/terrain/cnig_mdt05/PNOA_MDT05_ETRS89_HU30_0064_LID.tif"
TARGET_DIR = ROOT / "raw/DON/terrain/cnig_mdt05_api"
TARGET_FILE = TARGET_DIR / "DON_MDT05_north_ogc_25830_5m.tif"
RUN_DIR = ROOT / "runs/don_m1_citywide"
REPORT_JSON = RUN_DIR / "mdt05_north_api_source_manifest.json"
EVENT_JSONL = RUN_DIR / "mdt05_north_api_acquisitions.jsonl"
PROVENANCE_MD = ROOT / "docs/provenance/DON_MDT05_North_API.md"
BUILDINGS = ROOT / "processed/DON/derived/buildings_don.gpkg"
COLLECTION = "EL.ElevationGridCoverage_25830_5_PB"
API = "https://api-coverages.idee.es/collections/{}/coverage".format(COLLECTION)
CRS_URI = "http://www.opengis.net/def/crs/EPSG/0/25830"
AOI = (574351.982459101, 4785931.96049428, 589589.417160402, 4798637.86387985)
TARGET_IDS = {"198406", "200663", "196441"}
ATTRIBUTION = "Obra derivada de MDT05-cob1 2008-2015 CC-BY 4.0 scne.es"
LOG = logging.getLogger("habnetic.m1t.don.north")


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(2 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def requested_bbox(ref):
    """A small north strip, with margins, aligned to the 0064 pixel grid."""
    size = 5.0
    left = ref.bounds.left + floor((AOI[0] - ref.bounds.left) / size) * size - 50.0
    right = ref.bounds.left + ceil((AOI[2] - ref.bounds.left) / size) * size + 50.0
    bottom = ref.bounds.top - 50.0
    top = ref.bounds.top + ceil((AOI[3] - ref.bounds.top) / size) * size + 50.0
    assert top > bottom and right > left
    return tuple(round(v, 3) for v in (left, bottom, right, top))


def build_url(bbox):
    params = {
        "bbox": ",".join(str(v) for v in bbox),
        "bbox-crs": CRS_URI,
        "crs": CRS_URI,
        "f": "COG",
    }
    return API + "?" + urlencode(params)


def raster_metadata(src):
    return {
        "crs": str(src.crs),
        "resolution_m": list(src.res),
        "bounds": [float(v) for v in src.bounds],
        "shape": [src.height, src.width],
        "nodata": src.nodata,
        "dtype": src.dtypes[0],
    }


def validate_patch(path, requested, ref_path):
    with rasterio.open(str(ref_path)) as base, rasterio.open(str(path)) as patch:
        if patch.crs is None or patch.crs.to_epsg() != 25830:
            raise ValueError("North patch CRS is not EPSG:25830: {}".format(patch.crs))
        if patch.count != 1 or any(abs(x - 5.0) > 0.01 for x in patch.res):
            raise ValueError("North patch is not a 5 m single-band terrain raster")
        if patch.bounds.top < AOI[3] - 5 or patch.bounds.left > AOI[0] + 5 or patch.bounds.right < AOI[2] - 5:
            raise ValueError("Downloaded coverage does not include requested northern study extent")
        if patch.bounds.bottom > base.bounds.top + 1.0:
            raise ValueError("North patch does not overlap the 0064 raster; a mosaic gap would remain")
        # Require source grids to be on the same pixel lattice before mosaicking.
        dx = (patch.bounds.left - base.bounds.left) / 5.0
        dy = (patch.bounds.top - base.bounds.top) / 5.0
        if abs(dx - round(dx)) > 0.02 or abs(dy - round(dy)) > 0.02:
            raise ValueError("Patch pixel grid is not aligned with the CNIG 0064 tile; resampling needs explicit review")
        extent = unary_union([box(*base.bounds), box(*patch.bounds)])
        fraction = extent.intersection(box(*AOI)).area / box(*AOI).area
        return raster_metadata(patch), float(fraction)


def audit_targeted(ref_path, patch_path):
    """Check the 3 known edge buildings using a true two-raster mosaic.

    Overlapping pixels are not double counted: 0064 takes priority, with the
    north patch filling beyond its northern limit. This is QA, not final feature extraction.
    """
    gdf = gpd.read_file(str(BUILDINGS))
    subset = gdf[gdf.bldg_id.astype(str).isin(TARGET_IDS)]
    if len(subset) != 3 or subset.bldg_id.astype(str).nunique() != 3:
        raise ValueError("Expected 3 unique targeted building IDs")
    outcomes = []
    with rasterio.open(str(ref_path)) as src0, rasterio.open(str(patch_path)) as src1:
        if src0.crs != gdf.crs or src1.crs != gdf.crs:
            raise ValueError("Buildings and terrain CRS mismatch")
        full_extent = unary_union([box(*src0.bounds), box(*src1.bounds)])
        for _, row in subset.iterrows():
            footprint = row.geometry
            if footprint is None or footprint.is_empty:
                raise ValueError("Invalid geometry: {}".format(row.bldg_id))
            local20 = footprint.buffer(20)
            rings = {
                "local": local20.difference(footprint),
                "neighbourhood": footprint.buffer(100).difference(local20),
            }
            ring_rect = footprint.buffer(105).bounds
            data, transform = merge([src0, src1], bounds=ring_rect,
                                    res=(5.0, 5.0), nodata=-9999.0, method="first")
            arr = data[0]
            for label, ring in rings.items():
                mask = geometry_mask([mapping(ring)], out_shape=arr.shape,
                                     transform=transform, invert=True)
                total = int(mask.sum())
                valid = mask & np.isfinite(arr) & (arr != -9999.0)
                count = int(valid.sum())
                geometric = float(ring.intersection(full_extent).area / ring.area)
                outcomes.append({
                    "bldg_id": str(row.bldg_id), "ring": label,
                    "geometric_coverage": geometric,
                    "valid_pixels": count,
                    "total_pixels": total,
                    "valid_pixel_fraction": float(count / total if total else 0),
                })
    return sorted(outcomes, key=lambda x: (x["bldg_id"], x["ring"]))


def fetch(url, dest):
    # Restrict to the known official service. We are acquiring research data,
    # not accepting arbitrary URLs from untrusted inputs.
    if not url.startswith(API + "?"):
        raise ValueError("Unexpected download endpoint")
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".partial")
    if part.exists():
        raise FileExistsError("Existing partial download: {}".format(part))
    LOG.info("Downloading from official IDEE OGC API-Coverages (5 m MDT)")
    request = Request(url, headers={
        "User-Agent": "Habnetic-Research/0.1 (noncommercial)",
        "Accept": "image/tiff,application/octet-stream;q=0.9,*/*;q=0.1",
    })
    try:
        with urlopen(request, timeout=120) as response, part.open("wb") as file:
            mime = response.headers.get("Content-Type", "")
            LOG.info("HTTP %s | Content-Type: %s", response.status, mime)
            if any(x in mime.lower() for x in ("html", "json", "xml")):
                raise ValueError("Server returned a service/error document, not a GeoTIFF")
            shutil.copyfileobj(response, file, length=1024 * 1024)
        with part.open("rb") as f:
            magic = f.read(4)
        if magic not in (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"):
            raise ValueError("Response is not a TIFF (magic bytes mismatch)")
        return part
    except (HTTPError, URLError, OSError, ValueError):
        if part.exists():
            part.unlink()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print official request, no download")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    if not BASE_RASTER.is_file():
        raise FileNotFoundError("Original 0064 tile missing: {}".format(BASE_RASTER))
    with rasterio.open(str(BASE_RASTER)) as base:
        if base.crs is None or base.crs.to_epsg() != 25830 or any(abs(x - 5.0) > 0.01 for x in base.res):
            raise ValueError("Existing 0064 tile has unexpected CRS or pixel size")
        bbox = requested_bbox(base)
    url = build_url(bbox)
    print("CNIG/IDEE OGC API collection:", COLLECTION)
    print("Requested north strip EPSG:25830:", bbox)
    print("Request URL:", url)
    if args.dry_run:
        return
    if TARGET_FILE.exists():
        LOG.info("Revalidating existing downloaded patch: %s", TARGET_FILE)
        downloaded = TARGET_FILE
    else:
        part = fetch(url, TARGET_FILE)
        try:
            # Validate before moving the download into the raw-data archive.
            validate_patch(part, bbox, BASE_RASTER)
            part.replace(TARGET_FILE)
        except Exception:
            LOG.error("Patch invalid; keeping partial for investigation: %s", part)
            raise
        downloaded = TARGET_FILE
    metadata, rectangular = validate_patch(downloaded, bbox, BASE_RASTER)
    targeted = audit_targeted(BASE_RASTER, downloaded)
    print("\n=== DON M1-T NORTH COVERAGE CHECK ===")
    print("Combined rectangle extent coverage: {:.5%}".format(rectangular))
    for row in targeted:
        print("{bldg_id} {ring}: geometric={geometric_coverage:.4%}, valid={valid_pixels}/{total_pixels} ({valid_pixel_fraction:.2%})".format(**row))
    incomplete = [row for row in targeted if row["geometric_coverage"] < 0.99 or row["valid_pixels"] < 20]
    status = "PASS" if rectangular > 0.99999 and not incomplete else "REVIEW_REQUIRED"
    now = utc_now()
    manifest = {
        "schema_version": "1.0", "timestamp_utc": now, "status": status,
        "method": "Official IDEE OGC API-Coverages native 5 m north strip",
        "source_url": url, "collection": COLLECTION, "license": "CC-BY 4.0",
        "attribution": ATTRIBUTION,
        "note": "Separate official API distribution; not the adjacent MTN50 sheet download. Preserve without replacing 0064.",
        "original_tile": str(BASE_RASTER.relative_to(ROOT)).replace("\\", "/"),
        "new_source_file": str(downloaded.relative_to(ROOT)).replace("\\", "/"),
        "new_source_sha256": sha256(downloaded),
        "new_source_bytes": downloaded.stat().st_size,
        "new_raster_metadata": metadata, "requested_bbox_epsg25830": list(bbox),
        "required_aoi_epsg25830": list(AOI),
        "combined_extent_fraction": rectangular, "targeted_building_qa": targeted,
        "limitations": ["Only 3 previously flagged buildings are pixel-tested here; full 7755-building pixel QA remains pending.",
                         "Nearshore water elevation values may be interpolated; check terrain semantics before modelling.",
                         "Validate that combined raster sources share elevation datum and compatible pixel values in their overlap."],
    }
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if not EVENT_JSONL.exists():
        EVENT_JSONL.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    PROVENANCE_MD.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE_MD.write_text(
        "# DON M1-T | Northern terrain coverage via CNIG/IDEE API\n\n"
        + "**Status:** {}  \n**UTC:** {}  \n**Source:** {}  \n".format(status, now, url)
        + "**Collection:** `" + COLLECTION + "`  \n"
        + "**File SHA-256:** `" + manifest["new_source_sha256"] + "`  \n"
        + "**Attribution:** " + ATTRIBUTION + "\n\n"
        + "See `runs/don_m1_citywide/mdt05_north_api_source_manifest.json` for complete metadata and targeted QA.\n"
        + "\n**Warning:** extent and three-building QA is not equivalent to citywide valid-pixel coverage or terrain accuracy.\n",
        encoding="utf-8")
    print("\nSaved manifest:", REPORT_JSON)
    print("Saved provenance:", PROVENANCE_MD)
    print("STATUS:", status)
    if status != "PASS":
        raise SystemExit("North patch imported, but full geometry/pixel QA requires review")


if __name__ == "__main__":
    main()
