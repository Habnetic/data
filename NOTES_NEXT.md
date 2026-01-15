# Next steps — RTM pipeline

Current state (2026-01-15)
- Normalized hydrography created (TOP50NL waterdeel_lijn): processed/RTM/normalized/hydrography.gpkg
- Normalized Rotterdam boundary created (CBS gebiedsindelingen 2025): processed/RTM/normalized/boundary_rtm.gpkg
- Derived hydrography clipped to RTM boundary: processed/RTM/derived/hydrography_rtm.gpkg
- Scripts: scripts/rtm/{normalize_hydrography,normalize_boundary,clip_hydrography_to_rtm}.py
- QGIS checks passed (alignment + clipping)

Resume plan
1) Add RTM buildings (OSM)
   - download → raw/RTM/buildings/osm/
   - normalize CRS to EPSG:28992 → processed/RTM/normalized/buildings.gpkg
   - clip to boundary → processed/RTM/derived/buildings_rtm.gpkg

2) Compute exposure priors
   - distance to nearest water (from hydrography_rtm)
   - water length density within buffers (250m/500m)
   - output table → processed/RTM/priors/building_water_proximity.parquet
