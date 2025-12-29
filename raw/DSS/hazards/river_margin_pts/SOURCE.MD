# Regulatory River Margins — Donostia–San Sebastián (DSS)

## Source
Eusko Jaurlaritza / Gobierno Vasco  
geoEuskadi — Infraestructura de Datos Espaciales de Euskadi  
https://www.geo.euskadi.eus/

## Dataset
**Plan Territorial Sectorial de Ordenación de Márgenes de los Ríos y Arroyos**  
Regional urban-planning regulation defining protected river margin zones  
(dataset component: `COMP_URBANIST`)

## Files used
- `U11_PTS_RIOS_COMP_URBANIST_25000_ETRS89.shp`
- `U11_PTS_RIOS_COMP_URBANIST_25000_ETRS89.dbf`
- `U11_PTS_RIOS_COMP_URBANIST_25000_ETRS89.shx`
- `U11_PTS_RIOS_COMP_URBANIST_25000_ETRS89.prj`

Other components of the PTS dataset (e.g. hydraulic profiles, environmental
reference layers) were intentionally excluded for Phase II.

## Spatial reference
ETRS89 / UTM Zone 30N (EPSG:25830)

## Role in Habnetic
This dataset is used as a **regulatory exposure proxy**, not as a hydraulic
flood inundation model.

It represents officially designated river margin protection zones that are
considered flood-prone or environmentally constrained within regional
urban planning frameworks.

## Modeling assumptions
- River margin zones are treated as **prior indicators of flood exposure**, not
  as realizations of specific flood events.
- Building exposure is modeled probabilistically, informed by:
  - inclusion within regulatory river margins,
  - proximity to river networks,
  - topographic context (handled separately).
- Flood depth, velocity, and event return periods are **not** modeled at this
  stage.

## Limitations
- The dataset does not represent modeled flood extent for specific return
  periods (e.g. T100).
- Coastal storm surge and compound flooding are not included.
- Spatial precision reflects regulatory planning intent rather than hydraulic
  simulation.

## License
Creative Commons Attribution (CC BY)  
Attribution required: Eusko Jaurlaritza / Gobierno Vasco — geoEuskadi

## Retrieval
- Date: 2026-12-29
- Access method: Manual download via geoEuskadi data catalog

## Notes
For Donostia–San Sebastián, publicly downloadable vector datasets of hydraulic
flood inundation extent are not available. Regulatory river margin zones are
therefore used in Phase II as a conservative, officially defined spatial proxy
to introduce real-world constraints and uncertainty into the modeling pipeline.

Hydraulic flood extent layers (fluvial and coastal) may be integrated in later
phases if suitable vector data becomes accessible.
