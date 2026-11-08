"""Generate a source-level AHN5 provenance report from existing Rotterdam M1 records.

Run from any directory using Habnetic/data's Python interpreter:
    python scripts/m1t/generate_rtm_ahn5_provenance.py

Reads the historical records; does not download or alter source rasters.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
from pathlib import Path


def rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def indexed(items: list[dict[str, str]], label: str) -> dict[str, dict[str, str]]:
    result = {}
    for item in items:
        filename = item.get("filename", "").strip()
        if not filename or filename in result:
            raise ValueError(f"Missing or duplicate filename in {label}: {filename!r}")
        result[filename] = item
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_true(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def document(root: Path) -> tuple[str, dict[str, int]]:
    run = root / "runs/rtm_m1_citywide"
    inventory = indexed(rows(run / "ahn5_5m_download_inventory.csv"), "download inventory")
    initial = indexed(rows(run / "ahn5_5m_tile_manifest.csv"), "initial tile manifest")
    buffered = indexed(rows(run / "ahn5_5m_tile_manifest_buffered.csv"), "buffered tile manifest")
    integrity = indexed(rows(run / "ahn5_5m_mosaic_integrity.csv"), "mosaic integrity")

    if set(initial) - set(buffered):
        raise ValueError("Initial tile manifest contains files absent from buffered manifest")
    if set(inventory) != set(buffered):
        raise ValueError("Buffered tile list differs from downloaded inventory")
    if set(integrity) != set(inventory):
        raise ValueError("Mosaic integrity entries differ from downloaded inventory")
    if len(inventory) != 28:
        raise ValueError(f"Expected 28 final tiles, found {len(inventory)}")

    raw_dir = root / "raw/RTM/terrain/ahn/ahn5_dtm_5m"
    errors = []
    verified = 0
    missing = 0
    all_urls = []
    table = []
    years = set()
    statuses = {}
    for filename in sorted(inventory):
        row = inventory[filename]
        i = integrity[filename]
        url = row.get("url", "").strip()
        recorded_sha = row.get("sha256", "").strip().lower()
        year = str(row.get("year", "")).strip()
        years.add(year)
        all_urls.append(url)
        status = str(row.get("status", "")).strip().lower()
        statuses[status] = statuses.get(status, 0) + 1
        if not url.startswith("https://"):
            errors.append(f"{filename}: no HTTPS source URL recorded")
        if len(recorded_sha) != 64:
            errors.append(f"{filename}: invalid recorded SHA-256")
        # "reused" means an existing source tile was retained on acquisition.
        # This is a legitimate inventory state, not a download failure.
        # Reused files receive the same on-disk SHA-256 verification below.
        if status not in {"downloaded", "reused"}:
            errors.append(f"{filename}: unsupported acquisition status {status!r}")
        if str(row.get("resolution_m", "")).strip() not in {"5", "5.0"}:
            errors.append(f"{filename}: unexpected resolution {row.get('resolution_m')!r}")
        if row.get("crs", "").strip() != "EPSG:7415":
            errors.append(f"{filename}: unexpected CRS {row.get('crs')!r}")
        if not is_true(i.get("passed", "")) or not is_true(i.get("masks_identical", "")):
            errors.append(f"{filename}: mosaic integrity failure")
        try:
            if float(i.get("max_difference_m", "nan")) > 1e-6:
                errors.append(f"{filename}: mosaic elevation difference > 1e-6 m")
        except ValueError:
            errors.append(f"{filename}: invalid mosaic difference")

        original_file = raw_dir / filename
        if original_file.is_file():
            actual_sha = sha256(original_file)
            if actual_sha != recorded_sha:
                errors.append(f"{filename}: source SHA-256 does not match acquisition inventory")
            else:
                verified += 1
            local_state = "Verified"
        else:
            missing += 1
            local_state = "Not available locally"
        table.append(
            f"| `{filename}` | {year} | {status} | `{recorded_sha}` | {local_state} | [Source]({url}) |"
        )
    if errors:
        raise ValueError("Provenance audit FAILED:\n - " + "\n - ".join(errors))

    mosaic = root / "processed/RTM/derived/ahn5_dtm_5m_rtm_mosaic.tif"
    mosaic_sha = sha256(mosaic) if mosaic.is_file() else "Not reverified (mosaic file unavailable locally)"
    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    year_summary = ", ".join(sorted(years))
    status_summary = ", ".join(f"{key}: {count}" for key, count in sorted(statuses.items()))
    text = f"""# Habnetic | Rotterdam M1 AHN5 Source Provenance

**Scope:** Source provenance supplement for the frozen Rotterdam topographic experiment.  
**Generated (UTC):** {generated}  
**Research baseline:** `phase4-m1-complete-v1.0` (Bayesian repository).  
**Status:** Historical records cross-checked; {verified}/{len(inventory)} original source files locally rehashed.  

## Dataset identity

- **Product:** Actueel Hoogtebestand Nederland (AHN5), 5 m Digital Terrain Model (DTM).
- **Data source:** AHN distribution at `basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/`.
- **Provider/attribution:** AHN / Dutch AHN programme, including its participating public authorities.
- **Source years recorded in inventory:** {year_summary} (not download dates).
- **Acquisition statuses in inventory:** {status_summary}. Here, `reused` denotes an existing local tile used in the acquisition workflow; it is not evidence of a new download.
- **Horizontal CRS:** RD New, EPSG:28992.
- **Source compound CRS:** EPSG:7415 (RD New + NAP vertical EPSG:5709).
- **Raster resolution:** 5 m; 28 downloaded tiles for the buffered Rotterdam study area.
- **License:** **Creative Commons Attribution 4.0 International (CC BY 4.0)** for AHN5, not CC0. Official AHN index: https://basisdata.nl/hwh-ahn/AUX/bladwijzer/index.html . License: https://creativecommons.org/licenses/by/4.0/ .
- **Suggested acknowledgement:** "Contains AHN5 digital terrain elevation data, provided through the AHN programme, licensed under CC BY 4.0; terrain derivatives and analysis by Habnetic." Include the official dataset/source link when redistributing derivatives.

The AHN5 product documentation explains that the 5 m model is derived as an unweighted average from the underlying 0.5 m model. Source: https://basisdata.nl/hwh-ahn/AUX/bladwijzer/index.html .

## Acquisition and lineage

1. **Initial footprint selection:** `runs/rtm_m1_citywide/ahn5_5m_tile_manifest.csv` ({len(initial)} tiles).
2. **Buffered study-area selection:** `runs/rtm_m1_citywide/ahn5_5m_tile_manifest_buffered.csv` ({len(buffered)} tiles).
3. **Recorded acquisitions:** `runs/rtm_m1_citywide/ahn5_5m_download_inventory.csv` ({len(inventory)} files, with source URLs, recorded SHA-256, year, CRS, nodata, bounds and status; {status_summary}).
4. **Downloaded source files:** `raw/RTM/terrain/ahn/ahn5_dtm_5m/`.
5. **Mosaic integrity validation:** `runs/rtm_m1_citywide/ahn5_5m_mosaic_integrity.csv` ({len(integrity)} tiles; all marked passed and with identical masks).
6. **Processed mosaic:** `processed/RTM/derived/ahn5_dtm_5m_rtm_mosaic.tif`.
7. **Feature extractor:** `scripts/rtm/m1_extract_terrain_citywide.py` (frozen Rotterdam implementation).

**Mosaic SHA-256 (current local file):** `{mosaic_sha}`.

**Recorded source files with hashes and URLs:**

| Source tile | Tile year | Inventory status | Recorded SHA-256 | Local hash verification | Original URL |
| --- | --- | --- | --- | --- | --- |
"""
    text += "\n".join(table)
    text += f"""

## Verification scope and limitations

- All {len(inventory)} inventory rows match the {len(buffered)} buffered-tile and {len(integrity)} mosaic-integrity records.
- {verified} original source files were rehashed and match their recorded SHA-256 values; {missing} source files were not available locally for rehashing.
- Both `downloaded` and `reused` acquisition statuses are permitted. Neither status substitutes for a present-day file hash verification. An unavailable source is explicitly reported as unverified.
- Every recorded mosaic-integrity result is marked `passed=True`, with `masks_identical=True` and without a reported elevation difference greater than 1e-6 m.
- **Original acquisition timestamps are not present in the inspected inventory.** The timestamp above is the *report generation time*, not a claimed download time. Original file dates are not reliable substitutes.
- Tile years are source-vintage indicators and may differ from processing dates.
- This document is a supplemental provenance record. It does not amend frozen Rotterdam M1 results, and it does not certify inputs beyond this AHN5 terrain source.
- The CC BY 4.0 license pertains to AHN5 source data; license terms of derived software and other data sources must be tracked independently.

## Reproduction

From `Habnetic/data`, run using the existing geospatial Python interpreter:

```powershell
python scripts/m1t/generate_rtm_ahn5_provenance.py
```

Input: existing Rotterdam AHN5 acquisition records and, when present, original source raster files.  
Output: `docs/provenance/RTM_AHN5_Source.md`.  
The generator validates record alignment and SHA-256 checks, and refuses to overwrite the document if an audit check fails.
"""
    return text, {"inventory": len(inventory), "initial": len(initial), "buffered": len(buffered), "integrity": len(integrity), "locally_verified": verified, "not_locally_available": missing, "acquisition_statuses": statuses}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    content, stats = document(root)
    target = root / "docs/provenance/RTM_AHN5_Source.md"
    if not args.dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
    print("RTM AHN5 SOURCE AUDIT: PASS")
    print("Manifest alignment:", stats)
    print("Output:", target if not args.dry_run else "dry run (no file written)")


if __name__ == "__main__":
    main()
