# Next steps — RTM pipeline

## Current state (2026-01-31)

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

- **Schema guarantees**:
  - One row per building
  - Stable join key: `bldg_id`
  - No geometry (attribute table only)
  - Units: meters (distance), 1/m (density)

- **Sanity checks**:
  - Row count: 221,324
  - No missing `bldg_id`
  - Distance and density distributions validated

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

### 1) Deterministic latent exposure index (Ê) — **now**

Location:  
`resilient-housing-bayes/notebooks/03_model_definition.ipynb`

- Consume `building_water_proximity.parquet`
- Transform exposure variables (log + standardization)
- Define **deterministic latent exposure index**:
  - `E_hat = mean(z_d, z_250, z_500, z_1000)`
- Export:
  - `bldg_id`
  - `E_hat`
  - standardized components

This produces the **v0 exposure surface** used everywhere else.

---

### 2) Optional Bayesian wrapper (exploratory)

- Treat `E_hat` as:
  - latent mean, or
  - prior center
- Bayesian inference is **exploratory only**
- No claims, no calibration, no policy interpretation

---

### 3) Visualization & communication

- QGIS join on `bldg_id`
- Produce:
  - exposure gradient map
  - histogram of `E_hat`
- One reproducible figure or table

---

## Notes / constraints

- Exposure ≠ hazard
- No flood probability, depth, or damage modeled yet
- All assumptions documented upstream in `Habnetic/docs`
- RTM pipeline is **Phase 0 baseline**

The system is now ready to:
- scale to other cities
- accept additional exposure dimensions
- serve as input to hazard–impact models

No further spatial preprocessing is required for RTM.
