# Habnetic | M1-T Hamburg — representative spatial quality assessment

**Review date:** 2026-11-08<br>
**Dataset:** Hamburg (`HAM`), Phase 4 / M1-T, 5 m DGM-derived local terrain indicators<br>
**Status:** **Numeric QA passed; targeted spatial QA completed for six cases; remaining candidates not individually inspected.**<br>
**Scope:** Relative topographic indicator plausibility only. **Not** a validation of flood hazard, flood depth, damage, vulnerability or Bayesian decision stability.

## 1. Population and verified computational QA

- **Phase 3 population:** 341,530 building identifiers, exactly matched to `processed/HAM/derived/buildings_ham.gpkg` by the citywide numerical auditor.
- **Extracted and measured:** 341,530 / 341,530; no missing T50 or T25; 341,461 routed to mainland and 69 to western islands.
- **T50:** `median(local ring elevation) − median(neighbourhood ring elevation)`; local ring is footprint to 20 m; neighbourhood ring is 20–100 m.
- **T25:** `median(local ring elevation) − 25th percentile(neighbourhood ring elevation)`.
- **Resolution:** common 5 m terrain mosaics (1 m-to-5 m aggregation from HH/SH/NI/WSV providers); preprocessing explicitly excludes unmasked `−9999` values. No missing terrain elevations were imputed.
- **Source mosaics:** `processed/HAM/derived/ham_dgm5_mainland_mosaic.tif` and `ham_dgm5_western_islands_mosaic.tif`. Accompanying per-pixel provider-ID and original valid-source-fraction grids were retained.
- **Extraction eligibility:** at least 20 valid pixels in each ring; portability screen requires at least 99% *geometric extent coverage* per ring. The core extractor did **not** require 99% *valid-pixel coverage*. Valid-pixel coverage was independently audited afterward.
- **Minimum actual valid-pixel fraction:** local 1.0000; neighbourhood approximately **0.993377**. **Zero** buildings below 0.99 in either ring. All checked feature formulas and 342 batch output hashes passed QA.
- **Outlier inventory:** 398 buildings flagged for review by numerical thresholds and/or prioritization order, **not 398 demonstrated errors**. Candidate inventory: `runs/ham_m1_citywide/qa/ham_m1t_spatial_review.csv` and `.gpkg`.

### Important distinction

An unchanged numeric result and plausible terrain morphology do not establish vertical accuracy of source data or real-world risk. The manual review is a **purposeful six-case sample**, not an exhaustive validation of the 398 candidates or 341,530 assets.

## 2. Review protocol

The researcher visually examined QGIS building polygons against the final mainland DGM5 mosaic, with OpenStreetMap as geographical context and the Identify tool for selected raster cells. For two difficult cases, code reproduced the original extraction-ring pixel selection and emitted dedicated GeoPackage layers:

- `runs/ham_m1_citywide/qa/ham_targeted_diagnostics/ham_8629_low_quartile_pixel_centres.gpkg` and `ham_qa_neighbourhood_rings.gpkg`.
- `runs/ham_m1_citywide/qa/ham_targeted_diagnostics/ham_304428_invalid_5m_cells.gpkg` and `ham_qa_footprints.gpkg`.

The diagnostic script uses the same `raster_geometry_mask` pixel-centre selection as the shared extractor. Screenshots have been preserved in [`evidence/`](evidence/) (image names below). The user provided the visual interpretation and screenshots interactively; photographs or field measurements were **not** used.

## 3. Six case assessments

### `8937`: high positive local terrain position

**Extracted:** T50 **+19.6924 m**, T25 **+26.7582 m**; local and neighbourhood valid-pixel fractions both 1.0.<br>
**Context:** A prominent hillside building in Blankenese, near Süllberg. The site is surrounded by pronounced slopes descending towards the Elbe. The building footprint joins a larger adjacent polygon and has an unusual plan form; this affects how the exclusion and local rings are constructed.<br>
**Visual finding:** Surrounding DGM appears smoothly graded, with no obvious abrupt source discontinuity in the screenshot. This is compatible with a high local-to-neighbourhood median difference.<br>
**Decision:** `PLAUSIBLE_RETAIN` (representative spatial plausibility only). Exact ring elevation samples were not independently remeasured against original 1 m data.<br>
**Evidence:** [Blankenese context](evidence/HAM_8937_OSM.png).

### `7616`: negative median, positive lower-quartile difference

**Extracted:** T50 **−12.9748 m**, T25 **+11.0197 m**; local and neighbourhood valid-pixel fractions both 1.0.<br>
**Context:** Blankenese hillside near Bismarckstein. Selected raster samples included approximately 22.40 m downslope and 40.10–40.15 m upslope.<br>
**Visual finding:** Strong continuous hillside gradient, compatible with very different neighbourhood median and lower quartile. The four spot readings do not by themselves reproduce either ring statistic.<br>
**Decision:** `PLAUSIBLE_RETAIN`.<br>
**Evidence:** [terrain readings](evidence/HAM_7616_elevation.png), [map context](evidence/HAM_7616_OSM.png).

### `8629`: very low neighbourhood first quartile

**Extracted:** local z50 **35.4048 m**; neighbourhood z50 **36.2696 m**; neighbourhood z25 **8.6014 m**; T50 **−0.8648 m** and T25 **+26.8034 m**. Valid-pixel fractions both 1.0.<br>
**Diagnostic:** Pixel-centre classification explicitly isolated values at or below the extracted neighbourhood z25. In QGIS, these points form a **contiguous low-elevation sector on the southern part of the 20–100 m ring**, aligned with darker/sloping terrain. The low 8.60 m quantile was not inferred solely from the earlier 27–41 m manual clicks.<br>
**Decision:** `PLAUSIBLE_RETAIN_WITH_SOURCE_ACCURACY_CAVEAT`. The diagnostic resolves **where** the low quartile comes from and establishes spatial coherence. It does **not** verify absolute elevations against independent survey data.<br>
**Evidence:** [exact ring and lower quartile centres](evidence/HAM_8629_lower_quartile.png).

### `41204`: strong local depression relative to neighbourhood

**Extracted:** local z50 **33.9148 m**; neighbourhood z50 **42.9788 m**; neighbourhood z25 **42.4228 m**; T50 **−9.0640 m**; T25 **−8.5080 m**. Valid-pixel fractions both 1.0.<br>
**Context:** PETRA III research-facility district. QGIS spot readings around the local depression were approximately 33.6–33.8 m; another point was approximately 43.1 m.<br>
**Visual finding:** Concentrated low local elevations are consistent with the extracted negative differences. Cause of apparent depression (natural vs built earthworks) is **not established**.<br>
**Decision:** `PLAUSIBLE_RETAIN_CAUSE_UNVERIFIED`.<br>
**Evidence:** [33.6 m reading](evidence/HAM_41204_elevation.png), [facility context](evidence/HAM_41204_OSM.png).

### `304428`: lowest valid-pixel fraction in Hamburg

**Extracted:** T50 **−0.3254 m**, T25 **+0.2673 m**. Local valid-pixel fraction **1.0000**, neighbourhood **approximately 0.993377**; approximately 0.6623% of neighbourhood pixels missing.<br>
**Diagnostic:** Invalid 5 m cells were explicitly mapped against the 20–100 m neighbourhood ring. They are clustered near the **outer east/southeast margin**, consistent with a raster coverage edge rather than a scattered elevation artifact. The exact footprint used in the extraction appears coherently placed in the ring and corresponds to the QA GeoPackage geometry, but no independent source survey of the polygon was performed.<br>
**Decision:** `COVERAGE_ACCEPTABLE_RETAIN` under the observed coverage threshold. No interpolation.<br>
**Evidence:** [missing-pixel squares along ring edge](evidence/HAM_304428_invalid_pixels.png).

### `6904`: second high positive hillside case

**Extracted:** T50 **+18.2558 m**, T25 **+26.7139 m**; local and neighbourhood valid-pixel fractions both 1.0.<br>
**Context:** Elevated terrain around Blankenese / Schinckels Park. QGIS samples were approximately 77.45 m, 83.97 m and 77.94 m.<br>
**Visual finding:** Marked hillside relief visible in the DGM and streets/park context; compatible with the indicator signs and magnitude. Sampled points alone do not rederive ring medians.<br>
**Decision:** `PLAUSIBLE_RETAIN`.<br>
**Evidence:** [sample elevation](evidence/HAM_6904_elevation.png), [OSM context](evidence/HAM_6904_OSM.png).

Full case register: [`HAM_M1T_reviewed_cases.csv`](HAM_M1T_reviewed_cases.csv).

## 4. Known limits and scientific decisions

1. **Manual inspection limited to six buildings.** The other 392 numerical candidates remain unreviewed individually. Retain the full 398-candidate list and its `qa_status=PENDING_MANUAL_REVIEW` field in the machine-generated inventory; the separate six-row register records reviewed cases and does not silently mark the other 392 as accepted.
2. **Mixed data provenance:** HH LGV nominal 2022, SH LVermGeo 2021, NI LGLN 2025, WSV Scharhörn 2022. Source licences and raw checksums are in `docs/provenance/HAM_Terrain_Source_Provenance.md` and `runs/ham_m1_citywide/ham_terrain_source_manifest.json`. These are not a homogeneous, same-epoch survey.
3. **Datum checks:** Valid cross-source seams had small typical adjusted differences, but did not establish absolute vertical datum equivalence. At one HH/SH overlapping 1 km tile, the maximum absolute difference where both providers were valid was **2.944 m**; its precise location and potential effect on feature estimates have **not** been separately audited. Source priority: retain valid HH, fill only missing HH cells with SH. The provider-ID layer preserves attribution.
4. **Elevation validity:** The discovered 107,349,120 stored `−9999` pixels in HH source rasters, despite different declared nodata metadata, were excluded in the 1 m → 5 m preparation. The QA of final ring coverage and features supports numerical correctness but does not prove the upstream elevation surface is free of every physical interpolation error.
5. **Sampling sensitivity:** 5 m cell-centre masks, 20/100 m rings, footprint quality, slope and coastline/building-adjacent geometry can affect percentiles. No independently surveyed terrain control points were used in this QA.
6. **Not a flood validation:** T50/T25 are relative terrain contrasts, not inundation probabilities or depths. Impact of adding these indicators to ranking stability remains a subsequent modelling experiment.

## 5. Decision and closure gate

**Representative spatial QA is completed and supports retaining the six inspected cases unchanged**, with explicitly limited evidentiary scope. The citywide M1-T numerical extraction is complete (341,530/341,530). This supports **closing Hamburg M1-T as a documented derived-feature dataset**, not declaring all 398 flagged cases independently verified or claiming risk-model improvement.

Before archiving, run `scripts/m1t/finalize_ham_m1t.py --check` to verify the source local numeric QA, targeted diagnostic, candidate inventory and extraction manifest. Preserve the original machine QA JSON with its original `NUMERICAL_PASS_SPATIAL_REVIEW_PENDING` status as historical evidence; the separate closure manifest describes the later representative review. Archive the resulting source/QA material and generated feature outputs, noting that the large original raw terrain sources are preserved separately.

**What to test next:** Compare feature sensitivity to 1 m vs 5 m terrain processing in steep regions and to a local geographic buffer adjustment; evaluate whether the HH/SH overlap outlier affects any extracted rankings; test topographic inputs in the Bayesian model without assuming they improve predictive or decision quality.

## Image and basemap attribution

The evidentiary images are researcher-supplied QGIS screenshots. Where the OpenStreetMap basemap is visible, credit **© OpenStreetMap contributors** under the applicable ODbL attribution requirements. DGM source-provider attributions, including any CC BY obligations for reuse, are listed in the Hamburg terrain provenance document. Screenshots remain qualitative evidence and do not replace original terrain files.
