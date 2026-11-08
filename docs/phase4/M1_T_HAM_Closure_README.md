# Hamburg M1-T | Closure package v0.1

**Release intent:** Turn completed numerical QA and the *six-case* spatial review into a reproducible research record. **No scientific feature values are changed.** Original citywide numeric QA report is preserved untouched; a *separate* closure manifest describes subsequent review.

## Contents

- `docs/qa/HAM_M1T_Spatial_QA.md`: scientific QA evidence, six dispositions, 398-candidate limitation, source boundary uncertainty.
- `docs/qa/HAM_M1T_reviewed_cases.csv`: six-record human-readable review register (not a claim that the other 392 cases passed manual QA).
- `docs/qa/evidence/HAM_*.png`: nine QGIS screenshots supplied during user-assisted review. OpenStreetMap imagery © OpenStreetMap contributors where shown.
- `docs/phase4/M1_T_HAM_Closure_Report.md`: dataset release/closure note.
- `scripts/m1t/finalize_ham_m1t.py`: read-only verification, provenance addendum, separately recorded closure manifest, and optional local ZIP64 **derived analysis** archive.
- `tests/test_m1t_ham_closure.py`: five unit tests for guardrails; these synthetic checks are not a substitute for the user's citywide run.

## Installation (Windows PowerShell)

Run from `C:\Users\C.Price\Habnetic\resilient-housing-bayes`:

```powershell
Expand-Archive `
    -Path "$HOME\Downloads\Habnetic_HAM_M1T_Closure_v0.1.zip" `
    -DestinationPath "..\data" -Force
```

The package **adds** HAM-specific files and does **not** overwrite a previous official numerical QA report or mutate any raster/Parquet outputs.

## QA gate then closure manifest

```powershell
& ..\data\.venv\Scripts\python.exe ..\data\tests\test_m1t_ham_closure.py -v
if ($LASTEXITCODE -ne 0) { throw "Closure tests failed" }

& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\finalize_ham_m1t.py --check
if ($LASTEXITCODE -ne 0) { throw "Hamburg closure QA gate failed" }

& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\finalize_ham_m1t.py --write-manifest
if ($LASTEXITCODE -ne 0) { throw "Hamburg closure manifest not written" }
```

The default `--check` reads the 342 existing batches' inventory and cross-checks the unchanged numeric QA JSON, Phase 3 IDs/count summary, six-case register, two targeted diagnostics and 398 candidate IDs. Use `--deep` to additionally re-hash 342 batch Parquets, both elevation/source-ID mosaics and original buildings GeoPackage.

`--write-manifest` creates `runs/ham_m1_citywide/qa/ham_m1t_closure_manifest.json` and appends a uniquely headed closure paragraph to the **existing** `docs/provenance/HAM_Terrain_Source_Provenance.md`. It does not overwrite the numerical QA report or remove the earlier invalid seam diagnostic.

If a partial failure occurs, inspect the error and existing files rather than repeating `--write-manifest` blindly. The manifest command refuses overwrites.

## Source control

Review source code changes first. Only stage relevant scripts, tests and small scientific documentation, not raw DEMs, the 884 intermediate source GeoTIFFs or the 342 generated Parquet batches. Example from the same PowerShell folder:

```powershell
Push-Location ..\data

git status --short

git add -- docs/qa/HAM_M1T_Spatial_QA.md docs/qa/HAM_M1T_reviewed_cases.csv docs/qa/evidence/ docs/phase4/M1_T_HAM_Closure_Report.md docs/phase4/M1_T_HAM_Closure_README.md docs/provenance/HAM_Terrain_Source_Provenance.md

git add -- scripts/m1t/finalize_ham_m1t.py tests/test_m1t_ham_closure.py

# The remaining existing HAM code and tests can be staged after reviewing git status.
# Examples: prepare_ham_dgm5.py, build_ham_dgm5_mosaics.py,
# extract_ham_terrain_regions.py, qa_ham_citywide.py,
# diagnose_ham_8629_304428.py, diagnose_ham_source_seams.py,
# related source acquisition/conversion code and tests.

# Small reproducibility metadata may be ignored by rules for runs/:
git add -f -- runs/ham_m1_citywide/qa/ham_m1t_closure_manifest.json runs/ham_m1_citywide/qa/ham_m1t_citywide_numerical_qa.json runs/ham_m1_citywide/ham_terrain_source_manifest.json

git diff --cached --stat
# Only commit after checking the staged paths and changes.
git commit -m "docs(m1t): document Hamburg terrain QA and dataset closure"
git push origin phase4/m1t-ham-don

Pop-Location
```

If the documentation/provenance file already has separate user edits, review the diff before committing; do not overwrite them. To preserve full source reproducibility, make sure the HAM generation/extraction scripts and tests from earlier packages are committed as well.

## Reproducible derived-output archive (locally, after Git commit)

```powershell
& ..\data\.venv\Scripts\python.exe `
    ..\data\scripts\m1t\finalize_ham_m1t.py `
    --archive "$HOME\Habnetic\archives\Habnetic_HAM_M1T_2026-11-08_derived.zip"
```

The archive explicitly includes the 342 Parquet results, six final mosaic rasters, source-ID layers, Phase 3 buildings GeoPackage, QA, supporting manifests, scripts/tests, documentation and selected screenshots. A file-by-file SHA-256 inventory is embedded and the ZIP is CRC tested; a separate `.zip.sha256` file is written. It can be **large**. This archive is local and is **not** yet on Google Drive until you upload it.

**Excluded by design:** raw 1 m source elevation archives and 884 intermediate derived tiles. Preserve those original acquisitions separately on Drive under a source-data directory, together with their original checksums and official licence/attribution information. The derived ZIP alone does **not** permit independent reproduction starting only from raw data.

## Expected outputs and decision gate

- QA check: `Hamburg M1-T closure gate: PASS` for **341,530 measured**, **398 candidates**, **6 reviewed**, **392 not individually inspected**.
- Source document: appended explicit closure section, without deleting prior source uncertainty.
- Closure JSON: `runs/ham_m1_citywide/qa/ham_m1t_closure_manifest.json`.
- Git: a commit on `phase4/m1t-ham-don`, performed by the user in their local `data` repository.
- Derived ZIP, `.zip.sha256` file and detailed inventory available locally, then manually uploaded to Drive.

**Research conclusion:** HAM M1-T feature extraction is closed with documented limitations. This is **not** a flood-model validation, nor a claim that all 398 anomalous candidates were individually cleared.
