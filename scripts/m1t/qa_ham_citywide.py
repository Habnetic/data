"""Audit Hamburg M1-T citywide extraction and prepare spatial review candidates.

Run from anywhere with Habnetic/data's Python 3.8+ geospatial environment:
  python scripts/m1t/qa_ham_citywide.py

Reads existing extraction batches, manifests, and the Phase 3 building GeoPackage.
Never changes source rasters, extraction batches, or input GeoPackage.
"""

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RUN_BASE = ROOT / "runs/ham_m1_citywide"
DEFAULT_BATCH_DIR = RUN_BASE / "terrain_batches"
DEFAULT_QA_DIR = RUN_BASE / "qa"
BUILDINGS_FILE = ROOT / "processed/HAM/derived/buildings_ham.gpkg"
EXPECTED_POPULATION = 341530
EXPECTED_REGIONS = {"mainland": 341461, "western_islands": 69}


def hash_file(path: Path) -> str:
    """SHA-256 of the existing file contents."""
    result = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def require(condition, message: str) -> None:
    """Always-on validation (unlike Python's optimisable assertions)."""
    if not condition:
        raise ValueError(message)


def load_extraction(batch_dir: Path, verify_hashes: bool = True):
    """Validate a complete manifest and load precisely its listed Parquets."""
    manifest_path = batch_dir / "extraction_run_manifest.json"
    require(manifest_path.is_file(), "Missing extraction manifest: {}".format(manifest_path))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest.get("city") == "HAM" and manifest.get("mode") == "all",
            "Expected a Hamburg full extraction manifest")
    require(manifest.get("population") == EXPECTED_POPULATION, "Population mismatch")
    require(manifest.get("selected_buildings") == EXPECTED_POPULATION,
            "Selected population mismatch")
    outputs = manifest.get("outputs")
    require(isinstance(outputs, list) and bool(outputs), "Missing batch output metadata")
    file_names = set(p.name for p in batch_dir.glob("terrain_*.parquet"))
    expected_names = set()
    frames = []
    total = 0
    for record in outputs:
        path = ROOT / record["path"]
        require(path.parent.resolve() == batch_dir.resolve(),
                "Manifest output outside selected batch folder: {}".format(path))
        require(path.is_file(), "Missing output: {}".format(path))
        require(path.name not in expected_names, "Duplicate manifest path: {}".format(path))
        expected_names.add(path.name)
        if verify_hashes:
            require(hash_file(path) == record["sha256"],
                    "Batch SHA-256 mismatch: {}".format(path))
        frame = pd.read_parquet(path)
        require(len(frame) == int(record["count"]),
                "Manifest count mismatch: {}".format(path))
        require(record["end_exclusive"] - record["start"] == len(frame),
                "Manifest index range mismatch: {}".format(path))
        require(record["start"] == total,
                "Non-consecutive manifest batch index: {}".format(path))
        frames.append(frame)
        total += len(frame)
    require(expected_names == file_names,
            "Batch files and manifest differ; untracked or missing outputs")
    require(total == EXPECTED_POPULATION,
            "Unexpected total rows: {}".format(total))
    return pd.concat(frames, ignore_index=True), manifest


def numerical_checks(df: pd.DataFrame, population: int = EXPECTED_POPULATION) -> dict:
    """Verify definitions, eligibility and pixel-validity distributions."""
    required = (
        "bldg_id", "terrain_region", "terrain_measured", "T50", "T25",
        "local_z_50", "neighbourhood_z_50", "neighbourhood_z_25",
        "local_valid_pixels", "local_total_pixels", "local_coverage",
        "neighbourhood_valid_pixels", "neighbourhood_total_pixels", "neighbourhood_coverage",
        "local_geometric_coverage", "neighbourhood_geometric_coverage",
    )
    require(set(required).issubset(df.columns),
            "Missing required columns: {}".format(sorted(set(required) - set(df.columns))))
    require(len(df) == population, "Unexpected row count")
    ids = df.bldg_id.astype(str)
    require(df.bldg_id.notna().all() and ids.is_unique and not (ids.str.strip() == "").any(),
            "Missing or duplicate building identifiers")
    region_counts = {str(k): int(v) for k, v in df.terrain_region.value_counts().items()}
    require(set(region_counts) == {"mainland", "western_islands"},
            "Unknown or missing terrain region")
    measured_mask = df.terrain_measured == True  # noqa: E712; intentionally explicit
    measured = df.loc[measured_mask]
    for name in ("local", "neighbourhood"):
        valid = pd.to_numeric(df[name + "_valid_pixels"], errors="raise")
        total = pd.to_numeric(df[name + "_total_pixels"], errors="raise")
        fraction = pd.to_numeric(df[name + "_coverage"], errors="raise")
        geom = pd.to_numeric(df[name + "_geometric_coverage"], errors="raise")
        require(np.isfinite(valid).all() and np.isfinite(total).all(),
                "Nonfinite pixel count for {}".format(name))
        require(((valid >= 0) & (total >= valid)).all(),
                "Invalid pixel counts for {}".format(name))
        require(np.isfinite(fraction).all() and fraction.between(0, 1).all(),
                "Invalid valid-pixel fraction for {}".format(name))
        require(np.isfinite(geom).all() and geom.between(0, 1).all(),
                "Invalid geometric coverage for {}".format(name))
        calculated = np.where(total > 0, valid / total.replace(0, np.nan), 0.0)
        require(np.allclose(fraction, calculated, rtol=0, atol=1e-8),
                "Pixel coverage mismatch for {}".format(name))
        require((measured[name + "_valid_pixels"] >= 20).all(),
                "Measured buildings below minimum valid-pixel count for {}".format(name))
        require((measured[name + "_geometric_coverage"] >= .99 - 1e-10).all(),
                "Measured buildings below geometric coverage threshold for {}".format(name))

    if len(measured):
        values = measured[["T50", "T25", "local_z_50", "neighbourhood_z_50",
                           "neighbourhood_z_25"]].to_numpy(dtype=float)
        require(np.isfinite(values).all(), "Nonfinite terrain value in measured records")
        require(np.allclose(measured.T50, measured.local_z_50 - measured.neighbourhood_z_50,
                            rtol=0, atol=1e-5), "T50 formula inconsistent")
        require(np.allclose(measured.T25, measured.local_z_50 - measured.neighbourhood_z_25,
                            rtol=0, atol=1e-5), "T25 formula inconsistent")
        require((measured.T25 >= measured.T50 - 1e-5).all(), "T25 < T50")
    if len(df) - len(measured):
        unmeasured = df.loc[~measured_mask]
        require((~np.isfinite(unmeasured[["T50", "T25"]].to_numpy(dtype=float))).all(),
                "Unmeasured records contain finite terrain features")

    coverage = {}
    for name in ("local", "neighbourhood"):
        x = df[name + "_coverage"].astype(float)
        coverage[name] = {
            "minimum": float(x.min()), "median": float(x.median()),
            "p01": float(x.quantile(.01)), "p05": float(x.quantile(.05)),
            "below_0_99": int((x < .99).sum()),
            "below_0_90": int((x < .90).sum()),
            "below_0_50": int((x < .50).sum()),
        }
    def describe(col):
        s = measured[col].astype(float)
        return {name: float(value) for name, value in {
            "min": s.min(), "p01": s.quantile(.01), "median": s.median(),
            "p99": s.quantile(.99), "max": s.max(), "mean": s.mean(),
        }.items()} if len(s) else {}
    return {
        "rows": int(len(df)), "measured": int(len(measured)),
        "missing": int(len(df) - len(measured)),
        "region_counts": region_counts,
        "valid_pixel_fraction": coverage,
        "T50_m": describe("T50"), "T25_m": describe("T25"),
        "all_numeric_checks_pass": True,
    }


def spatial_candidates(df: pd.DataFrame, top_n: int = 20,
                       t50_limit: float = 8.0, t25_high: float = 15.0,
                       t25_low: float = -5.0) -> pd.DataFrame:
    """Return deterministic review targets, not automatically invalid features."""
    require(top_n >= 1, "top_n must be positive")
    require(t50_limit > 0 and t25_high > t25_low, "Invalid diagnostic thresholds")
    reasons = {}
    def tag(indices, label):
        for idx in indices:
            reasons.setdefault(idx, set()).add(label)
    measured = df.loc[df.terrain_measured == True]  # noqa: E712
    tag(measured.index[measured.T50 >= t50_limit], "T50_ge_{}m".format(t50_limit))
    tag(measured.index[measured.T50 <= -t50_limit], "T50_le_minus_{}m".format(t50_limit))
    tag(measured.index[measured.T25 >= t25_high], "T25_ge_{}m".format(t25_high))
    tag(measured.index[measured.T25 <= t25_low], "T25_le_{}m".format(t25_low))
    tag(df.index[df.local_coverage < .99], "local_valid_fraction_lt_0.99")
    tag(df.index[df.neighbourhood_coverage < .99], "neighbour_valid_fraction_lt_0.99")
    tag(measured.nlargest(top_n, "T50").index, "top_T50")
    tag(measured.nsmallest(top_n, "T50").index, "bottom_T50")
    tag(measured.nlargest(top_n, "T25").index, "top_T25")
    tag(measured.nsmallest(top_n, "T25").index, "bottom_T25")
    tag(df.nsmallest(top_n, "local_coverage").index, "lowest_local_valid_fraction")
    tag(df.nsmallest(top_n, "neighbourhood_coverage").index,
        "lowest_neighbour_valid_fraction")
    chosen = sorted(reasons)
    result = df.loc[chosen].copy()
    result["qa_reason"] = ["; ".join(sorted(reasons[i])) for i in chosen]
    result["qa_status"] = "PENDING_MANUAL_REVIEW"
    result["bldg_id"] = result.bldg_id.astype(str)
    return result


def export_spatial_review(candidates: pd.DataFrame, geo_path: Path,
                          output_dir: Path, expected_ids=None,
                          expected_population: int = EXPECTED_POPULATION) -> None:
    """Export exact building polygons as GeoPackage for QGIS review."""
    if candidates.empty:
        raise ValueError("No review candidates")
    buildings = gpd.read_file(geo_path)
    require(buildings.crs is not None and buildings.crs.to_epsg() == 25832,
            "Unexpected Hamburg building CRS")
    require(len(buildings) == expected_population, "Building GeoPackage population mismatch")
    source_ids = buildings.bldg_id.astype(str)
    require(source_ids.is_unique and buildings.bldg_id.notna().all(),
            "Source GeoPackage has missing or duplicate identifiers")
    if expected_ids is not None:
        require(set(source_ids) == set(pd.Series(expected_ids).astype(str)),
                "Extracted IDs do not match the Phase 3 building population")
    chosen_ids = set(candidates.bldg_id)
    require(chosen_ids.issubset(set(source_ids)), "Review ID not found in source GeoPackage")
    selected = buildings.loc[source_ids.isin(chosen_ids), ["bldg_id", "geometry"]].copy()
    selected["bldg_id"] = selected.bldg_id.astype(str)
    candidates = candidates.drop(columns=["geometry"], errors="ignore")
    joined = selected.merge(candidates, on="bldg_id", how="inner", validate="one_to_one")
    require(len(joined) == len(candidates), "Spatial candidate join lost rows")
    joined = gpd.GeoDataFrame(joined, geometry="geometry", crs=buildings.crs)
    output_dir.mkdir(parents=True, exist_ok=True)
    gpkg_path = output_dir / "ham_m1t_spatial_review.gpkg"
    if gpkg_path.exists():
        raise FileExistsError("Existing spatial review; refusing overwrite: {}".format(gpkg_path))
    joined.to_file(str(gpkg_path), driver="GPKG", layer="review_candidates")
    candidates.to_csv(output_dir / "ham_m1t_spatial_review.csv", index=False)
    print("QGIS layer:", gpkg_path)
    print("Review candidate rows:", len(joined))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-dir", type=Path, default=DEFAULT_BATCH_DIR)
    parser.add_argument("--qa-dir", type=Path, default=DEFAULT_QA_DIR)
    parser.add_argument("--skip-hashes", action="store_true",
                        help="Skip Parquet SHA-256 checks (default verifies hashes)")
    parser.add_argument("--top-n", type=int, default=20)
    args = parser.parse_args()

    df, manifest = load_extraction(args.batch_dir.resolve(), not args.skip_hashes)
    report = numerical_checks(df)
    require(report["region_counts"] == EXPECTED_REGIONS,
            "Hamburg region counts differ from documented 341461/69")
    candidates = spatial_candidates(df, top_n=args.top_n)
    report.update({
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "city": "HAM", "phase": "M1-T", "status": "NUMERICAL_PASS_SPATIAL_REVIEW_PENDING",
        "extraction_manifest_sha256": hash_file(args.batch_dir / "extraction_run_manifest.json"),
        "batch_hashes_verified": not args.skip_hashes,
        "spatial_candidates": int(len(candidates)),
        "selection_note": ("Candidate thresholds: |T50| >= 8m, T25 >= 15m, T25 <= -5m, "
                           "valid-pixel fraction < 0.99 in either ring, plus top/bottom "
                           "20 in each feature and 20 lowest coverage in each ring. "
                           "Flags are review priorities, not error diagnoses."),
        "critical_note": "terrain_measured requires 20 valid pixels per ring and 99% "
                         "geometric extent coverage; it does NOT require 99% valid pixels."
    })
    args.qa_dir.mkdir(parents=True, exist_ok=True)
    output = args.qa_dir / "ham_m1t_citywide_numerical_qa.json"
    if output.exists():
        raise FileExistsError("QA report exists; refusing overwrite: {}".format(output))
    if (args.qa_dir / "ham_m1t_spatial_review.gpkg").exists():
        raise FileExistsError("Spatial review exists; refusing overwrite")
    export_spatial_review(candidates, BUILDINGS_FILE, args.qa_dir,
                          expected_ids=df.bldg_id, expected_population=EXPECTED_POPULATION)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("\nHAMBURG CITYWIDE M1-T NUMERICAL QA: PASS")
    print("Rows:", report["rows"], "Measured:", report["measured"],
          "Missing:", report["missing"])
    print("Regions:", report["region_counts"])
    for ring in ("local", "neighbourhood"):
        c = report["valid_pixel_fraction"][ring]
        print("{} valid-pixel coverage: min {:.4f}, p01 {:.4f}, <99% {}, <90% {}".format(
            ring, c["minimum"], c["p01"], c["below_0_99"], c["below_0_90"]))
    print("Spatial QA candidates:", report["spatial_candidates"])
    print("QA report:", output)
    print("SPATIAL INTERPRETATION: PENDING (do not claim validation complete)")


if __name__ == "__main__":
    main()
