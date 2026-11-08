"""Consolidate and independently audit Donostia M1-T terrain batches.

Run (from Habnetic/data):
    .venv/Scripts/python.exe scripts/m1t/consolidate_don_terrain.py

Inputs: 8 citywide batches, extraction manifest, Phase 3 building IDs.
Outputs: versioned citywide Parquet and JSON QA report under runs/don_m1_citywide.
No terrain data are modified, interpolated or imputed.
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "runs/don_m1_citywide"
BATCHES = RUN / "terrain_batches"
PHASE3 = ROOT / "processed/DON/phase3_assets.parquet"
OUTPUT = RUN / "terrain_features_m1_5m.parquet"
REPORT = RUN / "terrain_features_m1_5m_qa.json"
EXTRACTOR = ROOT / "scripts/m1t/extract_terrain.py"
N_BUILDINGS = 7755
BATCH_SIZE = 1000
MIN_PIXELS = 20
MIN_GEOMETRIC_COVERAGE = 0.99


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def distribution(series):
    valid = pd.to_numeric(series, errors="raise").dropna()
    if valid.empty:
        return {"count": 0}
    return {
        "count": int(len(valid)),
        "min": float(valid.min()),
        "p01": float(valid.quantile(0.01)),
        "median": float(valid.median()),
        "p99": float(valid.quantile(0.99)),
        "max": float(valid.max()),
    }


def main():
    for path in [BATCHES, PHASE3, EXTRACTOR]:
        require(path.exists(), "Missing required input: {}".format(path))
    require(not OUTPUT.exists() and not REPORT.exists(),
            "Output or QA report already exists. Refusing to overwrite: {} / {}".format(OUTPUT, REPORT))

    run_manifest_path = BATCHES / "extraction_run_manifest.json"
    require(run_manifest_path.is_file(), "Missing extraction run manifest")
    manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    require(manifest.get("city") == "DON", "Wrong city in extraction manifest")
    require(manifest.get("batch_size") == BATCH_SIZE, "Unexpected batch size")
    require(manifest.get("min_valid_pixels") == MIN_PIXELS, "Unexpected minimum valid pixels")
    require(abs(float(manifest.get("min_geometric_coverage", -1)) - MIN_GEOMETRIC_COVERAGE) < 1e-12,
            "Unexpected geometric coverage threshold")
    require(manifest.get("script_sha256") == sha256(EXTRACTOR),
            "Extractor has changed since batches were generated")
    for field_path, field_sha in [("buildings_file", "buildings_sha256"),
                                   ("raster_file", "raster_sha256")]:
        input_file = Path(manifest[field_path])
        require(input_file.is_file(), "Missing extraction source: {}".format(input_file))
        require(sha256(input_file) == manifest[field_sha],
                "Extraction source hash changed: {}".format(input_file))

    expected = [
        "terrain_{:06d}_{:06d}.parquet".format(start, min(start + BATCH_SIZE, N_BUILDINGS) - 1)
        for start in range(0, N_BUILDINGS, BATCH_SIZE)
    ]
    found_paths = sorted(BATCHES.glob("terrain_*.parquet"))
    require([p.name for p in found_paths] == expected,
            "Batch file list does not match expected contiguous eight batches: {}".format([p.name for p in found_paths]))

    frames = []
    source_records = []
    for path in found_paths:
        frame = pd.read_parquet(path)
        match = re.fullmatch(r"terrain_(\d{6})_(\d{6})\.parquet", path.name)
        require(match is not None, "Unrecognized batch filename: {}".format(path))
        start, end = (int(match.group(1)), int(match.group(2)))
        require(len(frame) == end - start + 1, "Incorrect batch length: {}".format(path.name))
        require("bldg_id" in frame and frame["bldg_id"].is_unique and not frame["bldg_id"].isna().any(),
                "Missing/duplicate IDs in {}".format(path.name))
        frames.append(frame)
        source_records.append({"filename": path.name, "rows": len(frame), "sha256": sha256(path)})

    features = pd.concat(frames, ignore_index=True)
    require(len(features) == N_BUILDINGS, "Unexpected total building count")
    require(features.bldg_id.is_unique and not features.bldg_id.isna().any(), "Duplicate/missing output IDs")
    baseline = pd.read_parquet(PHASE3, columns=["bldg_id"])
    require(len(baseline) == N_BUILDINGS and baseline.bldg_id.is_unique and not baseline.bldg_id.isna().any(),
            "Unexpected Phase 3 population")
    require(set(features.bldg_id) == set(baseline.bldg_id), "Phase 3 and terrain building identifiers differ")

    required_columns = [
        "T50", "T25", "local_z_50", "neighbourhood_z_50", "neighbourhood_z_25",
        "local_valid_pixels", "neighbourhood_valid_pixels", "local_total_pixels",
        "neighbourhood_total_pixels", "local_coverage", "neighbourhood_coverage",
        "local_geometric_coverage", "neighbourhood_geometric_coverage", "terrain_measured",
    ]
    require(not (set(required_columns) - set(features.columns)), "Missing terrain QA columns")
    measured = features.terrain_measured.astype(bool)

    for prefix in ("local", "neighbourhood"):
        valid = pd.to_numeric(features[prefix + "_valid_pixels"], errors="raise")
        total = pd.to_numeric(features[prefix + "_total_pixels"], errors="raise")
        cov = pd.to_numeric(features[prefix + "_coverage"], errors="raise")
        geo = pd.to_numeric(features[prefix + "_geometric_coverage"], errors="raise")
        require(((valid >= 0) & (valid <= total) & (total >= 0)).all(), "Invalid pixel counts for {}".format(prefix))
        require(((cov >= 0) & (cov <= 1) & (geo >= 0) & (geo <= 1)).all(),
                "Invalid coverage fractions for {}".format(prefix))
        expected_cov = valid / total.replace(0, np.nan)
        expected_cov = expected_cov.fillna(0)
        require(np.allclose(cov, expected_cov, atol=1e-10, rtol=0),
                "Inconsistent valid-pixel coverage for {}".format(prefix))
        require((valid[measured] >= MIN_PIXELS).all(), "Measured building below pixel threshold")
        require((geo[measured] >= MIN_GEOMETRIC_COVERAGE - 1e-10).all(),
                "Measured building below geometric coverage threshold")

    for field in ["T50", "T25", "local_z_50", "neighbourhood_z_50", "neighbourhood_z_25"]:
        values = pd.to_numeric(features[field], errors="raise")
        require(np.isfinite(values[measured].to_numpy(dtype=float)).all(),
                "Nonfinite measured values: {}".format(field))
        require(values[~measured].isna().all(), "Unmeasured values should be missing: {}".format(field))

    l50 = features.local_z_50.to_numpy(dtype=float)
    n50 = features.neighbourhood_z_50.to_numpy(dtype=float)
    n25 = features.neighbourhood_z_25.to_numpy(dtype=float)
    t50 = features.T50.to_numpy(dtype=float)
    t25 = features.T25.to_numpy(dtype=float)
    require(np.allclose(t50[measured], l50[measured] - n50[measured], atol=1e-8, rtol=0),
            "T50 differs from frozen definition")
    require(np.allclose(t25[measured], l50[measured] - n25[measured], atol=1e-8, rtol=0),
            "T25 differs from frozen definition")

    summary = {
        "status": "PASS",
        "city": "DON",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "buildings": N_BUILDINGS,
        "measured": int(measured.sum()),
        "unmeasured": int((~measured).sum()),
        "geometric_coverage_threshold": MIN_GEOMETRIC_COVERAGE,
        "min_valid_pixels": MIN_PIXELS,
        "phase3_asset_sha256": sha256(PHASE3),
        "extraction_manifest_sha256": sha256(run_manifest_path),
        "extraction_script_sha256": sha256(EXTRACTOR),
        "source_batches": source_records,
        "T50_m": distribution(features.T50),
        "T25_m": distribution(features.T25),
        "local_geometric_coverage": distribution(features.local_geometric_coverage),
        "neighbourhood_geometric_coverage": distribution(features.neighbourhood_geometric_coverage),
        "unmeasured_building_ids": [str(x) for x in features.loc[~measured, "bldg_id"].tolist()],
        "notes": [
            "Complete geographic extent is distinct from valid elevation pixel coverage.",
            "99% geometric coverage is an M1-T portability QA rule, not part of frozen Rotterdam M1.",
            "No missing elevation values were imputed.",
            "Terrain feature values are methodological outputs, not observed flood damage.",
        ],
    }

    tmp_parquet = OUTPUT.with_suffix(".partial.parquet")
    try:
        features.to_parquet(tmp_parquet, index=False)
        require(len(pd.read_parquet(tmp_parquet, columns=["bldg_id"])) == N_BUILDINGS,
                "Temporary output failed verification")
        tmp_parquet.replace(OUTPUT)
    finally:
        if tmp_parquet.exists():
            tmp_parquet.unlink()
    summary["output_parquet_sha256"] = sha256(OUTPUT)
    temp_report = REPORT.with_suffix(".partial.json")
    temp_report.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_report.replace(REPORT)

    print("DON M1-T CONSOLIDATION: PASS")
    print("Buildings: {} | measured: {} | unmeasured: {}".format(
        N_BUILDINGS, summary["measured"], summary["unmeasured"]))
    print("T50 (m):", summary["T50_m"])
    print("T25 (m):", summary["T25_m"])
    print("Parquet:", OUTPUT)
    print("QA report:", REPORT)
    if summary["unmeasured"]:
        print("WARNING: Some terrain measurements remain missing. Review QA report.")


if __name__ == "__main__":
    main()
