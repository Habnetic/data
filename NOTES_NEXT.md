# Next steps — RTM pipeline

## Current state (2026-01-22)

### Spatial backbone
- Normalized hydrography created (PDOK/Kadaster TOP50NL `waterdeel_lijn`):  
  `processed/RTM/normalized/hydrography.gpkg`
- Normalized Rotterdam municipality boundary created (CBS gebiedsindelingen 2025):  
  `processed/RTM/normalized/boundary_rtm.gpkg`
- Derived hydrography clipped to RTM boundary:  
  `processed/RTM/derived/hydrography_rtm.gpkg`
- QGIS validation completed (alignment + clipping correct)

### Buildings (derived)
- Normalized buildings created (OSM, filtered schema, EPSG:28992):  
  `processed/RTM/normalized/buildings.gpkg` (~1.9M features)
- Buildings clipped to Rotterdam municipality boundary:  
  `processed/RTM/derived/buildings_rtm.gpkg` (221,324 features)
- QGIS validation completed (buildings fully contained within RTM boundary)

### Scripts
- `scripts/rtm/normalize_hydrography.py`
- `scripts/rtm/normalize_boundary.py`
- `scripts/rtm/clip_hydrography_to_rtm.py`
- `scripts/rtm/normalize_buildings.py`
- `scripts/rtm/clip_buildings_to_rtm.py`

---

## Next steps

### 1) Compute exposure priors (water)
- Compute distance to nearest water for each building  
  (source: `processed/RTM/derived/buildings_rtm.gpkg`  
  and `processed/RTM/derived/hydrography_rtm.gpkg`)
- Compute water length density within buffers (250 m / 500 m)
- Output table:  
  `processed/RTM/priors/building_water_proximity.parquet`

### 2) Validate exposure metrics
- Visual sanity check in QGIS (distance gradients)
- Basic descriptive statistics (min / median / max distances)
- Confirm units and expected ranges

---

## Notes
- Spatial data backbone for RTM is complete.
- All transformations are scripted and reproducible.
- Ready to move from spatial preprocessing to quantitative exposure modeling.
