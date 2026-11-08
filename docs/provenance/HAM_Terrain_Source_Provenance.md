# Habnetic | Hamburg M1-T terrain source provenance

**Record status:** Acquisition and native-resolution edge-ring coverage documented; cross-source elevation consistency remains **UNRESOLVED**.
**Record date:** 2026-11-08.
**Population:** 341,530 Phase 3 building IDs, EPSG:25832, no exclusions.
**Purpose:** Reconstruct the Hamburg M1-T terrain inputs without conflating different providers, vintages, measurement methods, formats, or height references.

## 1. Why four sources?

Hamburg's administrative area includes the mainland and North Sea islands. The LGV DGM1 2022 archive contains 880 one-kilometre GeoTIFFs but does not cover all 100-m building neighbourhoods. The Phase 3 building population contains 341,461 eastern/mainland buildings and 69 western/island buildings. A centroid/tile-presence screening found 341,529 of 341,530 centroids within LGV tile footprints. A stricter geometric screening of each building footprint and its 0–20 m and 20–100 m rings identified **27** cases below the provisional 99% tile-footprint threshold: 1 on Scharhörn, 23 by Schleswig-Holstein, and 3 by Niedersachsen. The initial expanded-bounding-box screening had 40 candidates; 13 passed the exact geometry test. These are coverage counts, not citywide raster-validity counts.

**Source precedence, provisional (not yet approved for final mosaic):** LGV primary wherever valid; WSV on Scharhörn; LVermGeo SH and LGLN NI only in their supplementary edge tiles. No gaps may be silently filled, and raster data from different height systems must not be assumed interchangeable.

## 2. Input ledger

### HH: Hamburg LGV DGM1 nominal 2022

- **Provider:** Freie und Hansestadt Hamburg, Landesbetrieb Geoinformation und Vermessung (LGV).
- **Catalogue:** https://suche.transparenz.hamburg.de/dataset/gelaendemodelle-hamburg-dgm
- **Actual archive URL used:** https://daten-hamburg.de/opendata/fernerkundung_hoehenmodelle/dgm/dgm1_hh_2022-04-30.zip
- **Local source:** `raw/HAM/terrain/lgv_dgm1/dgm1_hh_2022-04-30.zip`
- **Archive SHA-256:** `32b8d624af3000aa8257205b8701d6389b2a08d6c41a8b78850e6c6863be94f2`
- **Archive size:** 1,364,773,543 bytes. **Contents:** 880 `.tif` tiles and one `.csv`; ZIP CRC `testzip()` PASS.
- **Example tile structure:** `dgm1_32_555_5938_1_hh_2022.tif`, 1,000 × 1,000 cells, 1 m, EPSG:25832, float32; raster nodata metadata observed in inspected samples as approximately `-3.402823466e38`.
- **Vertical reference from official catalogue:** NHN / DE_DHHN2016_NH. **Licence:** Datenlizenz Deutschland Namensnennung 2.0. Attribution: `Freie und Hansestadt Hamburg, Landesbetrieb Geoinformation und Vermessung (LGV)`.
- **Temporal note:** `2022` is the nominal archive year, not proof of a single homogeneous acquisition campaign. Official product metadata describes ALS and photogrammetric updates from multiple periods and a non-ALS image-derived 2022 surface for Neuwerk.
- **Open QA:** Check actual raster values and masks, notably possible `-9999` values that may not match the declared raster nodata metadata; check whether these explain apparent seam discontinuities.

### WSV: Scharhörn DGM-W nominal 2022

- **Provider:** Wasserstraßen- und Schifffahrtsverwaltung des Bundes (WSV), distributed via Küstendaten.
- **Official regional index:** https://www.kuestendaten.de/Tideelbe/DE/Service/Kartenthemen
- **Official GeoTIFF subarea list:** https://www.kuestendaten.de/media/zdm/portaltideelbe/Allgemeine_Informationen/Archiv/GIS/DGM-W_Unterelbe_2022_1x1m/Teilgebiete.pdf
- **Local source:** `raw/HAM/terrain/wsv_dgmw_2022/DGM-W_2022_Unter-_und_Aussenelbe_1x1m_Scharhoern.tif`
- **Source SHA-256:** `b6582f0a656276b33ba4b76a8ae040f6491b85b3376a769cb917d67e32915538`
- **Observed raster:** EPSG:25832, 1 m, 15,000 × 10,000 cells; extent `(450000, 5978000, 465000, 5988000)`; nodata `-9999`.
- **Vertical reference:** DHHN2016 (official subarea sheet). **Usage conditions:** federal geodata usage terms / GeoNutzV as stated in official subarea listing; **not** silently assigned the Hamburg or SH licence.
- **Method/temporal warning:** DGM-W includes topography and waterbed/bathymetry. The nominal 2022 product combines methods and measurement dates; consult its data-source map for later quality assessment.
- **Role:** Only building `1` on Scharhörn. Its 0–20 m ring had 2,056 / 2,056 valid 1 m pixels, and its 20–100 m ring had 33,321 / 33,321; geometry and raster pixel coverage both 100%. This is native-resolution coverage, not final 5 m acceptance.

### SH: Schleswig-Holstein LVermGeo DGM1 nominal 2021

- **Provider:** Landesamt für Vermessung und Geoinformation Schleswig-Holstein (LVermGeo SH).
- **Official download client:** https://geodaten.schleswig-holstein.de/gaialight-sh/_apps/dladownload/dl-dgm1.html
- **Product reference:** https://www.schleswig-holstein.de/DE/landesregierung/ministerien-behoerden/LVERMGEOSH/Service/serviceGeobasisdaten/geodatenService_Geobasisdaten_DGM
- **Original download:** two individually selected files, delivered as auto-named `Mehrfachdownload_*.zip` archives, each containing a single `.xyz` file. Original archive names are preserved below.
- **Tile 555/5939:** `raw/HAM/terrain/lvermgeo_sh/Mehrfachdownload_nY2H30_FnpEbr.zip`; archive SHA-256 `907b0a0a9c297cbbce2b69533f0822a7fa9746f96b20c5b745d06cf92a3b8e83`; member `dgm1_32_555_5939_1_sh_2021.xyz`.
- **Tile 556/5939:** `raw/HAM/terrain/lvermgeo_sh/Mehrfachdownload_3S6dxh_eZFhh0.zip`; archive SHA-256 `174cb0c6d6b771d559bbbcff2c9fe6eca82bfd469ce9d92e12a4eb6f232e5298`; member `dgm1_32_556_5939_1_sh_2021.xyz`.
- **Derived 1 m GeoTIFFs:** `processed/HAM/derived/dgm1_sh_1m/dgm1_32_{555,556}_5939_1_sh_2021.tif`; generator `scripts/m1t/convert_sh_xyz.py`; conversion metadata `runs/ham_m1_citywide/qa/sh_dgm1_conversion_manifest.json` contains derived-file hashes.
- **Grid:** exactly 1,000,000 records per XYZ; first row pixel centres at `(555000.5, 5939999.5)` and `(556000.5, 5939999.5)`. The converter verified each coordinate, then wrote EPSG:25832 1 m GeoTIFFs without a 0.5 m shift.
- **Observed value ranges:** 555: 13.73–26.86 m; 556: 15.83–28.47 m.
- **Vertical reference:** DHHN2016 is Schleswig-Holstein's official height system; exact source-tile height-system metadata is still to be independently documented. **Licence:** CC BY 4.0; state attribution `© GeoBasis-DE/LVermGeo SH/CC-BY 4.0` (per official open-geodata licensing notice).
- **Role:** Supplement 23 buildings near tile row 5939. A temporary four-tile mosaic using two LGV tiles and two derived SH tiles gave **23/23** successful native 1 m exact-ring coverage tests; minimum valid fraction 1.0 for both rings. Report: `runs/ham_m1_citywide/qa/sh_boundary_ring_qa_1m.csv`.

### NI: Niedersachsen LGLN DGM1 nominal 2025

- **Provider:** Landesamt für Geoinformation und Landesvermessung Niedersachsen (LGLN).
- **Official STAC catalogue:** https://dgm.stac.lgln.niedersachsen.de/
- **Exact STAC item ID:** `dgm1_32_552_5924_1_ni_2025`; catalogue `datetime`: `2025-03-06T00:00:00Z`, not necessarily actual capture date.
- **Raster URL:** https://dgm1.s3.eu-de.cloud-object-storage.appdomain.cloud/L2502/Vollkacheln/dgm1_32_552_5924_1_ni_2025.tif
- **Metadata XML URL:** https://dgm1.s3.eu-de.cloud-object-storage.appdomain.cloud/L2502/Vollkacheln/dgm1_32_552_5924_1_ni_2025.xml
- **Local source:** `raw/HAM/terrain/lgln_ni_dgm1/dgm1_32_552_5924_1_ni_2025.tif`; **SHA-256:** `695acc10fe4bc04079df8d59629ab04c7e7380bcab6f63360a6f5f9201794a37`.
- **Local metadata:** same directory, `.xml`; **SHA-256:** `75f124daa6603efedc0b93b4e7693d16e9c094b65b1aeb230492bc4d006c6987`.
- **Observed raster:** EPSG:25832, 1 m, 1,000 × 1,000, bounds `(552000,5924000,553000,5925000)`, nodata `-9999`; all 1,000,000 pixels valid; elevation range 2.803–19.354 m.
- **Vertical reference:** DHHN2016/NHN from official LGLN product description. **Licence:** CC BY 4.0; credit LGLN Niedersachsen.
- **Role:** Supplement buildings `9091`, `9152`, `9158`. All 3 passed native 1 m exact-ring coverage in the temporary two-tile LGV + LGLN mosaic. Report: `runs/ham_m1_citywide/qa/ni_boundary_ring_qa_1m.csv`.
- **Rejected alternative:** STAC also returned a 2015 edition for the same tile. The newer nominal 2025 file was provisionally selected, with temporal mismatch retained as a source-quality issue.

## 3. Spatial assignment and remaining QA

| Source category | Buildings | Evidence level |
| --- | ---: | --- |
| LGV tile-footprint criterion >=99% | 341,503 | **Geometric screen only**, no all-city valid-pixel QA yet |
| WSV Scharhörn | 1 | Native 1 m exact-ring QA passed |
| SH supplement | 23 | Native 1 m exact-ring QA passed |
| NI supplement | 3 | Native 1 m exact-ring QA passed |
| **Total study population** | **341,530** | **5 m features not yet generated** |

The selection is by source requirement, **not** proof of vertical consistency or final acceptance of all ring medians. The supplementary tiles repair identified source-footprint gaps but do not remove the need to mask nodata and validate the complete building population after resampling.

## 4. Cross-source seam QA: unresolved, do not infer a 10 km datum mismatch

An **initial exploratory seam diagnostic was contaminated or at least rendered uninterpretable by extreme values**, likely including nodata sentinel values not masked as expected. Its reported numbers were:

| Seam | Valid positions claimed by initial script | Initial median gradient-adjusted residual | Initial p95 abs residual | Interpretation |
| --- | ---: | ---: | ---: | --- |
| HH / SH at easting tile 555, north boundary | 1,000 | +10,017.44 m | 10,021.2402 m | **INVALID / investigate masking** |
| HH / SH at easting tile 556, north boundary | 1,000 | −0.07 m | 0.255 m | Plausible, but provisional |
| HH / NI between easting tiles 552–553 | 1,000 | −10,013.3582 m | 10,017.5656 m | **INVALID / investigate masking** |

These are **not evidence that the federal states use vertical datums differing by 10 km**. They are an urgent reason to inspect pixel values and their masks. In the prior seam code, `rasterio.read(masked=True)` only masks values recognized by the source raster's metadata; an additional invalid sentinel inside otherwise unmasked pixels would remain numerically present. The exact cause must be diagnosed from the original border pixels, not asserted from the residual magnitude alone.

**Corrective action:** run `scripts/m1t/diagnose_ham_source_seams.py`. It preserves the original QA file and generates a separate v2 diagnostic with raw invalid-value counts and seam statistics after conservative invalid-value exclusion. No correction or offset is applied. If too few clean comparisons remain, report `INCONCLUSIVE` rather than `PASS`.

## 5. Conditions before the 5 m final terrain build

1. Resolve seam data validity; compare source seam residuals globally and **near the affected buildings**, and inspect any conspicuous discontinuities geographically. No arbitrary datum correction.
2. Independently check each source's vertical reference, with special attention to SH's source-specific documentation and the WSV composite source.
3. Freeze a source-priority rule with a per-building source flag and a nodata-aware **1 m to 5 m** aggregation rule; preserve the fraction of valid 1 m cells per output cell.
4. Run a 5 m pilot on the 27 exceptions plus representative mainland buildings. Audit local/neighbourhood geometric and valid-pixel coverage and a sample of T50/T25 values against native data.
5. Run citywide extraction on the **unchanged 341,530-building Phase 3 population**. Missingness must be explicit, with no imputation.
6. Record final scripts, manifests, outputs and their SHA-256 hashes, source credits and reproducible invocation; then archive and commit the source code/documentation. **Do not overwrite original downloaded rasters or historic audit outputs.**

## 6. Reproduction: current acquisition-stage commands

From `C:\Users\C.Price\Habnetic\resilient-housing-bayes` with the `data` geospatial environment:

```powershell
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\convert_sh_xyz.py
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\validate_sh_boundary.py
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\validate_ni_boundary.py
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\diagnose_ham_source_seams.py
```

**Inputs:** four downloaded source collections and `processed/HAM/derived/buildings_ham.gpkg`.
**Outputs:** SH-derived GeoTIFFs, per-building ring QA CSVs, and separate seam-diagnostic JSON.
**Reproducibility:** See source identifiers and SHA-256 values above; pin the `data` Git commit at archive time. Exact environment version pinning remains to be recorded.
**Scope limitation:** This is terrain provenance only. Buildings, hydrography and hazard source provenance are separate tasks.

## 7. Nodata diagnosis and corrected seam assessment

**Review date:** 2026-11-08

The initial exploratory seam audit reported apparent
elevation discontinuities of approximately 10,000 m.

Investigation identified stored -9999 values in Hamburg LGV
rasters that were not recognised by their declared nodata mask.

These values are invalid elevations and contaminated the
original comparison.

### Corrected diagnostic results

| Boundary | HH unmasked -9999 pixels | Clean seam positions | Near-building positions | Near-building median residual (m) | Near-building P95 absolute residual (m) |
|---|---:|---:|---:|---:|---:|
| HH_SH_555 | 392,638 | 199/1000 | 150/150 | -0.055 | 0.220 |
| HH_SH_556 | 0 | 1000/1000 | 200/200 | -0.065 | 0.286 |
| HH_NI_552 | 268,863 | 209/1000 | 209/400 | -0.032 | 0.228 |

### Interpretation

After excluding invalid elevations, the inspected source
boundaries show small gradient-adjusted residuals.

The original extreme residuals are attributable to invalid
source elevations entering the comparison.

The corrected results provide preliminary evidence of
cross-source consistency where valid pixels are available.

They do not establish absolute vertical accuracy, equivalence
of height-reference systems, or final 5 m model validity.

### Required processing correction

The Hamburg 1 m to 5 m preparation must:

1. Apply each source's declared raster validity mask.
2. Explicitly exclude unmasked -9999 elevation values.
3. Exclude non-finite values.
4. Preserve source identity and valid-source-pixel fractions.
5. Never replace missing terrain with zero elevation.
6. Validate boundary buildings after 5 m aggregation.

The earlier seam report is retained as evidence of the
diagnostic failure. It must not be used as a valid comparison.

### Status

Source acquisition and known geometric coverage gaps resolved.

Native-resolution supplementary boundary QA completed.

Cross-source seam validity diagnosed; preliminary residuals
are geographically plausible.

Final elevation harmonisation and citywide 5 m validation
remain pending.

## M1-T final citywide numerical and representative spatial QA (2026-11-08)

- Derived 1 m → 5 m preprocessing completed for **884** source regions. Across HH tiles,
  **107,349,120** stored but unmasked `−9999` values were diagnosed and excluded;
  all-25-valid aggregation was applied with no imputation.
- Final regional mosaics: mainland (8200 × 8000 at 5 m) and western islands
  (1200 × 1400 at 5 m); elevation, valid-source fraction and source ID grids retained.
- Final boundary exact-ring validation: 27/27 buildings passed; both rings at
  100% actual valid coverage for those inspected sites.
- Citywide extracted population: **341,530/341,530** unique Phase 3 building IDs;
  T50/T25 measured on all; zero missing. Final numerical QA passed and verified
  342 batch Parquet checksums and exact Phase 3 ID correspondence.
- Citywide minimum actual valid elevation pixel fraction: local **1.0**,
  neighbourhood **≈0.993377**; no building below 99% in either ring.
- **398** numeric/spatial priority candidates were generated; **six** cases were
  reviewed spatially, and **392** remain individually unreviewed. The six-case
  evidence and limitations are recorded in `docs/qa/HAM_M1T_Spatial_QA.md`.
- A shared HH/SH tile footprint used valid HH elevations and filled HH nodata
  from SH; 17,644 cells retained from HH and 22,356 supplied by SH.
  Where both provider values existed, median absolute difference 0.064 m,
  p95 absolute 0.1884 m, maximum absolute 2.944 m. The maximum-discrepancy
  location remains a sensitivity-check opportunity, **not a validation failure**.
- Data provenance remains temporally heterogeneous (HH 2022 / SH 2021 /
  NI 2025 / WSV 2022), and absolute vertical accuracy was not independently verified.
- The original numerical QA report and prior exploratory seam reports are
  preserved unchanged; the separate closure manifest records subsequent review.
