# DON Hydrography — Gipuzkoa Rivers and Streams

Provider: Gipuzkoa Provincial Council
Dataset: Rivers and Streams (Hydrography)
Access: B5M Gipuzkoa geographic datasets
License: official open geographic data service
Retrieved: 2026-04-16

Format used:
- GPKG

CRS:
- Source: to be confirmed from downloaded file
- Normalized: EPSG:25830

Notes:
- Official hydrographic network of Gipuzkoa, including rivers and streams.
- Used as the raw hydrography source for Donostia Phase 3.
- Hydrography is later clipped to the normalized Donostia municipal boundary.
- Selected to keep the Phase 3 water proximity logic aligned with RTM/HAM:
  - dist_to_water_m
  - water_len_density_250m
  - water_len_density_500m
  - water_len_density_1000m