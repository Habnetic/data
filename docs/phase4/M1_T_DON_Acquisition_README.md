# M1-T | Donostia MDT05 acquisition instructions

**Purpose:** Acquire official 5 m digital *terrain* models and retain verifiable data provenance. No synthetic modelling or citywide extraction is performed by this script.

**Reference:** CNIG / IGN, PNOA MDT05, 1st coverage. Source: https://centrodedescargas.cnig.es/CentroDescargas/modelo-digital-terreno-mdt05-primera-cobertura

## 1. Install

Unzip into `C:\Users\C.Price\Habnetic\data` (NOT into `resilient-housing-bayes`). This creates `scripts/m1t/acquire_don_mdt05.py`. Do this on a dedicated `phase4/m1t-ham-don` branch in `data`.

## 2. Acquire

The filtered catalogue shows `PNOA-MDT05-ETRS89-HU30-0064-LID.TIF`, 2012, ~74.47 MB. It is the correct product and a plausible starting sheet, **not yet proof of full buffered study-area coverage**. Search by geographic extent using the CNIG map to ensure neighbouring MTN50 tiles have not been overlooked.

The catalogue's download button may be session-dependent. We have **not verified a stable direct TIFF URL**. Do not invent one. Use the official browser button to download the file to `Downloads`, then run (from `resilient-housing-bayes`):

```powershell
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\acquire_don_mdt05.py --scan-downloads
```

Alternatively, specify a downloaded TIFF explicitly:

```powershell
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\acquire_don_mdt05.py --file "$HOME\Downloads\PNOA-MDT05-ETRS89-HU30-0064-LID.TIF"
```

**Direct automated download**, if you obtain a verified direct HTTPS link (e.g. via browser copy link address), without guessing endpoint URLs:

```powershell
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\acquire_don_mdt05.py --download-url "<ACTUAL_DIRECT_TIFF_URL>" --filename "PNOA-MDT05-ETRS89-HU30-0064-LID.TIF"
```

The script rejects HTML/error pages posing as download files. If a direct link is not available, use the browser route.

## 3. Revalidate and inspect

```powershell
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\acquire_don_mdt05.py --check
Get-Content ..\data\docs\provenance\DON_MDT05_Source.md
```

Machine-readable outputs:

- `data/raw/DON/terrain/cnig_mdt05/` original TIFFs, never modified.
- `data/runs/don_m1_citywide/mdt05_source_manifest.json` with filenames, import timestamps, SHA-256 hashes, source URLs, metadata and rectangular bounding-box coverage.
- `data/runs/don_m1_citywide/mdt05_acquisitions.jsonl` append-only event log.
- `data/docs/provenance/DON_MDT05_Source.md` human-readable provenance, license attribution and QA status.

The rectangular tile **extent** coverage test is necessary but insufficient: further QA must inspect valid raster cells (including water interpolation), source dates and all required 20 m/100 m building rings. This package does not generate a DTM mosaic.

## 4. Licence/attribution

- Unaltered source: **MDT05-cob1 2008-2015 CC-BY 4.0 scne.es**.
- Derivative mosaic/features/maps: **Obra derivada de MDT05-cob1 2008-2015 CC-BY 4.0 scne.es**.

The official licence requires attribution, including in research outputs and digital products. Source dataset uses orthometric heights; water interpolation may be unreliable.

## 5. Commit only code and documentation

Verify your `data` branch first; stage `scripts/m1t/acquire_don_mdt05.py`, `docs/phase4/M1_T_DON_Acquisition_README.md`, and optionally the generated `docs/provenance/DON_MDT05_Source.md`. Keep raw data and large generated outputs out of Git and backed up separately.
