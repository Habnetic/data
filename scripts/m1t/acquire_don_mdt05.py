#!/usr/bin/env python3
"""Acquire, validate, and document official CNIG MDT05 terrain tiles for Donostia.

Designed for Python 3.8+ and the existing Habnetic/data geospatial environment.
Requires rasterio and shapely. No third-party HTTP client required.

This script is intentionally independent of the frozen RTM extraction scripts.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import shutil
import sys
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import rasterio
from shapely.geometry import box
from shapely.ops import unary_union


LOG = logging.getLogger("habnetic.m1t.don.acquisition")
DATA_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = DATA_ROOT / "raw" / "DON" / "terrain" / "cnig_mdt05"
RUN_DIR = DATA_ROOT / "runs" / "don_m1_citywide"
DOC_PATH = DATA_ROOT / "docs" / "provenance" / "DON_MDT05_Source.md"
MANIFEST_PATH = RUN_DIR / "mdt05_source_manifest.json"
EVENT_LOG = RUN_DIR / "mdt05_acquisitions.jsonl"
CATALOG_URL = "https://centrodedescargas.cnig.es/CentroDescargas/modelo-digital-terreno-mdt05-primera-cobertura"
ATTRIBUTION_ORIGINAL = "MDT05-cob1 2008-2015 CC-BY 4.0 scne.es"
ATTRIBUTION_DERIVATIVE = "Obra derivada de MDT05-cob1 2008-2015 CC-BY 4.0 scne.es"
# Phase 3 DON derived buildings.gpkg bounds expanded 100 m for neighbourhood ring.
REQUIRED_BOUNDS = (574351.982459101, 4785931.96049428,
                   589589.417160402, 4798637.86387985)
FILE_PATTERN = re.compile(r"^PNOA[-_]MDT05[-_]ETRS89[-_]HU30[-_](\d{4})[-_]LID\.TIF$", re.I)


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect(path: Path) -> dict:
    """Verify that a tile has the expected spatial metadata, without resampling."""
    if not FILE_PATTERN.fullmatch(path.name):
        raise ValueError(f"Unexpected MDT05 tile filename: {path.name}")
    with rasterio.open(str(path)) as src:
        if src.crs is None or src.crs.to_epsg() != 25830:
            raise ValueError(f"Expected EPSG:25830, got {src.crs}: {path}")
        if src.count != 1:
            raise ValueError(f"Expected single-band raster, got {src.count}: {path}")
        if any(abs(float(r) - 5.0) > 0.000001 for r in src.res):
            raise ValueError(f"Expected 5 m cell size, got {src.res}: {path}")
        if src.width <= 0 or src.height <= 0:
            raise ValueError(f"Raster is empty: {path}")
        metadata = {
            "crs": str(src.crs),
            "resolution_m": list(src.res),
            "bounds_epsg25830": list(src.bounds),
            "width": src.width,
            "height": src.height,
            "bands": src.count,
            "dtype": src.dtypes[0],
            "nodata": src.nodata,
        }
    return metadata


def load_manifest() -> dict:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {
        "schema_version": "1.0",
        "city": "DON",
        "provider": "IGN / CNIG (Spain)",
        "product": "PNOA MDT05 - 1st LiDAR coverage",
        "source_catalog": CATALOG_URL,
        "original_attribution": ATTRIBUTION_ORIGINAL,
        "derivative_attribution": ATTRIBUTION_DERIVATIVE,
        "reference_system": "ETRS89 / UTM 30N (EPSG:25830); orthometric heights",
        "required_bounds_epsg25830": list(REQUIRED_BOUNDS),
        "records": {},
    }


def import_tile(source: Path, manifest: dict, method: str,
                direct_url: str = "", source_year: str = "") -> None:
    """Import a downloaded TIFF without replacing divergent source files."""
    if not source.is_file():
        raise FileNotFoundError(source)
    if not FILE_PATTERN.fullmatch(source.name):
        raise ValueError(f"Not a CNIG MDT05 HU30 LID TIFF: {source.name}")
    # Validate the source before copying anything into the research data store.
    metadata = inspect(source)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    destination = RAW_DIR / source.name
    source_hash = sha256(source)
    if destination.exists():
        if sha256(destination) != source_hash:
            raise ValueError(f"Existing tile has different content; refusing overwrite: {destination}")
        LOG.info("Already archived, checksum identical: %s", destination.name)
    else:
        temp_path = destination.with_name(destination.name + ".partial")
        if temp_path.exists():
            raise FileExistsError(f"Previous partial file exists: {temp_path}")
        try:
            shutil.copyfile(str(source), str(temp_path))
            if sha256(temp_path) != source_hash:
                raise IOError("File checksum mismatch during local import")
            temp_path.replace(destination)
        finally:
            if temp_path.exists():
                temp_path.unlink()
        LOG.info("Imported: %s", destination.name)
    sheet = FILE_PATTERN.fullmatch(source.name).group(1)
    record = {
        "filename": destination.name,
        "sheet_mtn50": sheet,
        "product_year_visible_in_catalog": source_year or ("2012" if sheet == "0064" else "not verified"),
        "imported_at_utc": timestamp(),
        "method": method,
        "acquisition_url": direct_url or "manual browser download from source_catalog",
        "local_relative_path": str(destination.relative_to(DATA_ROOT)).replace("\\", "/"),
        "bytes": destination.stat().st_size,
        "sha256": source_hash,
        "raster": metadata,
    }
    previous = manifest["records"].get(destination.name)
    if previous is not None and previous.get("sha256") != source_hash:
        raise ValueError(f"Manifest hash mismatch: {destination.name}")
    # Avoid falsely resetting the historical acquisition timestamp on repeat checks.
    if previous is not None:
        record = previous
    else:
        RUN_DIR.mkdir(parents=True, exist_ok=True)
        with EVENT_LOG.open("a", encoding="utf-8") as sink:
            sink.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    manifest["records"][destination.name] = record


def download_tile(url: str, name: str) -> Path:
    """Download from a direct HTTPS binary URL, preserving a partial file safely."""
    if not FILE_PATTERN.fullmatch(name):
        raise ValueError("--filename must match PNOA-MDT05-ETRS89-HU30-####-LID.TIF")
    if urlparse(url).scheme != "https":
        raise ValueError("Expected a direct HTTPS URL copied from the official catalogue")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = RAW_DIR / (name + ".download.partial")
    if temp_path.exists():
        raise FileExistsError(f"Previous partial file exists: {temp_path}")
    LOG.info("Downloading direct URL for %s", name)
    request = Request(url, headers={"User-Agent": "Habnetic-Research/1.0"})
    try:
        with urlopen(request, timeout=120) as response, temp_path.open("wb") as out:
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" in content_type or "text/xml" in content_type:
                raise ValueError("Server returned HTML/XML, not a direct TIFF; use browser download")
            shutil.copyfileobj(response, out, length=1024 * 1024)
        with temp_path.open("rb") as head:
            magic = head.read(4)
        if magic not in (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"):
            raise ValueError("Download is not a TIFF (possibly a login/error page or ZIP)")
        # rasterio can open the .partial TIFF using its magic bytes.
        with rasterio.open(str(temp_path)) as src:
            if src.count != 1:
                raise ValueError("Downloaded TIFF was not a single-band raster")
        return temp_path
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise


def coverage(manifest: dict) -> dict:
    all_bounds = [box(*record["raster"]["bounds_epsg25830"])
                  for record in manifest["records"].values()]
    roi = box(*REQUIRED_BOUNDS)
    if not all_bounds:
        return {"rectangular_bbox_coverage_fraction": 0.0,
                "aoi_fully_within_tile_extents": False}
    mosaic_extents = unary_union(all_bounds)
    fraction = float(mosaic_extents.intersection(roi).area / roi.area)
    return {
        "rectangular_bbox_coverage_fraction": fraction,
        "aoi_fully_within_tile_extents": fraction > 0.999999,
        "warning": "Bounds-only test: does not establish valid elevation pixels or per-building ring coverage",
    }


def write_outputs(manifest: dict) -> None:
    manifest["last_checked_utc"] = timestamp()
    manifest["extent_check"] = coverage(manifest)
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for record in sorted(manifest["records"].values(), key=lambda r: r["filename"]):
        rows.append("| `{}` | {} | {} | `{}` | {} |".format(
            record["filename"], record["product_year_visible_in_catalog"],
            record["bytes"], record["sha256"], record["imported_at_utc"]))
    if not rows:
        rows = ["| _Not acquired yet_ | | | | |"]
    area = manifest["extent_check"]
    text = """# Habnetic | DON M1-T terrain data provenance

**Status:** {status}
**Last checked (UTC):** {checked}
**Dataset:** PNOA MDT05, first LiDAR coverage, native 5 m DTM (NOT MDS).
**Provider:** Instituto Geográfico Nacional / Centro Nacional de Información Geográfica (Spain).
**Catalogue:** {catalog}
**Reference:** EPSG:25830, ETRS89 / UTM 30N, orthometric heights.
**Phase 3 DON study population:** 7,755 buildings (`processed/DON/derived/buildings_don.gpkg`).
**Required extent, EPSG:25830, including 100 m ring:** `{bbox}`.
**Raw files:** `raw/DON/terrain/cnig_mdt05/`.
**Machine-readable log:** `runs/don_m1_citywide/mdt05_source_manifest.json`.
**Append-only acquisition events:** `runs/don_m1_citywide/mdt05_acquisitions.jsonl`.

## Tiles received

| Original filename | Source year (catalogue) | Bytes | SHA-256 | Imported UTC |
| --- | --- | ---: | --- | --- |
{rows}

**Combined rectangular extent coverage:** {fraction:.3%}.
**Complete AOI within source extents:** {complete}.
**IMPORTANT:** This is only an extent test. Pixel NoData coverage, water interpolation quality,
ring coverage and all building-level terrain quality checks are **not yet validated**.
Do not begin citywide extraction solely because this flag says True.

## Attribution and reuse

Source dataset (unmodified): **{original}**.
For mosaics, derived raster clips, terrain features, figures, and other derived outputs, credit:
**{derived}**.

The CNIG/IGN licence is compatible with CC-BY 4.0, requiring source acknowledgement
for originals and derivative products. Preserve this credit in published figures,
web maps, derived datasets, and Operations Center source metadata.
See the current catalogue licence for the official wording.

## Scientific cautions

- Source LiDAR acquisition: first coverage (2008–2015); individual sheet vintages are listed above when verified.
- CNIG states water-surface voids can be interpolated and have low reliability. Do not treat all finite pixels as observed elevations of equal quality.
- Compare source quality, NoData and acquisition vintages against RTM AHN5; common 5 m resolution alone does not ensure equivalent data quality.
- The Phase 3 building IDs are fixed; no real flood-damage validation is implied.
- Recheck source tile extents using map search and inspect actual raster coverage before accepting the set.
""".format(status="Tiles acquired; pixel-level QA pending" if manifest["records"] else "Acquisition pending",
            checked=manifest["last_checked_utc"], catalog=CATALOG_URL,
            bbox=list(REQUIRED_BOUNDS), rows="\n".join(rows),
            fraction=area["rectangular_bbox_coverage_fraction"],
            complete=area["aoi_fully_within_tile_extents"],
            original=ATTRIBUTION_ORIGINAL, derived=ATTRIBUTION_DERIVATIVE)
    DOC_PATH.write_text(text, encoding="utf-8")
    LOG.info("Wrote provenance: %s", DOC_PATH)
    LOG.info("Wrote manifest: %s", MANIFEST_PATH)
    LOG.info("AOI rectangle covered by tile bounds: %.2f%%",
             area["rectangular_bbox_coverage_fraction"] * 100)
    if not area["aoi_fully_within_tile_extents"]:
        LOG.warning("Tile EXTENTS do not cover the full buffered study area: additional sheet(s) needed")
    else:
        LOG.warning("Extent coverage passed; NoData/real pixel coverage still require separate QA")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--file", type=Path, help="Import one TIFF already downloaded via CNIG browser")
    selector.add_argument("--scan-downloads", action="store_true", help="Import all matching MDT05 HU30 TIFFs from Downloads")
    selector.add_argument("--download-url", metavar="URL", help="Download a direct official HTTPS TIFF URL")
    selector.add_argument("--check", action="store_true", help="Recheck existing raw tiles and regenerate provenance")
    parser.add_argument("--filename", help="Filename when using --download-url; must match catalogue")
    parser.add_argument("--source-year", help="Acquisition year as listed by official catalogue; default 2012 for sheet 0064")
    parser.add_argument("--downloads-dir", type=Path, default=Path.home() / "Downloads")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    manifest = load_manifest()
    if args.file:
        import_tile(args.file.resolve(), manifest, "manual_browser_download", source_year=args.source_year or "")
    elif args.scan_downloads:
        matches = sorted(path for path in args.downloads_dir.iterdir() if path.is_file() and FILE_PATTERN.fullmatch(path.name))
        if not matches:
            raise FileNotFoundError(f"No MDT05 HU30 TIFFs in {args.downloads_dir}; download via the official CNIG catalogue first")
        for path in matches:
            import_tile(path.resolve(), manifest, "browser_download_scanned", source_year=args.source_year or "")
    elif args.download_url:
        if not args.filename:
            parser.error("--download-url requires --filename")
        partial = download_tile(args.download_url, args.filename)
        try:
            # import_tile expects an official file name, not a .partial filename.
            renamed = partial.with_name(args.filename + ".staging")
            # Use a temporary folder instead of changing the raw destination on partial success.
            # Download files are validated under a matching filename in the system temp directory.
            import tempfile
            with tempfile.TemporaryDirectory(prefix="habnetic_mdt05_") as tmp:
                temp_file = Path(tmp) / args.filename
                shutil.copyfile(str(partial), str(temp_file))
                import_tile(temp_file, manifest, "direct_url_download", direct_url=args.download_url,
                            source_year=args.source_year or "")
        finally:
            if partial.exists():
                partial.unlink()
    else:  # --check
        for path in sorted(RAW_DIR.glob("*.TIF")) if RAW_DIR.exists() else []:
            metadata = inspect(path)
            rec = manifest["records"].get(path.name)
            current_hash = sha256(path)
            if rec is None:
                raise ValueError(f"Raw tile not recorded in provenance: {path.name}; import with --file")
            if rec["sha256"] != current_hash or rec["raster"] != metadata:
                raise ValueError(f"Raw tile integrity/metadata mismatch: {path.name}")
        for filename in manifest["records"]:
            if not (RAW_DIR / filename).exists():
                raise FileNotFoundError(f"Manifest tile missing: {filename}")
        LOG.info("Validated %s previously imported raw files", len(manifest["records"]))
    write_outputs(manifest)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        LOG.error("Acquisition failed: %s", exc)
        sys.exit(1)
