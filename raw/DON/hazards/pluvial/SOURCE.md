# DON Climate — ERA5-Land Total Precipitation

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
  [43.55, -2.15, 43.20, -1.85]

Format:
- NetCDF (`.nc`)

Notes:
- Used as the pluvial hazard input source for Donostia Phase 3.
- Same source family and aggregation logic as Rotterdam and Hamburg.
- Monthly files are downloaded to ERA5_Land/ and later checked, concatenated,
  and aggregated into the `H_pluvial_v1` hazard signal.