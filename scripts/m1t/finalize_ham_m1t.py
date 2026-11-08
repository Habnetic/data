"""Auditable Hamburg M1-T dataset closure and derived-output archival.

Defaults to a read-only check. --write-manifest adds a separate closure manifest and
an idempotent provenance addendum. --archive builds a ZIP64 *derived analysis*
archive, excluding large original raw source DEMs (archive those separately).

Run using Habnetic/data's geospatial Python, from any working directory.
"""

import argparse
import csv
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
QA = ROOT / "runs/ham_m1_citywide/qa"
RUN = ROOT / "runs/ham_m1_citywide"
PROVENANCE = ROOT / "docs/provenance/HAM_Terrain_Source_Provenance.md"
EXTRACTION_MANIFEST = RUN / "terrain_batches/extraction_run_manifest.json"
NUMERIC_REPORT = QA / "ham_m1t_citywide_numerical_qa.json"
CANDIDATES = QA / "ham_m1t_spatial_review.csv"
TARGETED = QA / "ham_targeted_diagnostics/ham_8629_304428_diagnostic.json"
REGISTER = ROOT / "docs/qa/HAM_M1T_reviewed_cases.csv"
SPATIAL_NOTE = ROOT / "docs/qa/HAM_M1T_Spatial_QA.md"
CLOSURE_NOTE = ROOT / "docs/phase4/M1_T_HAM_Closure_Report.md"
CLOSURE_MANIFEST = QA / "ham_m1t_closure_manifest.json"
ARCHIVE_INVENTORY = QA / "ham_m1t_archive_inventory.json"
EXPECTED = 341530
EXPECTED_REGIONS = {"mainland": 341461, "western_islands": 69}
REVIEW_IDS = {"8937", "7616", "8629", "41204", "304428", "6904"}


def need(condition, message):
    """Raise a reliable error, including when Python assertions are disabled."""
    if not condition:
        raise ValueError(message)


def get_json(path):
    need(path.is_file(), "Missing required JSON: {}".format(path))
    return json.loads(path.read_text(encoding="utf-8"))


def file_hash(path):
    """Compute SHA-256 without loading a source file into RAM."""
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path):
    need(path.is_file(), "Missing required CSV: {}".format(path))
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def git_commit():
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(ROOT), stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, universal_newlines=True, check=False,
        )
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def validate_reports(numeric, extraction, targeted, candidates, register):
    """Verify reported observations without fabricating absent measurements."""
    need(numeric.get("city") == "HAM" and numeric.get("phase") == "M1-T",
         "Unexpected city/phase in numeric QA")
    need(numeric.get("all_numeric_checks_pass") is True, "Numerical QA not marked PASS")
    need(numeric.get("batch_hashes_verified") is True, "Original QA did not verify batch SHA-256")
    need(numeric.get("rows") == EXPECTED and numeric.get("measured") == EXPECTED,
         "Population/measurement count mismatch")
    need(numeric.get("missing") == 0, "Measurements missing")
    need(numeric.get("region_counts") == EXPECTED_REGIONS, "Regional population mismatch")
    need(numeric.get("spatial_candidates") == 398, "Expected 398 QA candidates")
    for ring in ("local", "neighbourhood"):
        stats = numeric["valid_pixel_fraction"][ring]
        need(stats["minimum"] >= 0.99, "Valid coverage <99% in {}".format(ring))
        need(stats["below_0_99"] == 0, "Buildings below 99% valid coverage")
    need(abs(numeric["valid_pixel_fraction"]["neighbourhood"]["minimum"] - 0.993377) < 0.0002,
         "Unexpected minimum neighbourhood coverage")

    need(extraction.get("city") == "HAM" and extraction.get("mode") == "all",
         "Expected a full Hamburg extraction")
    need(extraction.get("selected_buildings") == EXPECTED and
         extraction.get("population") == EXPECTED, "Extraction manifest population mismatch")
    batches = extraction.get("outputs")
    need(isinstance(batches, list) and len(batches) == 342, "Expected 342 batch outputs")
    need(sum(int(batch["count"]) for batch in batches) == EXPECTED, "Batch counts mismatch")
    need(set(extraction.get("rasters", {})) == {"mainland", "western_islands"},
         "Missing regional raster metadata")

    need(len(candidates) == 398, "Candidate CSV does not contain 398 rows")
    candidate_ids = {row["bldg_id"].strip() for row in candidates}
    need(len(candidate_ids) == 398 and REVIEW_IDS.issubset(candidate_ids),
         "Candidate identities are missing or duplicated")
    need(len(register) == 6 and {row["bldg_id"] for row in register} == REVIEW_IDS,
         "Six-case review register mismatch")
    candidates_by_id = {row["bldg_id"]: row for row in candidates}
    for row in register:
        source = candidates_by_id[row["bldg_id"]]
        for key in ("T50", "T25"):
            need(abs(float(row[key + "_m"]) - float(source[key])) < 0.002,
                 "Case value mismatch for {} {}".format(row["bldg_id"], key))
        for filename in row["evidence_files"].split(";"):
            evidence = ROOT / "docs/qa/evidence" / filename
            need(evidence.is_file(), "Missing QGIS screenshot: {}".format(evidence))
    need(targeted.get("status") == "DIAGNOSTIC_ONLY_NOT_SPATIAL_VALIDATION",
         "Unexpected diagnostic provenance/status")
    results = targeted["buildings"]
    need({"8629", "304428"}.issubset(results), "Missing targeted diagnostic building")
    need(abs(float(results["8629"]["neighbourhood_p25_m"]) - 8.6014) < 0.003,
         "8629 low quartile does not match extracted value")
    need(int(results["8629"]["lower_quartile_pixel_count"]) > 0,
         "8629 low quartile pixel layer missing or empty")
    need(abs(float(results["304428"]["neighbourhood_valid_fraction"]) - 0.993377) < 0.0002,
         "304428 neighbourhood coverage does not match QA")
    need(int(results["304428"]["neighbourhood_invalid_pixels"]) > 0,
         "304428 invalid-pixel count unexpectedly zero")
    return {"rows": EXPECTED, "measured": EXPECTED, "missing": 0,
            "regions": EXPECTED_REGIONS, "candidate_count": 398,
            "reviewed_count": 6, "unreviewed_count": 392,
            "local_min_valid_fraction": numeric["valid_pixel_fraction"]["local"]["minimum"],
            "neighbourhood_min_valid_fraction":
                numeric["valid_pixel_fraction"]["neighbourhood"]["minimum"],
            "building_8629_p25_m": results["8629"]["neighbourhood_p25_m"],
            "building_304428_valid_fraction":
                results["304428"]["neighbourhood_valid_fraction"]}


def verify_extraction_files(extraction, deep=False):
    """Check 342 existing Parquets and four raster provenance hashes when deep."""
    total = 0
    seen = set()
    for batch in extraction["outputs"]:
        relative = Path(batch["path"])
        absolute = (ROOT / relative).resolve()
        need(absolute.parent == (RUN / "terrain_batches").resolve(),
             "Unexpected batch path: {}".format(relative))
        need(absolute.is_file() and absolute.stat().st_size > 0,
             "Missing/empty Parquet: {}".format(relative))
        need(str(relative) not in seen, "Duplicate batch path in manifest")
        seen.add(str(relative))
        total += int(batch["count"])
        if deep:
            need(file_hash(absolute) == batch["sha256"], "Parquet hash mismatch: {}".format(absolute))
    need(len(seen) == 342 and total == EXPECTED, "Parquet inventory count mismatch")
    for region in ("mainland", "western_islands"):
        record = extraction["rasters"][region]
        for key, hash_key in (("path", "sha256"), ("source_id_path", "source_id_sha256")):
            path = ROOT / record[key]
            need(path.is_file() and path.stat().st_size > 0, "Missing raster: {}".format(path))
            if deep:
                need(file_hash(path) == record[hash_key], "Raster hash mismatch: {}".format(path))
        fraction = ROOT / "processed/HAM/derived" / (
            "ham_dgm5_{}_mosaic_valid_fraction.tif".format(region))
        need(fraction.is_file(), "Missing fraction raster: {}".format(fraction))
    buildings = extraction["buildings"]
    path = ROOT / buildings["path"]
    need(path.is_file(), "Missing Phase 3 building source GeoPackage")
    if deep:
        need(file_hash(path) == buildings["sha256"], "Building GeoPackage hash mismatch")
    print("Input/output inventory: 342 Parquet batches; 2 regions; 6 raster layers; buildings GPKG. PASS")
    if deep:
        print("SHA-256: all batches, both regional elevations/source-ID grids, and buildings source PASS")


def validate_source_documents():
    documents = [SPATIAL_NOTE, CLOSURE_NOTE, REGISTER, PROVENANCE,
                 RUN / "ham_terrain_source_manifest.json",
                 QA / "ham_dgm5_citywide_manifest.json",
                 QA / "ham_dgm5_mosaic_manifest.json",
                 QA / "ham_dgm5_final_boundary_ring_qa.csv"]
    for path in documents:
        need(path.is_file(), "Required document/manifest missing: {}".format(path))
    need("-9999" in PROVENANCE.read_text(encoding="utf-8"),
         "Hamburg provenance lacks nodata discussion")


def check(deep=False):
    numeric = get_json(NUMERIC_REPORT)
    extraction = get_json(EXTRACTION_MANIFEST)
    targeted = get_json(TARGETED)
    candidates = read_csv(CANDIDATES)
    register = read_csv(REGISTER)
    validate_source_documents()
    need(numeric.get("extraction_manifest_sha256") == file_hash(EXTRACTION_MANIFEST),
         "Numerical QA refers to a different extraction manifest")
    summary = validate_reports(numeric, extraction, targeted, candidates, register)
    verify_extraction_files(extraction, deep=deep)
    print("Hamburg M1-T closure gate: PASS (numeric + six-case representative review only)")
    print("Measured: {measured}/{rows}; review: {reviewed_count}/{candidate_count} candidates."
          .format(**summary))
    return summary


ADDENDUM_MARK = "## M1-T final citywide numerical and representative spatial QA (2026-11-08)"


def update_provenance():
    """Append rather than overwrite the detailed multi-source provenance ledger."""
    text = PROVENANCE.read_text(encoding="utf-8")
    if ADDENDUM_MARK in text:
        print("Provenance already contains closure addendum; unchanged")
        return
    addition = """
{}

- Derived 1 m → 5 m preprocessing completed for **884** source regions. Across HH tiles,
  **107,349,120** stored but unmasked `−9999` values were diagnosed and excluded;
  all-25-valid aggregation was applied with no imputation.
- Final regional mosaics: mainland (8200 × 8000 at 5 m) and western islands
  (1200 × 1400 at 5 m); elevation, valid-source fraction and source ID grids retained.
- Final boundary exact-ring validation: 27/27 buildings passed; both rings at
  100% actual valid coverage for those inspected sites.
- Citywide extracted population: **341,530/341,530** unique Phase 3 building IDs;
  T50/T25 measured on all; zero missing. Final numerical QA passed and verified
  342 batch Parquet checksums and exact Phase 3 ID correspondence.
- Citywide minimum actual valid elevation pixel fraction: local **1.0**,
  neighbourhood **≈0.993377**; no building below 99% in either ring.
- **398** numeric/spatial priority candidates were generated; **six** cases were
  reviewed spatially, and **392** remain individually unreviewed. The six-case
  evidence and limitations are recorded in `docs/qa/HAM_M1T_Spatial_QA.md`.
- A shared HH/SH tile footprint used valid HH elevations and filled HH nodata
  from SH; 17,644 cells retained from HH and 22,356 supplied by SH.
  Where both provider values existed, median absolute difference 0.064 m,
  p95 absolute 0.1884 m, maximum absolute 2.944 m. The maximum-discrepancy
  location remains a sensitivity-check opportunity, **not a validation failure**.
- Data provenance remains temporally heterogeneous (HH 2022 / SH 2021 /
  NI 2025 / WSV 2022), and absolute vertical accuracy was not independently verified.
- The original numerical QA report and prior exploratory seam reports are
  preserved unchanged; the separate closure manifest records subsequent review.
""".format(ADDENDUM_MARK)
    PROVENANCE.write_text(text.rstrip() + "\n\n" + addition.strip() + "\n", encoding="utf-8")
    print("Provenance addendum appended: {}".format(PROVENANCE))


def write_closure_manifest(summary):
    need(not CLOSURE_MANIFEST.exists(), "Closure manifest exists; refusing overwrite")
    payload = {
        "project": "Habnetic", "city": "HAM", "phase": "M1-T",
        "review_date": "2026-11-08",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "DERIVED_FEATURES_CLOSED_NUMERIC_PASS_REPRESENTATIVE_SPATIAL_QA_LIMITED",
        "scientific_scope": "Not a validation of flood risk or decision model improvement",
        "source_repo_git_commit_before_closure": git_commit(),
        "numeric_and_review_counts": summary,
        "spatial_review_limitation": "Six reviewed; 392 other priority candidates not inspected individually",
        "input_manifest_sha256": file_hash(EXTRACTION_MANIFEST),
        "numeric_report_sha256": file_hash(NUMERIC_REPORT),
        "targeted_diagnostic_sha256": file_hash(TARGETED),
        "spatial_inventory_csv_sha256": file_hash(CANDIDATES),
        "reviewed_case_register_sha256": file_hash(REGISTER),
        "spatial_qa_note_sha256": file_hash(SPATIAL_NOTE),
        "provenance_document_sha256": file_hash(PROVENANCE),
        "source_manifest_sha256": file_hash(RUN / "ham_terrain_source_manifest.json"),
        "raw_terrain_source_files_embedded": False,
        "raw_terrain_source_references": "docs/provenance/HAM_Terrain_Source_Provenance.md",
    }
    CLOSURE_MANIFEST.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                                encoding="utf-8")
    print("Closure manifest written: {}".format(CLOSURE_MANIFEST))


def gathered_files():
    """Explicit derived archive contents. Raw provider rasters are NOT included."""
    files = set()
    fixed = [EXTRACTION_MANIFEST, NUMERIC_REPORT, CANDIDATES, TARGETED,
             REGISTER, SPATIAL_NOTE, CLOSURE_NOTE, PROVENANCE, CLOSURE_MANIFEST,
             RUN / "ham_terrain_source_manifest.json",
             ROOT / "processed/HAM/derived/buildings_ham.gpkg"]
    files.update(fixed)
    for pattern in (
        "docs/qa/evidence/HAM_*.png",
        "docs/phase4/M1_T_HAM*.md",
        "docs/qa/HAM_*.md", "docs/qa/HAM_*.csv",
        "scripts/m1t/*ham*.py", "scripts/m1t/*sh*.py", "scripts/m1t/*ni*.py",
        "tests/test_m1t_ham*.py",
        "runs/ham_m1_citywide/terrain_batches/terrain_*.parquet",
        "runs/ham_m1_citywide/qa/*.json", "runs/ham_m1_citywide/qa/*.csv",
        "runs/ham_m1_citywide/qa/*.gpkg",
        "runs/ham_m1_citywide/qa/ham_targeted_diagnostics/*.json",
        "runs/ham_m1_citywide/qa/ham_targeted_diagnostics/*.gpkg",
        "processed/HAM/derived/ham_dgm5_*mosaic*.tif",
    ):
        files.update(ROOT.glob(pattern))
    files.add(ROOT / "scripts/m1t/extract_terrain.py")
    files.add(ROOT / "scripts/m1t/convert_sh_xyz.py")
    files.discard(ARCHIVE_INVENTORY)
    files = sorted(path for path in files if path.is_file())
    for mandatory in fixed:
        need(mandatory in files, "Missing archive requirement: {}".format(mandatory))
    need(len(list((RUN / "terrain_batches").glob("terrain_*.parquet"))) == 342,
         "Unexpected full extraction batch inventory")
    return files


def archive(archive_path):
    need(CLOSURE_MANIFEST.is_file(), "Create closure manifest with --write-manifest first")
    need(not archive_path.exists(), "Archive exists; refusing overwrite: {}".format(archive_path))
    files = gathered_files()
    inventory = []
    for idx, path in enumerate(files, 1):
        relative = path.relative_to(ROOT).as_posix()
        item = {"relative_path": relative, "bytes": path.stat().st_size,
                "sha256": file_hash(path)}
        inventory.append(item)
        if idx % 100 == 0:
            print("Inventory hashed {}/{} inputs".format(idx, len(files)))
    payload = {
        "archive_type": "HAM_M1T_DERIVED_ANALYSIS_NOT_RAW_SOURCE",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_repo_git_commit_at_archive": git_commit(),
        "raw_source_rasters_included": False,
        "raw_source_storage": "Store original Hamburg/SH/NI/WSV provider source files separately with checksums",
        "file_count": len(inventory), "files": inventory,
    }
    ARCHIVE_INVENTORY.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(str(archive_path), mode="w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=3, allowZip64=True) as zf:
        for idx, path in enumerate(files, 1):
            zf.write(str(path), arcname=path.relative_to(ROOT).as_posix())
            if idx % 100 == 0:
                print("Archived {}/{} inputs".format(idx, len(files)))
        zf.write(str(ARCHIVE_INVENTORY),
                 arcname=ARCHIVE_INVENTORY.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(str(archive_path)) as check_zip:
        need(len(check_zip.namelist()) == len(files) + 1,
             "Archive entry count mismatch")
        need(check_zip.testzip() is None, "Archive CRC verification failed")
    digest = file_hash(archive_path)
    checksum_path = archive_path.with_name(archive_path.name + ".sha256")
    checksum_path.write_text("{}  {}\n".format(digest, archive_path.name), encoding="ascii")
    print("Derived ZIP: {}".format(archive_path))
    print("ZIP SHA-256: {}".format(digest))
    print("Raw terrain sources: NOT INCLUDED; archive those independently.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Read-only closure check (default)")
    parser.add_argument("--deep", action="store_true",
                        help="Rehash Parquet batches and raster/building source references")
    parser.add_argument("--write-manifest", action="store_true",
                        help="Append provenance addendum and create separate closure JSON")
    parser.add_argument("--archive", type=Path,
                        help="Create a ZIP64 derived analysis archive at this local path")
    args = parser.parse_args()
    if args.archive and args.write_manifest:
        parser.error("Run --write-manifest before --archive as separate operations")
    summary = check(deep=args.deep or bool(args.archive))
    if args.write_manifest:
        update_provenance()
        write_closure_manifest(summary)
    if args.archive:
        archive(args.archive.resolve())


if __name__ == "__main__":
    main()
