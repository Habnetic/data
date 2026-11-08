# Habnetic | DON M1-T terrain data provenance

**Status:** Tiles acquired; pixel-level QA pending
**Last checked (UTC):** 2026-11-08T14:08:06+00:00
**Dataset:** PNOA MDT05, first LiDAR coverage, native 5 m DTM (NOT MDS).
**Provider:** Instituto Geográfico Nacional / Centro Nacional de Información Geográfica (Spain).
**Catalogue:** https://centrodedescargas.cnig.es/CentroDescargas/modelo-digital-terreno-mdt05-primera-cobertura
**Reference:** EPSG:25830, ETRS89 / UTM 30N, orthometric heights.
**Phase 3 DON study population:** 7,755 buildings (`processed/DON/derived/buildings_don.gpkg`).
**Required extent, EPSG:25830, including 100 m ring:** `[574351.982459101, 4785931.96049428, 589589.417160402, 4798637.86387985]`.
**Raw files:** `raw/DON/terrain/cnig_mdt05/`.
**Machine-readable log:** `runs/don_m1_citywide/mdt05_source_manifest.json`.
**Append-only acquisition events:** `runs/don_m1_citywide/mdt05_acquisitions.jsonl`.

## Tiles received

| Original filename | Source year (catalogue) | Bytes | SHA-256 | Imported UTC |
| --- | --- | ---: | --- | --- |
| `PNOA_MDT05_ETRS89_HU30_0040_LID.tif` | not verified | 3005080 | `532bc0c0666b4a60cc898ea7b663c90d5daefd526746537e0fa010ca527cd4c5` | 2026-11-08T14:08:06+00:00 |
| `PNOA_MDT05_ETRS89_HU30_0064_LID.tif` | 2012 | 78086945 | `2e9a9c29a626ac61c1e772c81e2886a0b2989dc4592172ac1f226d6843abaf38` | 2026-11-08T13:44:23+00:00 |

**Combined rectangular extent coverage:** 100.000%.
**Complete AOI within source extents:** True.
**IMPORTANT:** This is only an extent test. Pixel NoData coverage, water interpolation quality,
ring coverage and all building-level terrain quality checks are **not yet validated**.
Do not begin citywide extraction solely because this flag says True.

## Attribution and reuse

Source dataset (unmodified): **MDT05-cob1 2008-2015 CC-BY 4.0 scne.es**.
For mosaics, derived raster clips, terrain features, figures, and other derived outputs, credit:
**Obra derivada de MDT05-cob1 2008-2015 CC-BY 4.0 scne.es**.

The CNIG/IGN licence is compatible with CC-BY 4.0, requiring source acknowledgement
for originals and derivative products. Preserve this credit in published figures,
web maps, derived datasets, and Operations Center source metadata.
See the current catalogue licence for the official wording.

## Scientific cautions

- Source LiDAR acquisition: first coverage (2008–2015); individual sheet vintages are listed above when verified.
- CNIG states water-surface voids can be interpolated and have low reliability. Do not treat all finite pixels as observed elevations of equal quality.
- Compare source quality, NoData and acquisition vintages against RTM AHN5; common 5 m resolution alone does not ensure equivalent data quality.
- The Phase 3 building IDs are fixed; no real flood-damage validation is implied.
- Recheck source tile extents using map search and inspect actual raster coverage before accepting the set.
