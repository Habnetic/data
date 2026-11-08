# Habnetic M1-T | Donostia DTM mosaic: execution instructions

From `C:\Users\C.Price\Habnetic\resilient-housing-bayes`, use the existing geospatial interpreter explicitly:

```powershell
# First confirm data repo is on its M1-T branch
 git -C ..\data status -sb

# Read-only compatibility and seam inspection
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\build_don_mdt05_mosaic.py --inspect-only

# Build the clipped mosaic, verify three targeted edge buildings, write hashes/provenance
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\build_don_mdt05_mosaic.py

# Review provenance and Git changes
Get-Content ..\data\docs\provenance\DON_MDT05_Mosaic.md -TotalCount 45
git -C ..\data status -sb
```

## Inputs
- `raw/DON/terrain/cnig_mdt05/PNOA_MDT05_ETRS89_HU30_0064_LID.tif`
- `raw/DON/terrain/cnig_mdt05/PNOA_MDT05_ETRS89_HU30_0040_LID.tif`
- `processed/DON/derived/buildings_don.gpkg`

## Outputs
- `processed/DON/derived/mdt05_don_5m_mosaic.tif` (AOI-clipped, 5 m)
- `runs/don_m1_citywide/mdt05_mosaic_manifest.json` (SHA-256, source metadata, seam QA, targeted pixel QA)
- `docs/provenance/DON_MDT05_Mosaic.md` (human-readable attribution and provenance)

The script refuses to overwrite existing mosaics. It does not modify source TIFFs, compute building-level T50/T25, or claim complete citywide valid-pixel coverage. The citywide extraction pilot and subsequent pixel QA remain separate tasks.

Reference provider: CNIG MDT05 first coverage; derived-product attribution `Obra derivada de MDT05-cob1 2008-2015 CC-BY 4.0 scne.es`.
