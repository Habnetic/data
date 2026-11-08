# Habnetic M1-T | Shared terrain extractor v0.1

## Purpose

Reuse Rotterdam M1 terrain measurements across **DON** and **HAM** without changing frozen Rotterdam code. This is new development in `Habnetic/data` on `phase4/m1t-ham-don`.

The original 5 m algorithm and quantiles are preserved. **M1-T adds a geometric extent-coverage rule (>=99% for both rings)**; it is a new portability QA decision, not a retroactive amendment of the Rotterdam result.

## Source data

- DON population: `processed/DON/derived/buildings_don.gpkg` (7,755 Phase 3-matched IDs).
- DON raster: `processed/DON/derived/mdt05_don_5m_mosaic.tif` (official CNIG MDT05 2012 sheets 0040 and 0064; see `docs/provenance/DON_MDT05_Mosaic.md`).
- HAM raster is **not available yet**; the default filename in the script is a placeholder.
- RTM regression: frozen GeoPackage and `processed/RTM/derived/ahn5_dtm_5m_rtm_mosaic.tif`.

## Environment

Use the existing `data/.venv` geospatial interpreter initially; ensure it has GeoPandas, Rasterio, Shapely, NumPy, Pandas and a Parquet engine (as with the frozen Rotterdam pipeline). **Python 3.8 is end-of-life; migration to a pinned supported environment is a separate task.**

## Commands (from the `data` repo root)

```powershell
& .\.venv\Scripts\python.exe .\scripts\m1t\extract_terrain.py --city RTM --limit 100
& .\.venv\Scripts\python.exe .\scripts\m1t\verify_rtm_regression.py --limit 100
& .\.venv\Scripts\python.exe .\scripts\m1t\extract_terrain.py --city DON --limit 100
& .\.venv\Scripts\python.exe .\scripts\m1t\extract_terrain.py --city DON --all
```

Tests (if pytest is installed):

```powershell
& .\.venv\Scripts\python.exe -m pytest tests/test_m1t_terrain.py -q
```

Outputs are deterministic, ordered by `bldg_id`, resumable per 1,000-building batch, and kept in separate pilot/full folders under `runs/<city>_m1_citywide`. A SHA-256 manifest binds each run to the source GeoPackage, raster, script and parameters. Never mix outputs from different code/data versions in the same directory.

## Diagnostics and checks

- `T50 = local_p50 - neighbourhood_p50` and `T25 = local_p50 - neighbourhood_p25`.
- Local ring: 0–20 m outside footprint. Neighbourhood: 20–100 m.
- At least 20 valid pixels in each ring.
- Both geometric-coverage fractions >= 0.99, or `T50/T25 = NaN`, `terrain_measured = False`.
- Distinguish `local_coverage` (valid pixels / pixels *within raster*) from `local_geometric_coverage` (ring area within raster / full ring area). Same for neighbourhood.
- Check that all 7,755 DON identifiers occur in full output exactly once and that raster NoData is not confused with elevation.
- Compare the 100 RTM regression records against the frozen RTM terrain output before trusting DON.
- **The earlier targeted DON coverage check (3 buildings) is not a citywide validation.** Summarize missingness from all DON output batches after full run.
- These are terrain features, not observations of actual flood damage.

## Caveats

- Tests use synthetic rasters; no current M1-T code has yet been validated on the user's live Windows environment.
- Source-dependent elevation uncertainties, grid edge behavior and marine interpolation need substantive interpretation in a later scientific QA report.
- Use exact source-version and licensing details from existing CNIG acquisition manifests; do not substitute general license text.


## v0.1.1: Rotterdam compound CRS correction

The frozen AHN5 RTM raster reports EPSG:7415, a compound CRS combining
horizontal RD New (EPSG:28992) and vertical NAP height (EPSG:5709).
The M1-T shared extractor accepts **exactly EPSG:7415 or EPSG:28992**
for Rotterdam, and preserves EPSG:25830 (DON) and EPSG:25832 (HAM)
strictly. This corrects CRS metadata validation only; no raster values,
coordinates, quantiles, or geometry calculations are altered. Run the
RTM regression test before conducting DON extraction. Any existing M1-T
run manifest must not be reused across script changes.
