# HAM Climate — ERA5-Land Total Precipitation

Provider: Copernicus Climate Data Store (CDS)
Dataset: ERA5-Land hourly data
Variable: total_precipitation (`tp`)
Access: CDS API
Retrieved: 2026-04-16

Temporal coverage:
- 1991-2020
- hourly

Spatial subset:
- Bounding box [North, West, South, East]:
  [53.75, 9.55, 53.35, 10.45]

Format:
- NetCDF (`.nc`)

Notes:
- Used as the pluvial hazard input source for Hamburg Phase 3.
- Same source family and aggregation logic as Rotterdam.
- Monthly NetCDF files are stored under ERA5_Land/ and later:
    - checked
    - concatenated
    - aggregated into the H_pluvial_v1 hazard signal.