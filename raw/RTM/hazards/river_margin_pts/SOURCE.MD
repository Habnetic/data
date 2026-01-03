# Regulatory Waterway Constraints — Rotterdam (RTM)

## Source
Municipality of Rotterdam / City of Rotterdam  
Open Data Rotterdam  
https://data.rotterdam.nl/

Additional context from:
- Rijkswaterstaat (Dutch national water authority)
- Waterschap Hollandse Delta / Schieland en de Krimpenerwaard

## Dataset
**Waterways and regulated water-adjacent zones**  
Municipal and regional planning layers defining canals, rivers, and
water-adjacent buffer or constraint zones within the Rotterdam metropolitan area.

These datasets reflect planning, safety, and maintenance constraints related to
flood risk, navigation, and water management rather than event-based flood modeling.

## Files used
*(example structure; filenames may vary by release)*

- `rotterdam_waterways.gpkg`
- `rotterdam_water_buffers.gpkg`
- `rotterdam_water_constraints.gpkg`

Raster or hydraulic simulation outputs were intentionally excluded at this stage.

## Spatial reference
Amersfoort / RD New (EPSG:28992)

## Role in Habnetic
This dataset is used as a **regulatory and infrastructural exposure proxy**, not
as a hydraulic flood inundation model.

It represents officially defined water-adjacent constraints that indicate
elevated flood sensitivity, maintenance requirements, or land-use restrictions
within the Dutch planning and water governance framework.

## Modeling assumptions
- Water-adjacent zones are treated as **prior indicators of flood exposure and
  regulatory constraint**, not as realizations of specific flood events.
- Building exposure is modeled probabilistically, informed by:
  - inclusion within regulated water buffer or constraint zones,
  - proximity to canals, rivers, and major waterways,
  - relative elevation and local topography (handled separately).
- Flood depth, velocity, and return periods are **not** modeled at this stage.

## Limitations
- The dataset does not represent modeled inundation extent for specific return
  periods (e.g. T10, T100).
- Coastal storm surge and compound flooding are not explicitly represented.
- Spatial precision reflects planning and governance intent rather than
  physics-based hydraulic simulation.

## License
Open data, typically under **Creative Commons Attribution (CC BY 4.0)**  
Exact licensing depends on the specific Rotterdam Open Data layer used.  
Attribution required to the Municipality of Rotterdam and relevant water authorities.

## Retrieval
- Date: 2026-01-03
- Access method: Manual download via Rotterdam Open Data portal

## Notes
For Rotterdam, fully open, city-scale vector datasets of hydraulic flood
inundation extent (fluvial and coastal) are not consistently available across
return periods.

Regulatory water-adjacent constraints are therefore used in Phase 0 as a
conservative, officially defined spatial proxy to introduce real-world flood
sensitivity and planning constraints into the modeling pipeline.

Physics-based hydraulic inundation layers may be integrated in later phases if
consistent, open vector datasets become accessible.
