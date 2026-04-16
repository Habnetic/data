# HAM Buildings — Hamburg Building Footprints

Provider: Geofabrik GmbH
Dataset: Hamburg extract (OpenStreetMap-derived)
Layer used: gis_osm_buildings_a_free
Access: Geofabrik Germany regional downloads
License: ODbL 1.0
Retrieved: 2026-04-16

CRS:
- Source: OGC:CRS84
- Normalized: EPSG:25832

Notes:
- GeoPackage extract for Hamburg downloaded from Geofabrik.
- Building footprints are taken from the themed area layer
  `gis_osm_buildings_a_free`.
- Source schema observed:
  `osm_id`, `code`, `fclass`, `name`, `type`, `geometry`.
- Used as raw building footprint input for Hamburg Phase 3.
- OSM-derived source chosen for practical consistency with the Rotterdam MVP workflow,
  not as cadastral ground truth.