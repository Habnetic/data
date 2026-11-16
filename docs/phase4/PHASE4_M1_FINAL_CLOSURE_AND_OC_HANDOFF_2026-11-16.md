# Habnetic | Phase 4 M1 — Research Closure and Operations Center Handoff

**Closure record:** 2026-11-16
**Decision:** **CLOSE Phase 4 M1 as the completed topographic/synthetic research milestone; accept its frozen Phase 3 + M1-G2 inputs for Operations Center data integration.**
**Scope:** The historical M1 experiment family, the completed full-city M1-G2 analysis, its scientific and GIS audits, and the subsequent *read-only* source discovery for the urban Operations Center.
**Not claimed:** Empirical flood-risk validation, completed Operations Center deployment, an exhaustive scientific synthesis comparing every earlier M1 experiment, or completed single-facility/lunar research.

## 1. Decision and boundaries

The research and audit work needed to **begin implementing** the three-city Operations Center is complete. The remaining steps are application/data engineering: check building-ID joins and selection semantics, determine redistribution permissions, and export browser-ready spatial assets. These are **not reasons to reopen M1-G2 inference or its closed GIS audit**.

The original Phase 3 results and the later M1-G2 `B0` fits are **different analyses**. They must remain distinct in the interface, with explicit provenance, populations, synthetic-evidence warnings and top-*k* definitions.

**M1-G2 is a controlled synthetic specification-sensitivity experiment**, using observed geometries and derived terrain but synthetically generated Bernoulli outcomes. It does not estimate or validate actual flood-damage probabilities.

## 2. Research completed

### Phase 3 / M0 source baseline

Original Phase 3 per-building `asset_metrics.parquet`, `run_metadata.json`, and `decision_metrics.json` are physically present for **all three cities (9/9 core files)**. The original building geometries are also present (**3/3 GPKGs**). Phase 3 per-building schemas were inspected by the local read-only inventory tool.

| City | Phase 3 buildings | Original Phase 3 top-*k* field (approximately top 1%) | Original Phase 3 `k` |
|---|---:|---|---:|
| Donostia (DON) | 7,755 | `topk_prob_k78` | 78 |
| Rotterdam (RTM) | 221,324 | `topk_prob_k2213` | 2,213 |
| Hamburg (HAM) | 341,530 | `topk_prob_k3415` | 3,415 |

Original Phase 3 `asset_metrics.parquet` schemas include `bldg_id`, `p_mean`, `p_std`, `topk_prob_k...` and `rank_std_k...` fields for several budgets. Phase 3 `phase3_features_scaled.parquet` exists for each city and contains covariate/source fields, **but is not itself a historical decision-score table**. The source scan establishes existence and basic schema, not final geometry-join or semantic validation.

### Phase 4 M1-G2: full-city terrain sensitivity

Three cities, two synthetic terrain-effect scenarios (`gamma_true` 0 and -0.8), and two matched within-city Bayesian models:

- `B0`: original E/H predictor structure, fitted to the M1-G2 synthetic outcomes.
- `B1`: E/H plus transformed relative terrain `T = asinh(T50 / 0.5 m)`, where `T50 = local_z_50 - neighbourhood_z_50` in metres.
- **12 full Bayesian fits**, **6 B0/B1 comparisons**, all on the respective eligible full-city populations.
- Shared selection budget within each city/scenario: top ~1% by posterior mean event score; posterior `p_topk` is a separate *posterior inclusion frequency*, not the selected-set rule.

| City | M1-G2 eligible | Excluded vs Phase 3 | M1-G2 `k` | Entries into B1 selected set, gamma=0 | Entries, gamma=-0.8 |
|---|---:|---:|---:|---:|---:|
| DON | 7,755 | 0 | 78 | 0 | 49 (62.82% of `k`) |
| RTM | 220,456 | 868 | 2,205 | 7 | 493 (22.36% of `k`) |
| HAM | 341,530 | 0 | 3,415 | 26 | 1,511 (44.25% of `k`) |
| **Total eligible** | **569,741** | **868** | **5,698** | — | — |

Results establish *decision-set sensitivity under the synthetic generator*, not a measured reduction in flood losses. The negative terrain-effect scenario is an intentionally informative positive control; under the zero-effect control the selected sets change little.

### Scientific audit

- All **81/81 frozen M1-G2 artifacts** were found in the later independent read-only source inventory.
- Six comparison Parquets and their six comparison manifests were found (**12/12**).
- Original automated test run, convergence checks (R-hat/ESS/divergences), scientific audit, posterior predictive diagnostics, prior sensitivity by *importance reweighting* and twelve-fit visual trace review were documented in their existing reports.
- Scientific audit verdict: **automated checks passed with scoped limitations**. The posterior predictive checks use synthetic outcomes. Approximate prior reweighting does not constitute independent refits under alternative priors/likelihoods.
- The model's H covariate has a narrow across-building range, limiting interpretation of the corresponding regression coefficient; the audit records this explicitly.

### GIS and source-data audit: closed with limitations

**Donostia:** 7,755/7,755 geometries matched. Positive and negative extreme T50 values were inspected in QGIS and judged geographically plausible in steep/elevated and valley terrain. Visual plausibility is not exact numerical verification of terrain extraction.

**Rotterdam:** all 221,324 original building IDs have terrain-table rows; **868** have missing T50. The source eligibility rule (`local_valid_pixels >= 20` **and** `neighbourhood_valid_pixels >= 20`) was independently reconstructed for **every row** with **zero mismatches**. Rejection reasons: **854** local-only, **14** both, **0** neighbourhood-only. Some exclusions cluster geographically, but the available mapped-water-distance proxy did **not** show an overall enrichment of exclusions near water. The B0/B1 comparison consistently uses the 220,456 eligible buildings; the 868 remain present in the Phase 3 historical population.

**Hamburg:** 341,530/341,530 geometries matched. Both mainland and western-island DEM/source-ID pairs use aligned 5 m EPSG:25832 grids. The source manifest records **884 tiles**: Hamburg LGV 880, Schleswig-Holstein 2, Niedersachsen 1, WSV/Scharhoern 1. Provider-level datum documentation supports a common height reference, but **exact tile-level vertical-datum equivalence and mosaic-seam continuity were not independently verified**. This is an explicitly accepted limitation for the synthetic experiment, not a validated physical flood model.

**GIS decision:** `CLOSED — ACCEPTED WITH DOCUMENTED LIMITATIONS` as recorded on 2026-11-15; no evidence from the audit warrants editing frozen data or refitting.

## 3. Git freeze and reproducibility record

**Science repository:** `Habnetic/resilient-housing-bayes`

- Branch: `phase4/m1g-cross-city`
- Audited archive commit: `507adc4c0e899ba01b583c35e572eb2f0faf3d47`
- Published annotated tag: `phase4-m1g2-scientific-audit-2026-11-15`
- Earlier recorded code/research tags: `phase3-code-freeze-20261022`, `phase4-m1-complete-v1.0`

**Data repository:** `Habnetic/data`

- Branch: `phase4/m1t-ham-don`
- GIS/archive commit: `b3878587997a98a32cbd0eaf39f00d9a6054c412`
- Published annotated tag: `phase4-m1g2-data-gis-closure-2026-11-15`

Frozen binaries (`.parquet`, `.nc`, `.tif` and relevant GPKGs) are **not thereby published on GitHub**. Their large-file preservation/backups remain separate from Git; an existing SHA-256 index in `data/docs/phase4/M1_G2_FROZEN_ARTIFACT_INDEX_2026-11-15.json` records research artifact fingerprints. An annotated Git tag freezes tracked repository contents, **not ignored local data**.

Core tracked documents:

- Science: `docs/phase4/M1_G2_Full_City_Protocol.md`, `docs/phase4/M1_G2_Full_City_Results_2026-11-14.md`, `docs/phase4/M1_G2_Visual_Trace_Review_2026-11-15.md`, `docs/phase4/audits/M1_G2_AUDIT_REPORT_2026-11-15.md`, `docs/phase4/audits/M1_G2_GIS_AUDIT_REPORT_2026-11-15.md`.
- Data: `docs/phase4/M1_G2_DATA_GIS_AUDIT_CLOSURE_2026-11-15.md`, `docs/phase4/OPERATIONS_CENTER_INPUT_MANIFEST_2026-11-15.md`, `docs/phase4/M1_G2_FROZEN_ARTIFACT_INDEX_2026-11-15.json`.

## 4. November 15 source-handoff verification

A *read-only* inventory ran on the Windows workstation and reported:

| File family | Located |
|---|---:|
| M1-G2 frozen experiment artifacts | **81 / 81** |
| M1-G2 comparison tables + comparison manifests | **12 / 12** |
| Phase 3 core (`asset_metrics`, `run_metadata`, `decision_metrics`) across three cities | **9 / 9** |
| Original city geometry GPKGs | **3 / 3** |

The inventory found **no mandatory source paths missing** at their expected locations. It also discovered historical earlier-M1 and other Phase 4 file families; it did **not** validate every historical experiment's semantics, nor certify publication rights or spatial joins.

Local generated evidence (generated outside Git repositories):

```text
C:\Users\C.Price\Habnetic\_oc_inventory_reports\latest\
  source_handoff_status.md
  phase3_field_report.md
  inventory.json
  inventory.csv
  git_refs.json
  lineage_references.json
```

The two summary reports should be copied into the data repository alongside this closure record to make the source-discovery decision inspectable in Git. The full machine-generated inventory remains on the workstation unless separately reviewed and approved for publishing; it includes local filesystem paths.

## 5. What is closed vs what is not

### Closed at this milestone

1. Phase 4 M1-G2 controlled synthetic inference, paired comparisons and numerical auditing.
2. M1-G2 GIS review and Rotterdam terrain-eligibility explanation.
3. Git scientific/data audit freeze and published annotated milestone tags.
4. Discovery of mandatory **Phase 3 and M1-G2 urban source files** and their initial Phase 3 per-building schemas.

### Explicitly *not* part of this closure

- A complete scientific cross-comparison/synthesis of all earlier **M1-C/D/E/F/G1** experiments against M1-G2. Earlier experiments are historical research and may be inspected when scientifically justified; the initial viewer does not need to rerun or homogenize them.
- Geometry-to-score join uniqueness, exact historic selection semantics, map export integrity and geographic-data redistribution licenses. These are the **first Operations Center engineering/publication acceptance gates**.
- Browser-ready vector tiles/PMTiles, public JSON endpoints, UI, console, application build or deployment.
- M2/M3 and later hazard/impact model improvements.
- Verified datasets, physical models or probabilistic outputs for **Jungfraujoch**, **Concordia Research Station** or a **lunar south-pole candidate**. Those are independent future facility/lunar research tracks, not dependencies of the urban read-only application.
- Observed flood damage calibration or independent validation of flood probabilities.

## 6. Operations Center handoff contract

**Implement a static, versioned, read-only urban research viewer first.** Keep the research engine independent from the data publication pipeline, application logic and presentation.

Source inputs:

- Phase 3 **original** `asset_metrics.parquet`, run metadata, decision metrics and building geometries per city.
- M1-G2 six `citywide_comparison.parquet` files and paired `comparison_manifest.json` files, plus original geometry and source evidence.
- Scientific and GIS closure reports, frozen-artifact index and version/tag references.

Mandatory engineering validation before public release:

1. Verify **city + `bldg_id`** joins, unique IDs and per-analysis population definitions. RTM Phase 3 and M1-G2 populations differ by 868; do not hide them or silently assign M1-G2 scores.
2. Validate source field semantics, scoring/selection/top-*k* cardinality, units and artifact hashes.
3. Review source licenses and publication/attribution requirements for each city's geometries/terrain.
4. Generate versioned, browser-efficient public map assets and summaries, with synthetic-evidence labels and provenance.
5. Build the interactive urban map/inspector/terminal, initially in static hosting; model inference stays outside the browser.

**Recommended first implementation slice:** DON with the original Phase 3 map context and one frozen M1-G2 B0/B1 comparison, followed by RTM and HAM using the same artifact contract.

**Operations Center design direction already agreed:** one static GitHub-backed research workbench with three long-term environments: **Urban Regions**, **Isolated Facilities (Jungfraujoch / Concordia)** and **Lunar South Pole**. The latter two must indicate missing scientific data/results rather than displaying fabricated analyses.

## 7. Final decision

**M1 scientific milestone and the source-discovery handoff for the urban viewer: CLOSED at their stated scope, 2026-11-16.** Existing research tags remain unchanged. The next workstream is **Operations Center OC-M0 — data integration and publication preparation**, not another terrain or Bayesian audit.

**This document is a handoff/decision record**, not a retrospective redefinition of earlier Git releases and not proof that the web application is already deployable. Start OC engineering with the verified source files; treat unresolved joins, licenses and map exports as OC tasks.

### How to reproduce / review

- Read the existing science and data archive tags and their tracked audit reports.
- Inspect `source_handoff_status.md` and `phase3_field_report.md` from the read-only `oc_inventory.py` run; original scanner invocation used:

```powershell
& "C:\Users\C.Price\Habnetic\resilient-housing-bayes\.venv\Scripts\python.exe" `
  "C:\Users\C.Price\Habnetic\_oc_handoff\oc_inventory.py" `
  --workspace "C:\Users\C.Price\Habnetic"
```

- Inputs: existing local Phase 3 and Phase 4 research artifacts, Git repositories and geometries.
- Outputs: six read-only inventory reports in `_oc_inventory_reports/latest/`.
- No Bayesian fitting, edits to frozen artifacts or Git writes are needed for verification.

**Assumptions made:** the local source scan reports refer to the same frozen files and Git state captured in the November 15 archival record.
**How to validate:** inspect the two original reports and archived SHA-256/Git references; defer join/redistribution validation to OC-M0.
**Next small step:** commit this closure record and the two inventory summaries to `data`, then begin OC-M0 in a separate engineering workflow.
