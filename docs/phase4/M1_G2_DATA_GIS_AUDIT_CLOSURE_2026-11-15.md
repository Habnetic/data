# Habnetic | Phase 4 — M1-G2: Data, GIS and Scientific Audit Closure

**Record date:** 2026-11-15  
**Scope:** `M1-G2` full-city controlled synthetic experiment, covering DON, RTM and HAM  
**Data-repository destination:** `data/docs/phase4/M1_G2_DATA_GIS_AUDIT_CLOSURE_2026-11-15.md`  
**GIS/data audit decision:** **CLOSED — ACCEPTED WITH DOCUMENTED LIMITATIONS**  
**Entire M1-G2 scientific release/tag:** **NOT DECLARED BY THIS RECORD**; comparison with M1-G1 and archival/release decisions are separate work.  
**Data handling:** Read-only review; no frozen inputs, posterior files or model results were changed.

> **Non-negotiable interpretation boundary.** M1-G2 uses real building geometries and real derived terrain covariates, but **synthetically generated Bernoulli outcomes**. Its positive-control data-generating model intentionally includes terrain. It does **not** validate real flood-damage probabilities, present-day inundation, causal physical terrain effects, or transfer of fitted parameters between cities.

## 1. Purpose and decision

This is a **single retrospective closure record** for the information recovered and audited during the 2026-11-14–15 M1-G2 discussions, including the *Operations Center Roadmap* project conversation, run reports, automated audits, QGIS inspection and original `data` preprocessing scripts. It supersedes the **manual-review status** of earlier automated GIS reports; those original reports and their timestamps should be retained unchanged.

**Decision (2026-11-15):** The geographic inputs and exclusions are sufficiently identified, consistent and traceable for the stated **synthetic specification-sensitivity experiment**. The GIS investigation is closed. Remaining limitations are disclosed below; no evidence from this audit warrants modifying the terrain files or rerunning the twelve Bayesian fits.

This decision is **not** a claim of exact terrain accuracy, independent vertical-datum harmonisation or empirical validation. Do not reopen GIS QA without material new evidence; further physical terrain validation belongs to future method development, not a prerequisite invented after closure.

## 2. Experimental design and what the results mean

Three cities, two synthetic scenarios (injected transformed-terrain coefficient `gamma_true = 0` or `-0.8`) and two separately fitted within-city models:

- **B0:** logistic Bernoulli model using Phase 3 predictors `E_hat_v0` and `H_pluvial_v1_logrel`.
- **B1:** same model plus terrain `T = asinh(T50 / 0.5 m)`.
- `T50 = local_z_50 - neighbourhood_z_50` in **metres**; it is a **relative-terrain measure**, not absolute altitude.
- Synthetic generator: `logit(p_true) = -3 + E + H + gamma_true*T`; `Y_synthetic ~ Bernoulli(p_true)`.
- Priors: `alpha, beta_E, beta_H ~ Normal(0, 2.5)`; B1 `gamma_T ~ Normal(0, 0.5)`.
- Inference: PyMC NUTS, 4 chains, 1,000 warmup and 1,000 retained draws per chain, `target_accept = 0.90`; each run scores the **full eligible city population**, using 1,000 posterior coefficient draws for posterior top-k estimates.
- Budget `k = round(0.01*N)`; B0 and B1 share exactly the same eligible population, generated outcomes and top-k budget within each city/scenario.
- `p_topk` measures posterior selection frequency, whereas the reported selected set is the top-k **posterior mean event score**. These must not be conflated.
- Oracle regret is the difference in **expected synthetic events captured** between the known generating-probability oracle top-k and the model top-k. It is **not** observed damage, money or a normalised cross-city metric.

| City | Phase 3 geometries | M1-G2 eligible | Excluded | k (1%) | Geometry CRS |
|---|---:|---:|---:|---:|---|
| DON: Donostia / San Sebastián | 7,755 | 7,755 | 0 | 78 | EPSG:25830 |
| RTM: Rotterdam | 221,324 | 220,456 | 868 | 2,205 | EPSG:28992 |
| HAM: Hamburg | 341,530 | 341,530 | 0 | 3,415 | EPSG:25832 |
| **Total** | **570,609** | **569,741** | **868** | **5,698** | — |

**Completed:** 12 full-city B0/B1 fits, 6 paired comparisons. The earlier M1-G1 5,000-building experiments and the original Phase 3 fits are **different experiments**; there is no cross-city hierarchical transfer or common estimated city coefficient here.

## 3. Frozen full-city results (for cross-reference, not new fits)

This table is reproduced from the existing M1-G2 scientific results record and independent automated audit. The replacement denominator is the **selection budget k**, not the city population.

| City | Injected γ | N | k | B0/B1 shared selected | B1 entries / B0 exits | Share replaced | Borderline B0→B1 | Oracle regret B0→B1 |
|---|---:|---:|---:|---:|---:|---:|---|---|
| DON | 0 | 7,755 | 78 | 78 | 0 | 0.00% | 10→24 | 0.000000→0.000000 |
| RTM | 0 | 220,456 | 2,205 | 2,198 | 7 | 0.32% | 26→64 | 0.002933→0.015649 |
| HAM | 0 | 341,530 | 3,415 | 3,389 | 26 | 0.76% | 46→79 | 0.005606→0.067903 |
| DON | -0.8 | 7,755 | 78 | 29 | 49 | 62.82% | 14→10 | 31.367451→0.003040 |
| RTM | -0.8 | 220,456 | 2,205 | 1,712 | 493 | 22.36% | 35→68 | 59.120462→0.009864 |
| HAM | -0.8 | 341,530 | 3,415 | 1,904 | 1,511 | 44.25% | 47→100 | 282.578002→0.130386 |

B1 posterior terrain-coefficient recovery (`gamma_T` posterior mean [95% HDI]):

| City | γ=0 | γ=-0.8 |
|---|---|---|
| DON | -0.001 [-0.028, 0.028] | -0.810 [-0.851, -0.768] |
| RTM | 0.012 [-0.030, 0.055] | -0.797 [-0.839, -0.757] |
| HAM | -0.017 [-0.036, 0.003] | -0.819 [-0.837, -0.799] |

All six HDIs include the injected terrain coefficient. This is *synthetic parameter recovery under the chosen generator*, not an independent empirical predictive success. Under γ=0, selected sets change little; under γ=-0.8, B1 captures the terrain term intentionally used to generate outcomes, and synthetic oracle regret drops sharply.

### Existing statistical checks

- Original execution: `25 passed` in the M1-G2 pytest run; all twelve full fits completed runner gates (`R-hat <= 1.01`, adequate bulk/tail ESS, zero divergences).
- Independent scientific-audit report timestamp `2026-11-15T15:39:41.366543+00:00`, status `AUTOMATED_CHECKS_PASS_WITH_SCOPED_LIMITATIONS`.
- Four-chain visual trace review for all twelve fits: `VISUAL_TRACE_REVIEW_PASS_WITH_LIMITATIONS`, no persistent drift/trapping observed.
- Feature-stratified **synthetic** posterior predictive checks: some B0 misses, especially when γ=-0.8 deliberately makes B0 misspecified; B1 generally fits the synthetic strata, with a residual HAM T-bin miss reported for γ=-0.8. These are not empirical flood validation.
- Alternate B1 terrain priors σ=0.25 and 1.0 assessed by **importance reweighting**, not fresh NUTS refits; importance ESS reported high (minimum approximately 959.5 among listed cases). Small top-k changes in sensitivity review. This remains an approximation.
- Draw-split top-k Monte Carlo sensitivity inspected in the scientific audit; consult the original report for per-fit maxima.
- `H_pluvial_v1_logrel` has very small across-building SD (DON ~0.01606; RTM ~0.00757; HAM ~0.00670), contributing to difficult interpretation of `beta_H`. Broad coefficient uncertainty is not by itself an MCMC convergence failure.

## 4. DON | Geographic audit: **CLOSED, visually plausible**

**Geometry:** 7,755/7,755 terrain-eligible buildings successfully matched to the authoritative geometry file; no invalid geometry recorded in the GIS join. Projection EPSG:25830.

**Raster reviewed:** `data/processed/DON/derived/mdt05_don_5m_mosaic.tif` (IGN/CNIG MDT05-derived 5 m mosaic). Original survey vintages and vertical datum have not been independently audited per tile in this closure.

**T50 distribution:** min **-23.459 m**, median **+0.169 m**, max **+43.269 m**; 4 values `< -20 m`, 22 values `> +20 m`, total **26** extreme values; 100 review observations exported as `DON_T50_extremes_review.geojson`.

**QGIS manual examination (2026-11-15):**

1. Positive extreme, building `bldg_id=193156`, `T50≈+43.269 m`: inspected in steep island/coastal topography; the large difference relative to the neighbourhood is geographically plausible.
2. Negative extreme, `T50≈-23.459 m`: inspected in a valley/lower-lying corridor; the negative relative elevation is geographically plausible. The negative building ID was **not independently recorded** in this closure; do not invent it.
3. Wider geographical view showed strong Donostia relief. **Only the two inspected extremes** received specific visual confirmation; other extreme observations were not individually certified.

**Decision:** Retain all 7,755 T50 values. No evidence of gross outliers requiring deletion or recomputation. **Limit:** visual geographic plausibility does not independently reproduce exact neighbourhood aggregation, NoData treatment or vertical reference; those questions do not block this synthetic-scope GIS closure.

## 5. RTM | Missing terrain: **CLOSED, rule independently reproduced**

**Geometries:** 220,456/220,456 eligible buildings matched plus geometries located for all 868 excluded original Phase 3 records; projection EPSG:28992. Full original population: 221,324. Original terrain table includes **all** IDs, including exclusions:

`data/runs/rtm_m1_citywide/terrain_features_m1_5m.parquet`

Recorded original table SHA-256: `242045b495f547ddaa56f9e130415841831ca85f89de584ff44b3038d0c34711`.

**Observed:** All 868 excluded rows have `T50 = NaN` and `terrain_measured = False`; the 220,456 eligible have non-missing T50 and `terrain_measured = True`. There are no missing terrain-table records.

**Original rule recovered from preprocessing source:**

- `data/scripts/rtm/m1_extract_terrain_citywide.py` lines 170–174 initially marks `terrain_measured` when local and neighbourhood elevation statistics are finite.
- `data/scripts/rtm/m1_consolidate_terrain.py` lines 134–139 asserts exact agreement with:

```python
expected_measured = (
    (df["local_valid_pixels"] >= 20)
    & (df["neighbourhood_valid_pixels"] >= 20)
)
assert (df["terrain_measured"].astype(bool) == expected_measured).all()
```

- The threshold uses **absolute numbers of valid pixels in both sampling regions**, not percentage coverage. Hence some accepted rows have a lower coverage *fraction* than some rejected rows.

**Independent read-only replay of all 221,324 rows (2026-11-15):**

| Result | Count |
|---|---:|
| Accepted | **220,456** |
| Rejected | **868** (0.392% of original population) |
| Local `<20` valid pixels, neighbourhood `>=20` | **854** |
| Local `<20` and neighbourhood `<20` | **14** |
| Local `>=20`, neighbourhood `<20` | **0** |
| Eligibility/flag mismatches | **0** |
| Accepted with missing T50 | **0** |
| Rejected with nonmissing T50 | **0** |
| Finite-statistics/flag mismatches | **0** |

**Coverage fractions (secondary descriptive information):**

| Measure | Eligible median | Excluded median | Excluded max |
|---|---:|---:|---:|
| Local valid-pixel fraction | 75.3425% | 22.5352% | 36.5385% |
| Neighbourhood valid-pixel fraction | 75.9903% | 55.5731% | 87.9282% |

**QGIS geography and water-proximity hypothesis:** Clusters are visible around river/harbour infrastructure in the inspected screenshots, but the Phase 3 `dist_to_water_m` field **does not** support general water-proximity enrichment in the excluded population:

| Distance threshold | Eligible within threshold | Excluded within threshold |
|---|---:|---:|
| 25 m | 4.22% | 1.15% |
| 50 m | 9.33% | 1.96% |
| 100 m | 23.79% | 5.53% |

This rejects the **specific claim that exclusions are more common near mapped water as measured by that proxy**. It does **not** prove that local NoData, river edge, harbour processing, or spatially structured missingness are absent: the water proxy may miss some water infrastructure and cluster comparisons need suitable denominators. Exact physical causes of individual invalid elevation pixels were not established.

**Decision:** Exclusion is deterministic, completely reproduced and explicitly limited to 868 buildings. Use the frozen **matched** 220,456-building population for both B0 and B1. Do not impute or change these records retrospectively; avoid extrapolating results automatically to the 868 omitted buildings.

## 6. HAM | Multi-provider terrain provenance: **CLOSED WITH LIMITATION**

**Geometries:** 341,530/341,530 building IDs matched; EPSG:25832. No buildings excluded from the eligible population. The initial failure of a single mainland raster to cover all geometry is **not an M1-G2 data failure**: the actual extraction explicitly uses **two separate regional mosaics**.

**Original source pipeline:**

- `data/scripts/m1t/build_ham_dgm5_mosaics.py` builds regional DGM5 composites and pixel-level `_source_id.tif` provenance grids.
- `data/scripts/m1t/extract_ham_terrain_regions.py` loads both mainland and western-islands rasters, validates source-ID grid alignment, and uses the common terrain extraction core.
- Region assignment: centroid `x < 500000` ⇒ `western_islands`; `x > 540000` ⇒ `mainland`; gap ⇒ explicit error. These are projected X coordinates in EPSG:25832; do not interpret them as longitude.
- Mosaic target grid: 5 m, composed from aligned 1 m data, using the **masked mean of 25** 1 m pixels. Manifest source-fraction acceptance rule: **`source valid fraction >= 1.0`**. An explicit invalid value of `-9999.0` is tracked. Raster source precedence and provenance IDs are coded rather than inferred from filenames.

**Verified raster pairs (2026-11-15):**

| Property | Mainland | Western islands |
|---|---|---|
| DEM | `ham_dgm5_mainland_mosaic.tif` | `ham_dgm5_western_islands_mosaic.tif` |
| CRS | EPSG:25832 | EPSG:25832 |
| Pixel resolution | 5 × 5 m | 5 × 5 m |
| Dimensions | 8,200 × 8,000 | 1,200 × 1,400 |
| NoData | -9999.0 | -9999.0 |
| `_source_id.tif` grid matches DEM (CRS, transform, dimensions) | **PASS** | **PASS** |

**Manifest:** `data/runs/ham_m1_citywide/qa/ham_dgm5_citywide_manifest.json`, generated `2026-11-08T17:44:52.079328+00:00`, `phase=M1-T`, `mode=all`, `count=884` source tile records. Provenance counts:

| Code/source label | Recorded tile count | Meaning |
|---|---:|---|
| `LGV_HH_2022` | **880** | Hamburg LGV tile source label |
| `LVERMGEO_SH_2021` | **2** | Schleswig-Holstein LVermGeo |
| `LGLN_NI_2025` | **1** | Niedersachsen LGLN |
| `WSV_DGMW_2022_SCHARHOERN` | **1** | WSV/Scharhörn |
| **Total** | **884** | *Number of manifest tile records, NOT number of building rows or per-pixel source shares.* |

Recorded package/archive SHA-256 fingerprints:

```text
input_archive_sha256: 32b8d624af3000aa8257205b8701d6389b2a08d6c41a8b78850e6c6863be94f2
supplemental_ni_sha256: 695acc10fe4bc04079df8d59629ab04c7e7380bcab6f63360a6f5f9201794a37
supplemental_wsv_sha256: b6582f0a656276b33ba4b76a8ae040f6491b85b3376a769cb917d67e32915538
```

**Manifest caveat (preserved verbatim):**

> Geometric and source-fraction preparation only; no citywide building QA or source-datum equivalence established.

That warning accurately describes the **scope of the November 8 mosaic manifest**, not a permanent assertion that subsequent citywide QA was never performed. On November 15, the geometry correspondence and actual raster alignment were audited separately. **The manifest should not be rewritten to imply it performed those later checks.**

**Vertical reference:** The prior discussion cited provider-level documentation describing German DHHN2016 / NHN elevation reference for these source families. That is **supportive context**, not a tile-by-tile verification of these four exact delivered inputs or a numerical test of cross-source seam continuity. GeoTIFF `EPSG:25832` documents **horizontal CRS**, not the vertical datum. Therefore:

- **Provider-level datum consistency:** reported/supported by documentation cited in the previous discussion; not independently checked against every local input during this audit.
- **Exact tile-level datum equivalence and seam continuity:** **not independently verified**.
- **Observed material incompatibility:** **none identified in this audit** (which is not proof of absence).

The limitation is retained transparently. Since `T50` is a local-minus-neighbourhood elevation difference, constant vertical offsets cancel within a single source; source boundaries can still matter if sampling areas cross sources. Neither the synthetic experiment nor this review warrants claiming physical measurement perfection.

**Decision:** Hamburg inputs accepted **with explicit vertical-datum/boundary limitation** for M1-G2's synthetic experiment. No GIS correction or refit indicated by available evidence.

## 7. Final data/GIS assessment

| Check | Verdict | Precise scope |
|---|---|---|
| Three-city eligible geometry IDs | **PASS** | DON 7,755, RTM 220,456, HAM 341,530 matched; RTM exclusions traceable |
| DON extreme terrain | **PROVISIONAL PASS** | Positive and negative inspected extremes geographically plausible; exact T50 computation not re-extracted |
| RTM exclusion logic | **PASS — CLOSED** | Exact 20+20 valid-pixel rule independently reproduced; 0 mismatches |
| RTM water hypothesis | **NOT SUPPORTED** | Excluded buildings *less* likely to lie near mapped water under current distance proxy |
| HAM DEM and source-ID alignment | **PASS** | Both 5 m EPSG:25832 pairs match |
| HAM regional source traceability | **PASS** | Four source identifiers, 884 tile records, hashes/manifest |
| HAM tile-level datum and seam equality | **LIMITATION** | Not independently established; no material mismatch identified |
| Geographic input suitability for **synthetic** M1-G2 | **ACCEPT WITH LIMITATIONS** | No refit required by GIS findings |
| Empirical flood-risk/impact validity | **NOT TESTED** | No observed outcome calibration or flood-hazard validation |

**Closure action:** Preserve the original terrain tables, source manifests, review screenshots, output hashes and this decision record. Do not mutate any frozen M1-G2 outputs. Historical autogenerated reports with `GIS_REVIEW_REQUIRED` remain valid as **time-stamped intermediate states**, while this later manually reviewed document records the closed decision.

## 8. Provenance, source-of-truth locations and reproducibility

### Local project layout (Windows)

```text
C:\Users\C.Price\Habnetic\
  data\
    docs\phase4\M1_G2_DATA_GIS_AUDIT_CLOSURE_2026-11-15.md   <- this record
    processed\DON\derived\mdt05_don_5m_mosaic.tif
    processed\RTM\normalized\buildings.gpkg
    processed\HAM\derived\ham_dgm5_mainland_mosaic.tif
    processed\HAM\derived\ham_dgm5_western_islands_mosaic.tif
    processed\HAM\derived\ham_dgm5_mainland_mosaic_source_id.tif
    processed\HAM\derived\ham_dgm5_western_islands_mosaic_source_id.tif
    runs\rtm_m1_citywide\terrain_features_m1_5m.parquet
    runs\ham_m1_citywide\qa\ham_dgm5_citywide_manifest.json
    scripts\rtm\m1_extract_terrain_citywide.py
    scripts\rtm\m1_consolidate_terrain.py
    scripts\m1t\build_ham_dgm5_mosaics.py
    scripts\m1t\extract_ham_terrain_regions.py
  resilient-housing-bayes\
    docs\phase4\M1_G2_Full_City_Results_2026-11-14.md
    docs\phase4\M1_G2_Visual_Trace_Review_2026-11-15.md
    outputs\phase4\_m1g2_scientific_audit_v0.1\AUDIT_REPORT.md
    outputs\phase4\_m1g2_gis_audit_v0.1\GIS_AUDIT_REPORT.md
    outputs\phase4\_m1g2_gis_audit_v0.1\audit_gis_results.json
    outputs\phase4\_m1g2_gis_audit_v0.1\DON_T50_extremes_review.geojson
    outputs\phase4\_m1g2_gis_audit_v0.1\RTM_excluded_buildings_review.geojson
    outputs\phase4\{DON,RTM,HAM}\m1g_citywide_v0.1\...
```

**Scientific repository commit at automated audit:** `d1396ebf8e5d784260fd4ecc1f69316441fc2aa2` (reported in the scientific-audit report; not a claim of final archival tag).

**Known frozen config fingerprint:**

`configs/m1g_citywide_v0.1.json` SHA-256: `068b3a5d12b5e2bd410ce6a092cfba520901e2892bedbfa2c71e6b9eeff405c4`

**Study output structure:** 12 `idata.nc` posteriors, paired citywide decisions, 6 `citywide_comparison.parquet` and 6 comparison manifests under `outputs/phase4/{CITY}/m1g_citywide_v0.1/{gamma_0,gamma_neg0p8}/{B0,B1}`. Comparison parquets are **tables without geometry**: Operations Center maps must join canonical building geometry by `bldg_id` and label these as synthetic/model-dependent decisions.

**Existing ways to reproduce/check (no unnecessary rerun):**

- M1-G2 full-run engine: `RUN_M1G2_ALL.ps1` (resume-safe according to its archived README). Use only for intentional re-execution, not routine audit closure.
- Scientific audit: `RUN_M1G2_SCIENTIFIC_AUDIT.ps1` (read-only for frozen model artifacts; writes separate audit outputs).
- GIS audit: `RUN_M1G2_GIS_AUDIT.ps1` (read-only for original tables/geometries/DEM; writes separate GIS QA outputs).
- Source inputs: the exact `data/processed`, `data/runs` and `data/scripts` files listed above; original audit reports contain further hashes and analytical tables.

The present closure record **does not execute anything**. Reproducing the full analysis requires the frozen source files, code/config versions, compatible Python 3.11 environment and the original manifests. Large NetCDF/Parquet outputs need separate archival with checksums; a Git commit does not automatically archive ignored binary outputs.

## 9. Decision log and bounded remaining work

| Date | Decision | Reason |
|---|---|---|
| 2026-11-14 | Full-city synthetic M1-G2 completed | 569,741 eligible buildings; 12 NUTS fits; 6 comparisons |
| 2026-11-15 | Scientific automated audit and trace review passed with scoped limits | Reproducibility, diagnostics, posterior decisions checked |
| 2026-11-15 | DON geographical extreme review accepted provisionally | Two high-magnitude opposite-signed examples plausible in actual terrain |
| 2026-11-15 | RTM exclusion inquiry closed | All 868 explained by deterministic 20-pixel rule; zero mismatches |
| 2026-11-15 | HAM multi-source terrain review closed with limitation | Two aligned mosaics; 884 provenance tiles; exact vertical-datum equivalence unverified |
| 2026-11-15 | **GIS/data audit closed** | No identified GIS defect warranting correction or refit in synthetic scope |

**NOT a reason to reopen GIS closure:** The existence of an explicit residual vertical-datum limitation. For **future empirical/physical flood modelling**, a datum or seam check may be appropriate; that is a new scoped investigation, not an outstanding M1-G2 GIS acceptance condition.

**Separate, still-unfinished research/engineering items (not GIS audit gates):** compare M1-G1 and M1-G2 claims, decide any broader scientific-acceptance tag, archive exact large binary outputs/hash manifests, and design the Operations Center map layer joins. None of these requires rerunning the completed twelve fits merely because the GIS audit had a documented limitation.

## 10. Evidence record and epistemic limits

This closure is based on:

1. The existing `M1_G2_Full_City_Results_2026-11-14.md` results document (full design, six comparisons, posterior recovery and fingerprints).
2. `AUDIT_REPORT.md` and `M1_G2_Visual_Trace_Review_2026-11-15.md` (independent numerical checks and visual MCMC interpretation).
3. `audit_gis_results.json`, `GIS_AUDIT_REPORT.md`, GIS-review GeoJSON exports and user-reviewed QGIS screenshots (spatial correspondence/extremes/clusters).
4. **User-executed and reported read-only checks**, 2026-11-15: RTM water-distance percentages, terrain coverage and independent eligibility-rule reconstruction; HAM DEM/source-ID raster metadata and manifest inventory.
5. Original displayed code snippets from the `data` repository: RTM extraction/consolidation and HAM mosaic building/region extraction.
6. Prior *Operations Center Roadmap* conversation for experiment framing, chronology and existing source provenance. Earlier discussion should have been consulted before repeating already completed checks.

**Important:** This closure report was assembled from those preserved artifacts and reported console checks. The assistant did **not** directly access the user's Windows `C:\` drive or rerun the local QGIS/PyMC workflows while preparing this file. Only facts reproduced in the source reports or user-shared outputs are asserted as observed. No empirical validation, per-tile vertical-datum confirmation, independent physical T50 re-extraction or final Git tag is implied.

**Final status:** **M1-G2 DATA/GIS AUDIT CLOSED — ACCEPTED WITH DOCUMENTED LIMITATIONS (2026-11-15).**
