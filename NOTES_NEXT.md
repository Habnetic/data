# Next steps — RTM pipeline

## Current state (2026-02-02)

### Spatial backbone (complete)

- **Normalized hydrography** created  
  PDOK / Kadaster TOP50NL `waterdeel_lijn`  
  `processed/RTM/normalized/hydrography.gpkg`

- **Normalized Rotterdam municipality boundary**  
  CBS gebiedsindelingen 2025  
  `processed/RTM/normalized/boundary_rtm.gpkg`

- **Derived hydrography clipped to RTM boundary**  
  `processed/RTM/derived/hydrography_rtm.gpkg`

- **CRS**: EPSG:28992 (meters)  
- **QGIS validation**: alignment and clipping verified

---

### Buildings (complete, stable IDs)

- **Normalized buildings** created from OSM (EPSG:28992)  
  `processed/RTM/normalized/buildings.gpkg`  
  (~1.9M features)

- **Deterministic internal building ID (`bldg_id`)**
  - Generated during normalization
  - Stable across reruns (centroid + area–sorted)
  - Canonical join key for all downstream tables

- **Buildings clipped to Rotterdam boundary**  
  `processed/RTM/derived/buildings_rtm.gpkg`  
  (221,324 buildings)

- **QGIS validation**: buildings fully contained in RTM boundary

---

### Exposure priors — water (v0 complete)

- **Computed exposure metrics** for all RTM buildings:
  - Distance to nearest water (`dist_to_water_m`)
  - Water length density within buffers:
    - `water_len_density_250m`
    - `water_len_density_500m`
    - `water_len_density_1000m`

- **Output table (canonical)**  
  `processed/RTM/priors/building_water_proximity.parquet`

- **Schema guarantees**
  - One row per building
  - Stable join key: `bldg_id`
  - Attribute-only table (no geometry)
  - Units:
    - meters for distance
    - 1/m for density

- **Sanity checks**
  - Row count: 221,324
  - No missing or duplicated `bldg_id`
  - Distance and density distributions validated
  - Correlations inspected (expected sign + magnitude)

---

### Deterministic latent exposure (v0 complete)

- **Notebook**
  - `resilient-housing-bayes/notebooks/03_model_definition.ipynb`

- **Definition**
  - Log-transform exposure variables
  - Z-score standardization
  - Deterministic aggregation:
    ```
    E_hat = mean(z_d, z_250, z_500, z_1000)
    ```

- **Exports**
  - `resilient-housing-bayes/outputs/rtm/water_exposure_Ehat_v0.parquet`
  - `resilient-housing-bayes/outputs/rtm/water_exposure_Ehat_v0_stats.json`

- **Properties**
  - One row per building
  - Keyed by `bldg_id`
  - No probabilistic interpretation
  - Suitable for ranking, clustering, and visualization only

---

### Scripts (pipeline complete)

- `scripts/rtm/normalize_hydrography.py`
- `scripts/rtm/normalize_boundary.py`
- `scripts/rtm/clip_hydrography_to_rtm.py`
- `scripts/rtm/normalize_buildings.py`  
  → generates stable `bldg_id`
- `scripts/rtm/clip_buildings_to_rtm.py`  
  → preserves `bldg_id`
- `scripts/rtm/compute_building_water_exposure.py`  
  → outputs priors keyed by `bldg_id`

All transformations are scripted and reproducible end-to-end.

---

## Next steps (actual, not aspirational)

### 1) QGIS verification (short, manual)

- Join `water_exposure_Ehat_v0.parquet` to:
  - `processed/RTM/derived/buildings_rtm.gpkg`
- Join key: `bldg_id`
- Style by graduated color on `E_hat`

Expectation:
- High `E_hat` near canals, rivers, harbor network
- Smooth spatial gradients, no checkerboarding

If this fails, fix **inputs or transforms**, not downstream models.

---

### 2) Documentation lock-in

- Update canonical definition:
  - `Habnetic/docs/references/exposure/rtm_water_exposure_v0.md`
- Must include:
  - input features
  - transforms
  - `E_hat` formula
  - interpretation constraints
  - exact export paths

This freezes RTM exposure v0.

---

### 3) Exposure observatory (v0)

- Artifact-driven, read-only
- Inputs:
  - `water_exposure_Ehat_v0.parquet`
  - stats JSON
  - one or two static figures
- Output:
  - static HTML report per run
  - stored under `runs/<run_id>/`

No interactivity. No inference. No sliders. No promises.

---

## Notes / constraints

- Exposure ≠ hazard
- No flood probability, depth, or damage modeled
- No Bayesian inference without an outcome
- RTM is **Phase 0 baseline**, not a result

The RTM pipeline is now:
- spatially complete
- numerically stable
- reproducible
- ready to accept hazards or scale to other cities

No further spatial preprocessing is required for Rotterdam.
