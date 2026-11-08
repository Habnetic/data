# Hamburg M1-T: provenance bundle v0.1

## Install on Windows PowerShell

From `C:\Users\C.Price\Habnetic\resilient-housing-bayes`:

```powershell
Expand-Archive -Path "$HOME\Downloads\Habnetic_HAM_M1T_Source_Provenance_v0.1.zip" -DestinationPath "..\data" -Force
```

This creates:

- `docs/provenance/HAM_Terrain_Source_Provenance.md`: narrative inventory, provider responsibilities, dates/licences, file hashes, known exceptions, and unresolved issues.
- `runs/ham_m1_citywide/ham_terrain_source_manifest.json`: machine-readable inventory and QA status.
- `scripts/m1t/diagnose_ham_source_seams.py`: read-only raster inspection + new JSON diagnostic.
- This README.

Run the diagnostic using the correct geospatial environment:

```powershell
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\diagnose_ham_source_seams.py
```

**Inputs**: the existing LGV ZIP, the two converted SH GeoTIFFs, and the NI GeoTIFF. **Output**: `runs/ham_m1_citywide/qa/ham_cross_source_seam_diagnostic_v2.json`. The script does not overwrite any source raster or the original v1 seam report.

## Scientific caution

The existing v1 seam outputs of ~±10,000 m are **not valid evidence of vertical datum mismatch**. The v2 diagnostic inspects potential invalid pixels (including unmasked `-9999`) and computes seam statistics only on four provisionally valid source pixels. A result of insufficient comparisons is `INCONCLUSIVE`, not PASS. Global and near-building regions are reported separately.

No citywide terrain-feature extraction or final 5 m mosaic should be signed off until seam and source-mask QA is resolved.

## Before Git commit

```powershell
git -C ..\data diff --check
git -C ..\data status -sb
git -C ..\data diff --stat
```

Stage only the new documentation, script, and small manifest. Keep downloaded 1.3 GB source ZIP and derived rasters out of Git. Verify checksum strings from source copies before freezing an archive. Update the documentation with actual v2 results afterward.
