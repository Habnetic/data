# Habnetic | Phase 4 M1-T Hamburg — dataset closure note

**Date:** 2026-11-08<br>
**Disposition:** **Numerical QA passed. Six-case representative spatial review completed with recorded limitations. Derived terrain-feature dataset suitable for downstream experiments, not physically validated citywide.**

## Purpose and scientific boundary

Carry the frozen Rotterdam definitions for T50 and T25 to the 341,530 Hamburg Phase 3 building population using a documented and reproducible terrain-data workflow. M1-T does **not** fit a Bayesian model and does **not** assert that terrain features improve flood-risk prediction or selection stability.

## Data inputs and lineage

- Buildings: `processed/HAM/derived/buildings_ham.gpkg`, 341,530 distinct Phase 3 identifiers, EPSG:25832.
- DGM native sources: Hamburg LGV 2022 (880 source tiles), Schleswig-Holstein LVermGeo 2021 (2 tiles), Niedersachsen LGLN 2025 (1 tile) and Scharhörn WSV 2022 (one 1 km extraction from the larger DGM-W raster).
- 1 m → 5 m: 884 source regions, conservative all-25-valid source-pixel aggregation, explicit `−9999` exclusion, separate elevation/coverage/source attribution layers; no elevation interpolation.
- Two raster mosaics: mainland and western islands. The only duplicate 1 km footprint, at `(556000,5939000)`, reconciled by retaining valid Hamburg cells and filling Hamburg nodata with valid SH cells; provenance retained in source-ID raster.
- Shared building extraction core: `scripts/m1t/extract_terrain.py:extract_building`, unchanged by Hamburg routing; ring definitions `footprint.buffer(20) − footprint`, and `footprint.buffer(100) − footprint.buffer(20)`.

## Audited outputs

| Dimension | Verified observation |
| --- | --- |
| Buildings and unique Phase 3 IDs | 341,530 / 341,530 |
| Mainland / western routed | 341,461 / 69 |
| Measured T50/T25 | 341,530 / 341,530 |
| Missing measurements | 0 |
| Batch outputs | 342 Parquets; hashes verified by citywide QA |
| Actual local valid-pixel fraction, minimum | 1.0000 |
| Actual neighbourhood valid-pixel fraction, minimum | approximately 0.993377 |
| Buildings with <99% valid elevation pixels in either ring | 0 |
| T50 median / range, m | +0.0426 / [−12.9748, +19.6924] |
| T25 median / range, m | +0.6168 / [−8.5080, +27.0540] |
| Automatic spatial-review candidates | 398 |
| Reviewed manually/targeted | 6 |

The 398 review candidates remain in `runs/ham_m1_citywide/qa/ham_m1t_spatial_review.csv/.gpkg`; the reviewed set and evidence are separately recorded in `docs/qa/HAM_M1T_Spatial_QA.md` and `HAM_M1T_reviewed_cases.csv`. **The 392 remaining candidates were not manually approved.** The full numeric QA report retains its historical pre-spatial-review status and is not overwritten.

## Scientific limitations to carry forward

- Strong relief dominates several extreme T50/T25 results; selected QGIS visual inspections support plausibility, not ground-truth elevation accuracy.
- Case `8629` low quartile is geographically coherent within its exact 20–100 m ring, but its absolute terrain value is not independently surveyed.
- Case `41204` appears to be a local depression near a facility; natural versus anthropogenic origin is unresolved.
- Case `304428` has 0.6623% missing neighbourhood pixels concentrated near a raster edge; the original footprint has not been independently surveyed.
- Source-year differences, the 2.944 m maximum HH/SH overlap disagreement, nodata masking and potential 5 m aggregation sensitivity remain documented uncertainties.
- These terrain indicators describe local contrast, not flood hazard, impact, vulnerability, recovery, calibrated probabilities or decision stability.

## Outputs and reproducibility

**Run QA check:**

```powershell
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\finalize_ham_m1t.py --check
```

**Derived data sources to retain:** `runs/ham_m1_citywide/terrain_batches/`, both final DGM5 mosaics with their valid-fraction/source-ID companions, Phase 3 buildings GeoPackage, numerical QA manifests, targeted QA layers, script/test versions, raw source attribution and hashes.

**Archive convention:** create a **derived analysis archive** from the local Windows repository using `finalize_ham_m1t.py --archive ...`. The original raw source DGM1/DGM-W files are **not** embedded; keep them in a separate source archive with official download references and SHA256 checksums. A derived-only archive is insufficient for full from-raw reproducibility without those original sources.

**Next gate:** record Git commit and source archival location/checksum, then begin sensitivity and Bayesian downstream integration. Neither model performance nor decision utility has been established here.
