# HAM Hydrography — Basis-Gewässernetz Hamburg

Provider: Freie und Hansestadt Hamburg — Behörde für Umwelt und Energie (BUE)
Dataset: Basis-Gewässernetz für Hamburg
Access: Hamburg Transparenzportal
License: Datenlizenz Deutschland – Namensnennung – Version 2.0
Retrieved: 2026-04-16

CRS:
- Source: EPSG:3044
- Normalized: EPSG:25832

Notes:
- Official Hamburg hydrographic network dataset provided via WFS download service.
- Downloaded as XML and read successfully as a line-based geospatial dataset.
- Observed source schema:
  - gml_id
  - name
  - gid
  - geometry
- Observed geometry type:
  - MultiLineString
- Used as hydrography input for Hamburg Phase 3 water proximity metrics.

Extreme dist_to_water_m values likely reflect peripheral Hamburg territory and the fact that the hydrography source is inland-network focused, not full coastal/sea-water representation.

Note:
After clipping hydrography to the Donostia boundary, non-line clip artifacts
(Point, MultiPoint, GeometryCollection) were observed. These are filtered out
before computing building water proximity metrics so that only line geometries
contribute to distance and buffer-length calculations.