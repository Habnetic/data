# Hamburg M1-T regional 5 m terrain mosaics (v0.1.1)

## Goal and observed correction

Combine 884 source tile entries (880 Hamburg LGV, 2 Schleswig-Holstein, 1 Niedersachsen, 1 WSV Scharhörn) into two regional 5 m mosaics, preserving source identity and strict 25/25 source-pixel validity.

**Why v0.1 failed:** the original mosaic builder assumed the 884 entries represented 884 disjoint 1 km cells. This assumption is false: a Hamburg LGV footprint can coexist with a neighbouring state's DGM1 footprint at a state boundary. In particular, inspection stopped at `(556000, 5939000)`. This was a *builder logic error*, not a reason to discard a provider or its values. No final mosaic was generated in that failed `--inspect-only` run.

## Deterministic overlap policy

- Permit **only** HH LGV + Schleswig-Holstein, or HH LGV + Niedersachsen, on the **same aligned** 1 km footprint. Reject repeated tiles from the same provider and other overlaps.
- On each 5 m cell, **keep valid HH elevation** as the primary source.
- When HH elevation is nodata, **fill only from a valid supplementary 5 m cell**. The supplementary cell itself must pass strict 25/25 native 1 m validity.
- If neither source has a valid elevation, output remains nodata. Preserve the highest source-valid-pixel fraction as metadata and the corresponding provider ID; never invent or average across sources.
- Record the **per-5 m-cell provider** in a source-ID raster. Source 0 means no source tile. Codes: `1=LGV_HH_2022`, `2=LVERMGEO_SH_2021`, `3=LGLN_NI_2025`, `4=WSV_DGMW_2022_SCHARHOERN`.
- On overlap, compare both-valid 5 m values and record absolute-difference statistics. These differences are **not** automatically a datum offset; differing acquisition dates and terrain changes remain possible.
- The policy is a documented *engineering choice*. A sensitivity analysis using the alternative valid provider at overlapping cells remains appropriate after initial extraction.

**The overlap policy does not create new 5 m values from mixing partial 1 m source samples.** All accepted 5 m elevations were independently aggregated by the v0.1 preparation workflow.

## Inputs

- `runs/ham_m1_citywide/qa/ham_dgm5_citywide_manifest.json` (884 source entries)
- `processed/HAM/derived/dgm5_tiles/{HH,SH,NI,WSV}/` (884 elevation and 884 valid-fraction TIFFs)
- EPSG:25832; each input is a 200 × 200 cell 5 m tile for an aligned 1 km footprint.

## One-command reproduction

From `C:\Users\C.Price\Habnetic\resilient-housing-bayes`:

```powershell
& ..\data\.venv\Scripts\python.exe ..\data\tests\test_m1t_ham_dgm5_mosaics.py -v
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\build_ham_dgm5_mosaics.py --inspect-only
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\build_ham_dgm5_mosaics.py
```

The `--inspect-only` command prints the exact duplicated footprints and reconciled source-cell counts; it does **not** write outputs. Inspect the printed overlap statistics before invoking the final build. Existing outputs are never overwritten without `--force`.

## Outputs and checks

- `processed/HAM/derived/ham_dgm5_mainland_mosaic.tif`
- `processed/HAM/derived/ham_dgm5_mainland_mosaic_valid_fraction.tif`
- `processed/HAM/derived/ham_dgm5_mainland_mosaic_source_id.tif`
- `processed/HAM/derived/ham_dgm5_western_islands_mosaic.tif`
- `processed/HAM/derived/ham_dgm5_western_islands_mosaic_valid_fraction.tif`
- `processed/HAM/derived/ham_dgm5_western_islands_mosaic_source_id.tif`
- `runs/ham_m1_citywide/qa/ham_dgm5_mosaic_manifest.json`

The mosaic manifest includes input-manifest SHA-256, region extent and dimensions, raw source tile counts, **unique footprints**, overlap reconciliation records, final provider cell counts, valid elevation counts and output checksums.

Synthetic tests cover nonoverlapping mosaics, nodata/strict aggregation, valid-primary retention, supplementary fill in a shared footprint, and rejection of unsupported/duplicate-source overlaps. This validates the *logic*, not yet the 884 real inputs. After building the real mosaics, recheck the 27 known edge buildings and the full population. Source-datum equivalence and building-level T50/T25 remain unvalidated.

## Scope and data handling

Keep the primary and supplementary raw terrain unchanged. Keep the 884 prepared 5 m tiles unchanged. Do not commit large derived rasters to Git. Commit scripts/tests/docs and small manifests after review; archive outputs after QA.
