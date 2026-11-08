# Habnetic | M1-T Donostia — Spatial terrain QA

**Review date:** 2026-11-08  
**Status:** In progress. Numeric QA complete; spatial outlier review not yet complete.  
**Scope:** Topographic-feature plausibility, not flood-risk or decision-model validation.

## Dataset and validation context

- **Study population:** 7,755 Donostia buildings; Phase 3 `bldg_id` identities matched exactly.
- **Terrain source:** CNIG/IGN MDT05 first coverage, MTN50 sheets 0064 and 0040 (source year 2012; 5 m; ETRS89 / UTM 30N, EPSG:25830).
- **Mosaic:** `processed/DON/derived/mdt05_don_5m_mosaic.tif`.
- **Mosaic SHA-256:** `36f3def4e107da827ba49ffed76b8a06f751c16666f18e0031271c3fb827a569`.
- **Consolidated features:** `runs/don_m1_citywide/terrain_features_m1_5m.parquet`.
- **Consolidation result:** PASS; 7,755/7,755 measured, no missing features, unique identifiers, and minimum recorded ring geometric coverage approximately 100%.
- **Extraction regression:** first 100 Rotterdam building measurements matched frozen M1 calculations for the tested terrain statistics and coverage metrics.
- **Outlier inspection layer:** `runs/don_m1_citywide/qa/DON_T50_extremes.gpkg` (five highest and five lowest T50 values).

## Case DON / building `200663` — coastal lighthouse

**Observation (user-assisted visual inspection):** The building marked in QGIS was identified by the researcher as a lighthouse at La Plata / La Platako itsasargia, near the entrance to Pasaia harbour. The screenshots show an elevated coastal setting; exact physical terrain consistency has **not** been independently established by a ring-level elevation audit.

| Measure | Result |
|---|---:|
| `T50` | +36.195 m |
| `T25` | +53.7265 m |
| Local geometric coverage | ~100% |
| Neighbourhood geometric coverage | ~100% |
| Mosaic local ring valid pixels | 94 / 94 |
| Mosaic neighbourhood ring valid pixels | 1,378 / 1,378 |

**Interpretation:** The pronounced positive relative-elevation values are geographically *plausible* given steep coastal relief. The images do **not** prove the precise 20 m / 100 m elevation differences. In particular, a 100%-valid DTM pixel count does not establish whether values near the shoreline represent reliable bare-earth measurements: MDT05 may interpolate poorly constrained areas over water. The potential effect on the neighbourhood elevation quantiles remains untested.

**Decision:** Retain the measured values unchanged in the current consolidated data. Mark `200663` as **COASTAL_SENSITIVITY_PENDING**, rather than labelling it an extraction failure or claiming complete physical validation. Do not interpret this observation as flood vulnerability.

**Follow-up:**

1. Overlay the 20 m local and 20–100 m neighbourhood rings on the DTM and a coastline / land mask; measure potential intersection with water areas.
2. Review raw DTM elevation distributions in the rings; if warranted, recompute land-only T50/T25 as a **sensitivity analysis**, preserving the original results.
3. Visually inspect at least `193156` (highest T50, +43.2695 m) and `198335` (lowest T50, −23.4590 m) before closing the spatial outlier review.
4. Record screenshots and QGIS project CRS (EPSG:25830) in the research evidence archive, if retained. Screenshots are not bundled into this note.

## Attribution and evidence status

- For derived outputs: **Obra derivada de MDT05-cob1 2008-2015 CC-BY 4.0 scne.es**.
- The CNIG acquisition provenance and tile hashes are tracked separately under `docs/provenance/` and `runs/don_m1_citywide/`.
- **Validated:** data integrity, full geometrical/raster measurement coverage, source mosaic seam agreement, extracted-feature numerical definitions for the tested Rotterdam regression sample.
- **Not yet validated:** land/water influence on coastal T50/T25 values; full manual spatial inspection of ten extreme buildings; any empirical flood-risk relationship.

**Next decision gate:** Close Donostia spatial QA only after reviewing remaining outliers and recording the coastal sensitivity disposition (completed analysis or explicitly deferred limitation).
