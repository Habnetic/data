# Donostia | M1-T MDT05 mosaic provenance

- **Status:** AOI-clipped mosaic built; full citywide per-building pixel QA pending.
- **Generated (UTC):** 2026-11-08T14:25:00.884616+00:00
- **Provider:** Instituto Geografico Nacional / Centro Nacional de Informacion Geografica (IGN/CNIG).
- **Dataset:** MDT05 first coverage, 5 m, ETRS89 UTM zone 30N (EPSG:25830).
- **Source catalogue:** https://centrodedescargas.cnig.es/CentroDescargas/modelo-digital-terreno-mdt05-primera-cobertura
- **Source sheets, merge priority:** 0064 then 0040.
- **Year listed in catalogue:** 2012 for both sheets (source-vintage metadata; not acquisition date).
- **Licence / attribution for derived product:** Obra derivada de MDT05-cob1 2008-2015 CC-BY 4.0 scne.es
- **Operations:** Extracted 5 m cells over the buffered Phase 3 study rectangle; preserved source values and NoData (-32767); no resampling or gap filling. First valid pixel takes priority in overlaps.
- **Mosaic:** `processed/DON/derived/mdt05_don_5m_mosaic.tif`
- **Mosaic SHA-256:** `36f3def4e107da827ba49ffed76b8a06f751c16666f18e0031271c3fb827a569`
- **Source 0064 SHA-256:** `2e9a9c29a626ac61c1e772c81e2886a0b2989dc4592172ac1f226d6843abaf38`
- **Source 0040 SHA-256:** `532bc0c0666b4a60cc898ea7b663c90d5daefd526746537e0fa010ca527cd4c5`
- **Overlapping valid-cell comparisons:** 370175
- **Median absolute overlap difference (m):** 0.0
- **Max absolute overlap difference (m):** 0.0
- **Three original edge buildings:** All six targeted terrain rings contain valid elevation pixels. This does **not** establish full citywide valid-pixel coverage or source accuracy over water.
- **Machine-readable report:** `runs/don_m1_citywide/mdt05_mosaic_manifest.json`
- **Acquisition log:** `runs/don_m1_citywide/mdt05_source_manifest.json` and `docs/provenance/DON_MDT05_Source.md`.

**Caution:** Topographic measurements remain descriptive features from an older lidar-derived DTM. Coastal interpolated surfaces and disagreements between tile vintages can limit reliability. The frozen Rotterdam scientific definitions are unchanged.
