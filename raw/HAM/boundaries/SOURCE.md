# HAM Boundary — Hamburg Municipality

Provider: Freie und Hansestadt Hamburg — Landesbetrieb Geoinformation und Vermessung (LGV)  
Dataset: ALKIS Verwaltungsgrenzen Hamburg  
Layer used: APP_LANDESGRENZE (observed as single feature in GML)  
Access: Hamburg Transparenzportal  
URL: https://suche.transparenz.hamburg.de/dataset/alkis-verwaltungsgrenzen-hamburg28  
License: Datenlizenz Deutschland – Namensnennung – Version 2.0  
Retrieved: 2026-04-16  

CRS:
- Source: not explicitly detected in GML (assigned during normalization)
- Normalized: EPSG:25832 (ETRS89 / UTM Zone 32N)

Notes:
- Dataset contains administrative boundaries from ALKIS, including:
  Landesgrenze, Bezirke, Stadtteile, Ortsteile, Gemarkungen.
- Downloaded GML resolved to a single feature representing the Hamburg
  city boundary (Landesgrenze).
- Used as authoritative spatial clip for Hamburg datasets in Phase 3.
- Administrative boundary (not morphological urban extent).
- CRS had to be assigned during normalization due to missing metadata in the raw read.