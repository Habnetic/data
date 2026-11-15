# Habnetic | Operations Center v0.1 — source-file and build inventory

**Inventory date:** 2026-11-15  
**Purpose:** hand-off from frozen Phase 3 and audited M1-G2 research to the Operations Center application.  
**Status:** ready to **start building** the three-city read-only viewer. Not yet a deployed, map-ready product.  
**Repositories:** `resilient-housing-bayes` (science), `data` (data and derived assets), existing `docs` (canonical specification). **No new repository is required.**

## 0. Decisions already made (do not reopen)

- Operations Center is a **research decision workbench**, not a physical terminal: **Explore → Simulate → Decide → Record**. The first release is read-only; simulate/record become real application capabilities only when their scientific pipelines and persistence are implemented.
- Layers stay separate: **scientific engine → versioned data/artifacts → application/API → presentation**. Move the application to a server later without rewriting the science.
- Initial front end: operational dark/amber aesthetic, map and building inspector, model/scenario comparison, text command console for navigation and status. Existing `habnetic.org` remains the separate editorial site.
- For the initial three cities: **RTM / HAM / DON**, Phase 3 (M0) context and **M1-G2 matched B0/B1** comparisons at fixed top 1% for each city's eligible population. The 2026-11-14 *Operations Center v0.1 Maps Amendment* supersedes earlier deferral of citywide maps.
- Three-city M1-G2 is a **synthetic specification-sensitivity experiment**, not empirical flood probability or validated hazard. No inference is executed in the browser; use frozen outputs.
- The lunar L0 panel is a **separate optional module only after audited L0 data exist**. No invented lunar rankings, Concordia outcomes, or facility transfer. M2/M3/M4/5 are subsequent research milestones.

## 1. Existing scientific inputs (`resilient-housing-bayes/`)

**Status key:** `RECORDED` = known from the completed research reports/previous discussion, **not** a new inspection of your Windows disk; `LOCATE` = exact existing path still needs discovery; `GENERATE` = not yet a browser-facing asset.

| Status | Relative path / pattern | Why required |
|---|---|---|
| RECORDED | `configs/m1g_citywide_v0.1.json` | Frozen scenarios, seeds, priors, 1% budget, full population sizes. SHA256 `068b3a5d12b5e2bd410ce6a092cfba520901e2892bedbfa2c71e6b9eeff405c4`. |
| RECORDED | `src/rhb/pipelines/m1g_citywide.py` | Original synthetic data generation, B0/B1 fitting, scoring, comparisons and artifact definitions. |
| RECORDED | `src/rhb/experiments/m1f_population_sampling.py` and `src/rhb/experiments/m1g_cross_city_sampling.py` | Exact source-population adapters and covariate transformations. |
| RECORDED | `RUN_M1G2_ALL.ps1`, `scripts/run_m1g2_all.py`, `README_RUN_ALL.md` | Reproducible execution entrypoint; **do not rerun for viewer creation**. |
| RECORDED | `docs/phase4/M1_G2_Full_City_Protocol.md` | Experimental scientific contract. |
| RECORDED | `docs/phase4/M1_G2_Full_City_Results_2026-11-14.md` | Frozen six comparisons, coefficients and interpretation. |
| RECORDED | `docs/phase4/M1_G2_Visual_Trace_Review_2026-11-15.md` | Trace interpretation for 12 fits. |
| RECORDED | `RUN_M1G2_SCIENTIFIC_AUDIT.ps1`, `scripts/audit_m1g2_full.py`, `tests/test_m1g2_scientific_audit.py` | Numerical audit implementation. |
| RECORDED | `outputs/phase4/_m1g2_scientific_audit_v0.1/{AUDIT_REPORT.md,audit_results.json}` | Scientific audit results. Keep raw outputs local; a small archival copy goes into tracked docs. |
| RECORDED | `RUN_M1G2_GIS_AUDIT.ps1`, `scripts/audit_m1g2_gis.py`, `tests/test_m1g2_gis_audit.py` | GIS audit implementation. |
| RECORDED | `outputs/phase4/_m1g2_gis_audit_v0.1/{GIS_AUDIT_REPORT.md,audit_gis_results.json}` | Automated intermediate GIS record (manual closure below supersedes pending-review status). |
| RECORDED | `docs/phase4/Operations_Center_v0.1_Maps_Amendment.md` | Required three-city maps, map inspector, difference layers and disclaimer. |
| LOCATE | Phase 3/M0 **citywide building-level decision tables** for DON, RTM and HAM | Historical context layer. Exact path and attribute schema not verified by this inventory. RTM covariate input is known as `outputs/phase3/RTM/phase3_features_scaled.parquet`; this is **not automatically a decision-score table**. |
| LOCATE | Original Phase 3 run configuration, posterior summaries and provenance per city | Explain the M0 baseline honestly and avoid presenting newly refitted M1-G2 B0 as the original M0. |

### Frozen M1-G2 study outputs: **all six comparisons + all twelve fits**

Under `outputs/phase4/{CITY}/m1g_citywide_v0.1/`, for each `CITY ∈ {DON,RTM,HAM}`:

```text
preparation_manifest.json
gamma_0_scenario.parquet
gamma_neg0p8_scenario.parquet
gamma_0/
  B0/{idata.nc,posterior_summary.csv,fit_diagnostics.json,citywide_decisions.parquet,scoring_manifest.json}
  B1/{idata.nc,posterior_summary.csv,fit_diagnostics.json,citywide_decisions.parquet,scoring_manifest.json}
  citywide_comparison.parquet
  comparison_manifest.json
gamma_neg0p8/
  B0/{same five files}
  B1/{same five files}
  citywide_comparison.parquet
  comparison_manifest.json
```

**For map construction**, the **six `citywide_comparison.parquet`** files are the primary model-dependent building-level decision inputs; the corresponding six manifests are mandatory. Archive the **twelve `idata.nc`** and scoring files as reproducibility evidence but **never load them into the browser**. The comparisons have **no geometry**. Never replace an M0 layer with M1-G2 B0: B0 was refitted on synthetic outcomes and a matched eligible population.

Expected populations: **DON 7,755**, **RTM 220,456**, **HAM 341,530**; combined eligible **569,741**. Fixed `k`: 78, 2,205 and 3,415. RTM has **868 original Phase 3 buildings with no T50**; label as unscored, not excluded from the historical city inventory.

## 2. Existing geographic / source inputs (`data/`)

These paths are grounded in the M1-G2 data/GIS closure, source scripts and GIS review. They are **local input artifacts, not automatically publishable open-data files**.

| Status | Relative path | Purpose |
|---|---|---|
| RECORDED | `processed/DON/derived/buildings_don.gpkg` | Canonical DON building geometry; CRS EPSG:25830. |
| RECORDED | `processed/RTM/normalized/buildings.gpkg` | Geometry source for RTM’s original 221,324-building Phase 3 cohort; the GPKG may contain additional records. CRS EPSG:28992. |
| RECORDED | `processed/HAM/derived/buildings_ham.gpkg` | Canonical HAM building geometry; CRS EPSG:25832. |
| RECORDED | `processed/DON/derived/mdt05_don_5m_mosaic.tif` | Original DON topography context; 5 m. |
| RECORDED | `runs/rtm_m1_citywide/terrain_features_m1_5m.parquet` | Full RTM terrain measurements and the 868 QC failures; recorded SHA256 `242045b495f547ddaa56f9e130415841831ca85f89de584ff44b3038d0c34711`. |
| RECORDED | `processed/HAM/derived/ham_dgm5_mainland_mosaic.tif` | Mainland terrain mosaic, EPSG:25832, 5 m. |
| RECORDED | `processed/HAM/derived/ham_dgm5_western_islands_mosaic.tif` | Western-islands terrain mosaic, EPSG:25832, 5 m. |
| RECORDED | `processed/HAM/derived/ham_dgm5_mainland_mosaic_source_id.tif` | Pixel-level source provenance, grid-aligned with mainland elevation. |
| RECORDED | `processed/HAM/derived/ham_dgm5_western_islands_mosaic_source_id.tif` | Pixel-level source provenance, grid-aligned with western-islands elevation. |
| RECORDED | `runs/ham_m1_citywide/qa/ham_dgm5_citywide_manifest.json` | 884 tile records: HH 880, SH 2, NI 1, WSV 1; source hashes and processing decisions. |
| RECORDED | `scripts/rtm/{m1_extract_terrain_citywide.py,m1_consolidate_terrain.py}` | Exact Rotterdam 20-valid-pixel per region eligibility rule. |
| RECORDED | `scripts/m1t/{build_ham_dgm5_mosaics.py,extract_ham_terrain_regions.py}` | Two-mosaic construction and regional assignment logic. |
| **NEW IN HANDOFF** | `docs/phase4/M1_G2_DATA_GIS_AUDIT_CLOSURE_2026-11-15.md` | Final accepted data/GIS audit; keep earlier automated reports unchanged. |
| **NEW IN HANDOFF** | `docs/phase4/OPERATIONS_CENTER_INPUT_MANIFEST_2026-11-15.md` | **This** handoff and inventory. |
| **NEW IN HANDOFF** | `docs/phase4/M1_G2_FROZEN_ARTIFACT_INDEX_2026-11-15.json` | SHA256/size reference for the M1-G2 frozen research artifacts, generated on workstation during archive. |

**Research caveat:** DON extremes were reviewed as geographically plausible; RTM 868 missing T50 all explained by the 20+20 pixel rule (854 local-only, 14 both, 0 neighbourhood-only); HAM mosaics aligned and provenance tracked; exact tile-level vertical-datum/seam equivalence **not** independently verified. This is **closed GIS QA for a synthetic experiment**, not empirical flood-risk validation.

## 3. Existing design contract (`docs/`)

| Status | Relative path | Notes |
|---|---|---|
| RECORDED BY PRIOR DESIGN | `phase4/Operations_Center_v0.1_Specification.md` | Original read-only spec, commands, map, inspector, deployment expectations. Check actual repository location before use. |
| RECORDED | `resilient-housing-bayes/docs/phase4/Operations_Center_v0.1_Maps_Amendment.md` | **Overrides** the older specification where it deferred citywide M0/M1 maps. Copy or reference amendment in canonical `docs` only during implementation. |
| LOCATE | Existing V7 Operations Center HTML prototype and amber brand assets | **Design references**, not an approved production app. They may live outside the scientific/data repositories. |

## 4. Files still to GENERATE for the Operations Center v0.1

The research **does not produce these automatically**. These are the remaining engineering deliverables, not unfinished M1-G2 inference or GIS audits.

| Proposed artifact (relative to existing `data` / application working tree) | Required? | Contract |
|---|---|---|
| `data/public/oc/v0.1/manifest.json` | YES | Versioned public index: publication version, synthetic evidence flag, area IDs, model/scenario availability, source analysis Git tag/commit, hashes, licenses. |
| `data/public/oc/v0.1/areas/{RTM,HAM,DON}.json` | YES | CRS, counts, available M0/M1 layers, k, defaults, provenance, legal attribution, limits, bounding box. Never overstate empirical meaning. |
| `data/public/oc/v0.1/summary/{CITY}/{gamma}.json` | YES | Curated citywide B0/B1 metrics and manifest hashes; six comparison summaries. |
| `data/public/oc/v0.1/tiles/{CITY}/{scenario}/...` | YES | **Vector tiles / PMTiles / equivalent browser-efficient spatial layers** from joining authoritative geometries to comparison Parquet on unique `bldg_id`. Avoid one 569k-feature GeoJSON. Store selection class and numeric change attributes. |
| `data/public/oc/v0.1/terrain/{CITY}/...` | OPTIONAL for first usable comparison map | DEM/hillshade web tiles after permitted redistribution; show sourced terrain context and accessible attribution. |
| `data/public/oc/v0.1/provenance/{CITY}.json` | YES | Geometry license, original-source/version hashes, terrain caveat, transformation schema, model run ID and evidence status. |
| `data/scripts/oc/build_public_map_assets.py` | YES (proposed path) | Deterministic exporter: validates joins, counts, `k`, `sum(p_topk)=k`, CRS, missing RTM T50; generates manifest + tiles. This script **does not yet exist**. |
| `data/scripts/oc/validate_public_map_assets.py` | YES (proposed path) | Independent QA of public tiles/index/IDs/source hashes and disclosure labels. |
| `data/docs/phase4/OPERATIONS_CENTER_DATA_CONTRACT.md` | YES (proposed path) | Stable schemas for `ResearchArea`, building inspector, source provenance, model/scenario results and map layer semantics. |
| `docs/phase4/Operations_Center_v0.1_Specification.md` updated with amendment | YES | Canonical product specification in existing docs repository; preserve original revision history. |
| Operations Center application code (`app/`, `ui/` or existing established location) | YES | MapLibre-based 2D map, building inspector, side-by-side M0/M1 and B0/B1, delta toggle, status console, accessible labels, read-only local/hosted serving. **Final app path depends on existing repo architecture; do not make a new repo by default.** |
| `README.md` / `Makefile` or one-command launcher and tests | YES | One command for local viewer, exact data expected, integrity tests, build steps, publication version. |

### Expected joined attributes for the building inspector

`bldg_id`, `city`, `scenario`, `model`, `evidence_type=synthetic`, `T50` (m), `p_mean`, `p_topk`, `selected_by_p_mean`, `rank_sd` (or recorded rank-variability field), decision-change class (`stayed/entered/left/unselected`), `delta_p_topk`, `k`, `run_id`, `source_hash`. **Use exact exported column names from the Parquet schema**; the list is an interface requirement, not an assertion that every column is identically named across files.

A MapLibre map must transform display coordinates correctly from original local projected CRSs. Treat missing terrain/eligible geography explicitly; do not place longitude/latitude values in metres or treat `T50` as absolute altitude.

## 5. Minimum build order (not another research audit)

1. **Archive:** commit the M1-G2 closure documents, code and summary evidence; create annotated tags in **science and data**; push. Preserve large Parquet/NetCDF/GeoTIFF files locally with SHA256 index and backup. **Do not publish raw geometries or DEMs before checking city-specific licenses.**
2. **Join one city first:** DON has 7,755 eligible footprints; join one existing `citywide_comparison.parquet` by unique `bldg_id` and validate counts, CRS and selection cardinality; export browser-efficient layer.
3. **Implement a read-only viewer** with a city selector, DON map, scenario switch, B0/B1 difference and inspector; then add RTM and HAM through the identical contract.
4. **Add M0 context** after locating its actual per-building outputs. M0 is historical Phase 3; it must remain distinct from synthetic M1-G2 B0.
5. **Publish** only versioned, licensed map exports and summary JSON through existing GitHub-backed static hosting. Later server migration changes the application/artifact service, not the scientific engine.

## 6. Archive tags and verification boundaries

Suggested **annotated tags in separate Git repositories**, both pointing at their respective archive commits:

- Science: `phase4-m1g2-scientific-audit-2026-11-15`.
- Data: `phase4-m1g2-data-gis-closure-2026-11-15`.

These denote an **audited synthetic M1-G2 milestone**, **not** empirical model validation or completed M1-G1/M1-G2 cross-experiment synthesis. Do not create retroactive tags for Phase 3/M0/M1-G1 without first inspecting their actual existing tags/commit hashes.

**Important:** An annotated Git tag records **repository state**, not ignored binaries or unpushed local files. The frozen-artifact SHA256 index must be committed and copied to an independent backup with those binaries. The included PowerShell publishing script prints the current branch, checks existing tags, archives an inventory and pushes only explicit Git-scoped files. It never runs full Bayesian fits or silently force-pushes.

### Assumptions made

Windows workspace root `C:\Users\C.Price\Habnetic`, two existing Git repositories (`resilient-housing-bayes`, `data`) and a separate `docs` repository. These are user-reported locations and require workstation verification. Scientific conclusions are accepted within synthetic scope; OC is an application built **on** the evidence, not a new scientific claim.

### How to validate

Run `Publish-M1G2-Audit.ps1` from the attached package. It checks expected source files and frozen outputs, creates hashes, stages a tightly scoped archive, commits, tags and attempts the pushes using your Windows Git authentication. Then check `git status` and both tag pointers.

### Next small step

After both archive tags are pushed, implement DON's first map-ready B0/B1 join. Do **not** begin with new PyMC sampling, yet another GIS audit or an invented lunar inference dataset.
