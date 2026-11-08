# Habnetic | HAM M1-T Citywide QA v0.1

## Aim
Validate numerical and identity completeness of the **341,530-building** Hamburg extraction, distinguish valid-pixel coverage from geometric coverage, and create a reproducible QGIS review layer for unusual topographic values. This is **not** a flood-risk validation or a certificate of physical elevation accuracy.

## Inputs
- `runs/ham_m1_citywide/terrain_batches/terrain_*.parquet` (expected full set, 342 batches at the default batch size)
- `runs/ham_m1_citywide/terrain_batches/extraction_run_manifest.json`
- `processed/HAM/derived/buildings_ham.gpkg` in EPSG:25832

## Install
Extract this ZIP into `C:\Users\C.Price\Habnetic\data`. No original extractor files are overwritten.

## One-command reproducibility
From `C:\Users\C.Price\Habnetic\resilient-housing-bayes`:

```powershell
& ..\data\.venv\Scripts\python.exe ..\data\tests\test_m1t_ham_citywide_qa.py -v
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\qa_ham_citywide.py
```

The first command tests numerical QA with synthetic examples. The second validates the real extraction; by default all Parquet SHA-256 digests are checked against the run manifest. It refuses to overwrite existing QA reports and spatial review files.

## Outputs
- `runs/ham_m1_citywide/qa/ham_m1t_citywide_numerical_qa.json`: explicit population, distribution and valid-pixel coverage diagnostics.
- `runs/ham_m1_citywide/qa/ham_m1t_spatial_review.csv`: candidate IDs, values and review reasons.
- `runs/ham_m1_citywide/qa/ham_m1t_spatial_review.gpkg`: `review_candidates` building polygons, ready for QGIS.

## Review-candidate selection (diagnostic, not exclusions)
- All buildings with `|T50| >= 8 m`, `T25 >= 15 m`, `T25 <= -5 m`.
- All buildings with under 99% **valid pixels** in either ring (not necessarily invalid according to the frozen extraction criteria).
- Top and bottom 20 for T50 and T25; the 20 lowest coverage measurements for each ring.
- Duplicated candidates appear only once, with combined reason labels.

**Crucial methodological distinction:** the shared extractor uses `>=20` valid pixels and `>=99%` *geometric extent* per ring. **It does not require `>=99%` of all pixels inside each ring to be valid.** Therefore 341,530/341,530 measured does not alone establish 100% valid-pixel coverage or 100% physical validity.

## QGIS review protocol
1. Open `ham_m1t_spatial_review.gpkg` alongside the final Hamburg elevation mosaic and `ham_dgm5_*_mosaic_source_id.tif`.
2. Inspect the largest positive and negative T50 values, largest and smallest T25 values, and the lowest valid-pixel-coverage cases.
3. Compare local building footprint geometry with actual terrain, slopes, embankments, coast/river edges, bridges, tile seams, source transitions, and masked areas.
4. Mark each reviewed ID as `plausible`, `questionable`, or `artifact`, recording evidence. Distinguish physical topography from flood exposure or vulnerability. The QA layer is a starting point, not a final annotation.
5. Do **not** edit the source observations to force plausible results. Corrections require their own version and documented method.

## Provenance and versioning
- Existing source, mosaics and extraction manifest remain unchanged.
- Review outputs are generated under `runs/` and should be archived with SHA-256 checksums.
- Commit script, test and README to the `Habnetic/data` Git repository after successful validation. Do not commit large generated GeoPackage files if excluded by repository policy.

## Assumptions
Population: 341,530; region counts: mainland 341,461 and western islands 69. CRS: EPSG:25832. All length/elevation-derived differences in metres. Extraction formulas and ring geometries are unchanged. Candidate thresholds are **screening heuristics**, not scientific rejection rules.

## Next
Write a reviewed spatial QA register and consolidate the M1-T Hamburg results. Compare sampling and terrain feature distributions across RTM, DON and HAM only after each city's scientific QA status is documented.
