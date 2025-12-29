# Flood Hazard Zones — Donostia–San Sebastián (DSS)

## Source
Eusko Jaurlaritza / Gobierno Vasco  
geoEuskadi — Infraestructura de Datos Espaciales de Euskadi  
https://www.geo.euskadi.eus/

## Dataset
Plan Territorial Sectorial de Ordenación de Márgenes de los Ríos y Arroyos  
Urban planning flood hazard extent (COMP_URBANIST)

## Files used
- U11_PTS_RIOS_COMP_URBANIST_25000_ETRS89.shp
- U11_PTS_RIOS_COMP_URBANIST_25000_ETRS89.dbf
- U11_PTS_RIOS_COMP_URBANIST_25000_ETRS89.shx
- U11_PTS_RIOS_COMP_URBANIST_25000_ETRS89.prj

Other components of the dataset (hydraulic profiles, environmental layers)
were intentionally excluded for Phase II.

## Spatial reference
ETRS89 / UTM Zone 30N (EPSG:25830)

## Purpose in Habnetic
Used as flood hazard *support* for Phase II thin-slice modeling.
Represents fluvial and pluvial flood-prone areas relevant to urban planning.
Does not explicitly model coastal storm surge.

## Modeling assumptions
- Flood zones are treated as spatial extent indicators, not event reconstructions.
- Exposure is binary or ordinal (inside / outside hazard zone).
- Flood depth and velocity are not modeled at this stage.

## License
Creative Commons Attribution (CC BY)  
Attribution required: Eusko Jaurlaritza / Gobierno Vasco — geoEuskadi

## Retrieval
- Date: 2026-12-29
- Access method: Manual download via geoEuskadi data catalog

## Notes
This dataset was selected to introduce real-world spatial constraints
and uncertainty into the modeling pipeline. Coastal flood layers may be
added in later phases for sensitivity analysis.
