# Habnetic | Rotterdam M1 AHN5 Source Provenance

**Scope:** Source provenance supplement for the frozen Rotterdam topographic experiment.  
**Generated (UTC):** 2026-11-08T15:34:48+00:00  
**Research baseline:** `phase4-m1-complete-v1.0` (Bayesian repository).  
**Status:** Historical records cross-checked; 28/28 original source files locally rehashed.  

## Dataset identity

- **Product:** Actueel Hoogtebestand Nederland (AHN5), 5 m Digital Terrain Model (DTM).
- **Data source:** AHN distribution at `basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/`.
- **Provider/attribution:** AHN / Dutch AHN programme, including its participating public authorities.
- **Source years recorded in inventory:** 2023, 2024 (not download dates).
- **Acquisition statuses in inventory:** downloaded: 27, reused: 1. Here, `reused` denotes an existing local tile used in the acquisition workflow; it is not evidence of a new download.
- **Horizontal CRS:** RD New, EPSG:28992.
- **Source compound CRS:** EPSG:7415 (RD New + NAP vertical EPSG:5709).
- **Raster resolution:** 5 m; 28 downloaded tiles for the buffered Rotterdam study area.
- **License:** **Creative Commons Attribution 4.0 International (CC BY 4.0)** for AHN5, not CC0. Official AHN index: https://basisdata.nl/hwh-ahn/AUX/bladwijzer/index.html . License: https://creativecommons.org/licenses/by/4.0/ .
- **Suggested acknowledgement:** "Contains AHN5 digital terrain elevation data, provided through the AHN programme, licensed under CC BY 4.0; terrain derivatives and analysis by Habnetic." Include the official dataset/source link when redistributing derivatives.

The AHN5 product documentation explains that the 5 m model is derived as an unweighted average from the underlying 0.5 m model. Source: https://basisdata.nl/hwh-ahn/AUX/bladwijzer/index.html .

## Acquisition and lineage

1. **Initial footprint selection:** `runs/rtm_m1_citywide/ahn5_5m_tile_manifest.csv` (27 tiles).
2. **Buffered study-area selection:** `runs/rtm_m1_citywide/ahn5_5m_tile_manifest_buffered.csv` (28 tiles).
3. **Recorded acquisitions:** `runs/rtm_m1_citywide/ahn5_5m_download_inventory.csv` (28 files, with source URLs, recorded SHA-256, year, CRS, nodata, bounds and status; downloaded: 27, reused: 1).
4. **Downloaded source files:** `raw/RTM/terrain/ahn/ahn5_dtm_5m/`.
5. **Mosaic integrity validation:** `runs/rtm_m1_citywide/ahn5_5m_mosaic_integrity.csv` (28 tiles; all marked passed and with identical masks).
6. **Processed mosaic:** `processed/RTM/derived/ahn5_dtm_5m_rtm_mosaic.tif`.
7. **Feature extractor:** `scripts/rtm/m1_extract_terrain_citywide.py` (frozen Rotterdam implementation).

**Mosaic SHA-256 (current local file):** `4ff604c8e8c57261dc05d93881259b4add501111c0bbd0eded4b89efa6e524c1`.

**Recorded source files with hashes and URLs:**

| Source tile | Tile year | Inventory status | Recorded SHA-256 | Local hash verification | Original URL |
| --- | --- | --- | --- | --- | --- |
| `2023_M5_36FN2.TIF` | 2023 | downloaded | `23b254e7af4de27ceb0d7e5c9325c720504167c810d9e4554e4d7314e4a3f763` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_36FN2.TIF) |
| `2023_M5_36FZ2.TIF` | 2023 | downloaded | `bcbb55a144df1aed532b6555b7da8f64769d6253cf66b3415d372dad1e90811f` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_36FZ2.TIF) |
| `2023_M5_36HN2.TIF` | 2023 | downloaded | `0265d0abbff13186b0f05fe558a4c497b2c99774917a53f89c11f1f11f75c709` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_36HN2.TIF) |
| `2023_M5_37AN1.TIF` | 2023 | downloaded | `cd9de9ec588746ad7abfc0b692d03b87329179dadd58880388d471dad2f65f5b` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_37AN1.TIF) |
| `2023_M5_37AN2.TIF` | 2023 | downloaded | `93f116a290d92c81d1de08216e518620ace5f7cb1de7ac9845fbdd6a9651ae8d` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_37AN2.TIF) |
| `2023_M5_37AZ1.TIF` | 2023 | downloaded | `10c2c711debcfbb533a5943ca6c2c6c5cc12333ed801ff430262b595b4a704c1` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_37AZ1.TIF) |
| `2023_M5_37AZ2.TIF` | 2023 | downloaded | `e6b7c49c32541c52e10b2347b6473ec7b1e3b2cee9b1646f2bc71491737f5090` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_37AZ2.TIF) |
| `2023_M5_37BN1.TIF` | 2023 | downloaded | `37d43d42e80714ba104032b873de542b322c556bc0d8e0580ce7db28a1297cd3` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_37BN1.TIF) |
| `2023_M5_37BZ1.TIF` | 2023 | downloaded | `10b18769ea952a76e738bcd0746979dbe896afb3f7a2d8f9e2454ab5fca0345e` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_37BZ1.TIF) |
| `2023_M5_37BZ2.TIF` | 2023 | downloaded | `d28051c365b987d4bbddb17a8b88eeb4c836473f4d28c9c8568f671dc16d5cfa` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_37BZ2.TIF) |
| `2023_M5_37CN1.TIF` | 2023 | downloaded | `4cec471de5d9c7b26c730854fd02336874ffdeca60cf888496cd1b3edba558a3` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_37CN1.TIF) |
| `2023_M5_37DN1.TIF` | 2023 | downloaded | `cbea111329e362358c37d747c7ebaa0a3372fa1698c393a574faa60426364ba9` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_37DN1.TIF) |
| `2023_M5_37DN2.TIF` | 2023 | downloaded | `e3290b52a5ebac0f0d9996cee68610225b3eba9512417fffa93a1ce22cc5ab7c` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_37DN2.TIF) |
| `2023_M5_37EZ2.TIF` | 2023 | downloaded | `eb970f3e9d6f7f92642665c0ad74f1e1619e45d7cf4f519bdff3955d4da4b542` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_37EZ2.TIF) |
| `2023_M5_37FN1.TIF` | 2023 | downloaded | `89c5222718e72f9f6544232b685227db1084786b8834dbdfc73676ae80e1401d` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_37FN1.TIF) |
| `2023_M5_37FN2.TIF` | 2023 | downloaded | `8490086223706cf6f33b783970f00d233ff48f23de963b09d290d1eb1af290a5` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_37FN2.TIF) |
| `2023_M5_37FZ1.TIF` | 2023 | downloaded | `acbfe0f126608c17f37075943c65eb24bc10f85248ea6bdeeb1fd6dd4bfe09fe` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_37FZ1.TIF) |
| `2023_M5_37FZ2.TIF` | 2023 | downloaded | `3948f70e003e755c0ef29da81d97242208b5e6e5d306e6e6cd9678cfbcb06c2c` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_37FZ2.TIF) |
| `2023_M5_37GN1.TIF` | 2023 | downloaded | `e88b63d8f3b9521e9e8ccddd5ee8d39bcc2146acbffca9436fa79e070f1da910` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_37GN1.TIF) |
| `2023_M5_37GN2.TIF` | 2023 | downloaded | `f04fa142f8b7b3823c23f8efe1d5ddccc3324c0287b28eeaad96266d1427e181` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_37GN2.TIF) |
| `2023_M5_37HN1.TIF` | 2023 | reused | `4a41f66243d950e8f3af86e7d4165d7316e6b987b6ac8d515cf234a653689110` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_37HN1.TIF) |
| `2023_M5_37HN2.TIF` | 2023 | downloaded | `0c87a759a1c838ef925aec2ab4714edab0321febe4856f8210858fe769229086` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_37HN2.TIF) |
| `2023_M5_38AN1.TIF` | 2023 | downloaded | `679ca5804264d86abedfcf0f14442afc529dadfee98f75c4c8490e1267e03dd8` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_38AN1.TIF) |
| `2023_M5_38AZ1.TIF` | 2023 | downloaded | `7ddabff4b8e6ff4c790ba96252d19fdce8f7c23248d1654f5147beb140fd3379` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2023_M5_38AZ1.TIF) |
| `2024_M5_37DZ2.TIF` | 2024 | downloaded | `5b23ff48de9d8adf57d8ccd32be3dc7e87437433d328bf9454669caf49187513` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2024_M5_37DZ2.TIF) |
| `2024_M5_37GZ1.TIF` | 2024 | downloaded | `7aec6dd7eceaf847d83cb528f704f5da60c3255eb14e6c0e1c6362fafd35f484` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2024_M5_37GZ1.TIF) |
| `2024_M5_37GZ2.TIF` | 2024 | downloaded | `567d8c0c9dfd795f74ca10eaafb213426b4f47752d7a04bf95f9b72686a05798` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2024_M5_37GZ2.TIF) |
| `2024_M5_37HZ1.TIF` | 2024 | downloaded | `2e40f3fb14d8f77781beeeb3982c07d0422d42c5f7cf604afaa807e8ac56dbb0` | Verified | [Source](https://basisdata.nl/hwh-ahn/AHN5/02b_DTM_5m/2024_M5_37HZ1.TIF) |

## Verification scope and limitations

- All 28 inventory rows match the 28 buffered-tile and 28 mosaic-integrity records.
- 28 original source files were rehashed and match their recorded SHA-256 values; 0 source files were not available locally for rehashing.
- Both `downloaded` and `reused` acquisition statuses are permitted. Neither status substitutes for a present-day file hash verification. An unavailable source is explicitly reported as unverified.
- Every recorded mosaic-integrity result is marked `passed=True`, with `masks_identical=True` and without a reported elevation difference greater than 1e-6 m.
- **Original acquisition timestamps are not present in the inspected inventory.** The timestamp above is the *report generation time*, not a claimed download time. Original file dates are not reliable substitutes.
- Tile years are source-vintage indicators and may differ from processing dates.
- This document is a supplemental provenance record. It does not amend frozen Rotterdam M1 results, and it does not certify inputs beyond this AHN5 terrain source.
- The CC BY 4.0 license pertains to AHN5 source data; license terms of derived software and other data sources must be tracked independently.

## Reproduction

From `Habnetic/data`, run using the existing geospatial Python interpreter:

```powershell
python scripts/m1t/generate_rtm_ahn5_provenance.py
```

Input: existing Rotterdam AHN5 acquisition records and, when present, original source raster files.  
Output: `docs/provenance/RTM_AHN5_Source.md`.  
The generator validates record alignment and SHA-256 checks, and refuses to overwrite the document if an audit check fails.
