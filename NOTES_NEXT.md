# Next steps — RTM pipeline

## Current state (2026-01-18)

### Spatial backbone
- Normalized hydrography created (PDOK/Kadaster TOP50NL `waterdeel_lijn`):  
  `processed/RTM/normalized/hydrography.gpkg`
- Normalized Rotterdam municipality boundary created (CBS gebiedsindelingen 2025):  
  `processed/RTM/normalized/boundary_rtm.gpkg`
- Derived hydrography clipped to RTM boundary:  
  `processed/RTM/derived/hydrography_rtm.gpkg`
- QGIS validation completed (alignment + clipping correct)

### Buildings (source ready)
- OSM buildings source downloaded (Geofabrik Zuid-Holland extract, dated 2026-01-17):  
  `raw/RTM/buildings/osm/downloads/zuid-holland-260117.osm.pbf`
- Source documented:  
  `raw/RTM/buildings/osm/SOURCE.md`

### Scripts
- `scripts/rtm/normalize_hydrography.py`
- `scripts/rtm/normalize_boundary.py`
- `scripts/rtm/clip_hydrography_to_rtm.py`

---

## Resume plan

### 1) Extract and normalize RTM buildings (OSM)
- Extract building polygons from OSM PBF
- Normalize CRS to EPSG:28992 →  
  `processed/RTM/normalized/buildings.gpkg`
- Clip to RTM boundary →  
  `processed/RTM/derived/buildings_rtm.gpkg`

### 2) Compute exposure priors (water)
- Distance to nearest water (from `hydrography_rtm`)
- Water length density within buffers (250 m / 500 m)
- Output table →  
  `processed/RTM/priors/building_water_proximity.parquet`
