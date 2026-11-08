# Habnetic | M1-T Donostia terrain consolidation (v0.1)

**Goal:** Independently check and consolidate the eight citywide M1-T terrain batches produced for Donostia, without changing the frozen Rotterdam calculations or source rasters.

## How to run

From `C:\Users\C.Price\Habnetic\resilient-housing-bayes` (Windows PowerShell), using the **data** repository's known-working geospatial Python interpreter:

```powershell
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\consolidate_don_terrain.py
```

## Expected data

- `data/runs/don_m1_citywide/terrain_batches/terrain_000000_000999.parquet` through `terrain_007000_007754.parquet` (eight deterministic batches).
- `data/runs/don_m1_citywide/terrain_batches/extraction_run_manifest.json`.
- `data/processed/DON/phase3_assets.parquet` with the frozen 7,755 `bldg_id` identifiers.
- Unchanged geospatial extraction inputs (recorded in the manifest) and `data/scripts/m1t/extract_terrain.py`.

## Outputs

- `data/runs/don_m1_citywide/terrain_features_m1_5m.parquet`: citywide terrain features, preserving all 7,755 Phase 3 asset identifiers.
- `data/runs/don_m1_citywide/terrain_features_m1_5m_qa.json`: counts, T50/T25 distributions, boundary/valid-pixel checks, source and output SHA-256 hashes, incomplete IDs if any.

## Validation

The script refuses to run when batches are missing/extra, IDs mismatch Phase 3, input or script hashes changed, measurements violate geometric / pixel thresholds, or T50/T25 are inconsistent with their frozen definitions. It refuses to overwrite existing outputs.

**Caveats:** A `PASS` confirms dataset integrity and compliance with the M1-T QA rules, not terrain accuracy or empirical flood prediction validity. The 99% geometric coverage threshold is a new portability criterion and must not be retroactively attributed to frozen Rotterdam M1. The source-data licence and attribution remain in `docs/provenance/DON_MDT05_Source.md` and `DON_MDT05_Mosaic.md`.

**To reproduce:** install the data repository's pinned environment, generate the two-tile mosaic, run the citywide extractor, and execute the one-line consolidation command above. The extraction manifest fixes data hashes and parameters. Preserve source datasets and manifests alongside outputs when archiving.
