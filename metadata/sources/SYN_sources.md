# Synthetic / Lunar Analog (SYN) — Data Sources

**Focus:** procedural terrain, radiation & thermal analogs.

| Domain | Source | Dataset / Method | Format | License | Notes |
|:--|:--|:--|:--|:--|:--|
| Terrain | NASA PDS / LROC DEM | Lunar surface DEM tiles | GeoTIFF | Public | Use as seed terrain |
| Radiation | ESA Space Environment | Solar particle flux | CSV | Public | For synthetic hazard fields |
| Synthetic generation | Custom noise fields | Perlin / fractal noise | npy | MIT | Simulated hazard maps |
