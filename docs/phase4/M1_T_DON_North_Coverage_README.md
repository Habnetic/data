# Habnetic | M1-T DON north coverage acquisition (v0.2)

## Objective

Download a **small, native 5 m**, official elevation patch to cover the 115.36 m northern shortfall left by CNIG MDT05 sheet 0064. The source is Spain's official **OGC API-Coverages** endpoint, collection `EL.ElevationGridCoverage_25830_5_PB` (ETRS89 / UTM 30N, first LiDAR coverage). It avoids downloading an entire adjacent map sheet.

**Important:** This is an *alternate official distribution*, not a confirmed copy of adjacent MTN50 sheet 0040. Keep both sources separately; verify agreement before mosaicking them. The tool makes no changes to frozen Rotterdam M1.

## Install

Extract ZIP into `C:\Users\C.Price\Habnetic\data` (on `phase4/m1t-ham-don` branch). Existing `scripts/m1t/acquire_don_mdt05.py` is left untouched.

## One-command run

From `C:\Users\C.Price\Habnetic\resilient-housing-bayes`:

```powershell
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\download_don_north_api.py --dry-run
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\download_don_north_api.py
```

No manual CNIG browser download is required **if the API responds correctly**. This workflow has been syntax-checked and locally dry-run tested, **but live API downloading has not been verified from this environment**. If it fails, preserve the error output and use the manual 0040 sheet alternative below.

## Expected output files

- `raw/DON/terrain/cnig_mdt05_api/DON_MDT05_north_ogc_25830_5m.tif`
- `runs/don_m1_citywide/mdt05_north_api_source_manifest.json`
- `runs/don_m1_citywide/mdt05_north_api_acquisitions.jsonl`
- `docs/provenance/DON_MDT05_North_API.md`

The tool verifies TIFF format, CRS, 5 m resolution, grid registration, combined *rectangular* coverage, and complete terrain-ring pixel counts for the three previously flagged buildings. It does not automatically imply all 7,755 buildings have valid elevation. The final citywide QA comes after mosaicking.

## Alternative (manual CNIG tile)

The MTN50 sheet immediately north of **0064 Donostia/San Sebastián** is **0040 Jaizquibel** (verified from the IGME adjoining-sheet index). Look for `PNOA_MDT05_ETRS89_HU30_0040_LID.TIF` *only if that file actually appears in the official CNIG MDT05 catalogue*. The catalogue availability of that particular file was not independently verified. Download it in Firefox, then run the **existing** importer:

```powershell
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\acquire_don_mdt05.py --scan-downloads
```

For consistency, prefer one acquisition method, and document it. If API patch has been downloaded, do not also combine the adjacent sheet without an explicit provenance and pixel-identity comparison.

## Provenance

Provider: CNIG/IGN through API-Coverages, Spanish National Cartographic System. Product: first LiDAR coverage 5 m DTM. Attribution: `Obra derivada de MDT05-cob1 2008-2015 CC-BY 4.0 scne.es`. Every downloaded file is SHA-256 identified. Source URL and timestamp appear in the JSON manifest.
