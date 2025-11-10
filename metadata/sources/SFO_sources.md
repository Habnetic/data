# San Francisco (SFO) — Data Sources

**Focus:** seismic, coastal surge, wildfire, and urban recovery.

| Domain | Source | Dataset | Format | License | Notes |
|:--|:--|:--|:--|:--|:--|
| Hazards | USGS ShakeMap / PAGER | Earthquake intensity & exposure | GeoJSON / CSV | Public Domain | For fragility priors |
| Hazards | NOAA / FEMA | Flood surge zones | Shapefile | Public | Coastal hazard extent |
| Climate | NASA EarthData (MERRA-2) | Climate reanalysis | NetCDF | Public | For stochastic forcing |
| Buildings | SF Open Data Portal | Building footprints & permits | GeoPackage | Public | Good structural typology |
| Socio | US Census TIGER/ACS | Population, income | GeoJSON / CSV | Public | Join to exposure model |
