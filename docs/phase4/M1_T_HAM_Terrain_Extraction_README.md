# Hamburg M1-T two-region extraction (pilot)

**Purpose:** Reuse `scripts/m1t/extract_terrain.py` without changing the frozen Rotterdam T50/T25 definitions. Hamburg has two disjoint 5 m mosaics (mainland and western islands).

**Requirements:** `data/.venv`, `processed/HAM/derived/buildings_ham.gpkg`, both `ham_dgm5_*_mosaic.tif` elevation files and their matching `*_source_id.tif` layers, `runs/ham_m1_citywide/qa/ham_tile_coverage_candidates.csv`. Uses the already installed `geopandas`, `rasterio`, `pandas` and Parquet engine. Python 3.8-compatible code.

Run from `Habnetic/resilient-housing-bayes`:

```powershell
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\extract_ham_terrain_regions.py --mode pilot-mainland
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\extract_ham_terrain_regions.py --mode pilot-boundary
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\extract_ham_terrain_regions.py --mode pilot-western --pilot-count 10
```

Run citywide **only after all pilot outputs are reviewed**:

```powershell
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\extract_ham_terrain_regions.py --mode all
```

Outputs under `runs/ham_m1_citywide/terrain_pilot_*` and `terrain_batches` respectively, with individually hashed batches and an `extraction_run_manifest.json`. Existing outputs are never overwritten. Use `--output-dir` to create an isolated fresh run.

The script checks building count (341,530), ID uniqueness, CRS, both elevation rasters, source-ID grid alignment and routes buildings by disjoint spatial cluster. It calls the existing shared `extract_building` function unchanged and adds only `terrain_region` to each result. Source provenance **within a ring** is represented in the existing per-pixel source-ID mosaics; the region field alone must not be interpreted as a provider. No random sampling; pilots select deterministic input-order subsets.

**QA limitations:** Geometry and pixel validity must still be evaluated citywide; full source-ID composition is not yet extracted per building. Do not claim 100% feature acceptance based solely on native-resolution boundary QA. Monitor extreme T50/T25 values and missingness. Compare RTM/DON regressions when modifying the shared extractor.
