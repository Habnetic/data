# Hamburg M1-T: Nodata-aware 1 m → 5 m preparation (v0.1)

## Goal and scope

Convert Hamburg's four acquired source families to independent, grid-aligned 5 m elevation tiles. **Do not mosaic or run the building extractor yet.** The first run is a 7-tile pilot. This does not change the Rotterdam/Donostia processing specification, and all 341,530 Hamburg building IDs must ultimately remain in the population.

## Inputs

Run from `C:\Users\C.Price\Habnetic\resilient-housing-bayes`. The data root is inferred from the Python script location (`Habnetic/data`). Expect:

- `raw/HAM/terrain/lgv_dgm1/dgm1_hh_2022-04-30.zip`: 880 GeoTIFF tiles, 1 m, Hamburg LGV, nominal 2022, expected source SHA-256 `32b8d624af3000aa8257205b8701d6389b2a08d6c41a8b78850e6c6863be94f2`.
- `processed/HAM/derived/dgm1_sh_1m/`: two 1 m GeoTIFFs converted from LVermGeo Schleswig-Holstein DGM1 2021 XYZ source tiles, matching the saved `runs/ham_m1_citywide/qa/sh_dgm1_conversion_manifest.json` checksums.
- `raw/HAM/terrain/lgln_ni_dgm1/dgm1_32_552_5924_1_ni_2025.tif`: Niedersachsen LGLN DGM1 2025; expected SHA-256 `695acc10fe4bc04079df8d59629ab04c7e7380bcab6f63360a6f5f9201794a37`.
- `raw/HAM/terrain/wsv_dgmw_2022/*Scharhoern*.tif`: WSV DGM-W source; expected SHA-256 `b6582f0a656276b33ba4b76a8ae040f6491b85b3376a769cb917d67e32915538`. Only aligned 1 km square `(463000, 5979000, 464000, 5980000)`, containing Scharhörn building `1` and its two rings, is converted.

For original acquisition links, licences, acquisition years, height references, and seam diagnostics, see `docs/provenance/HAM_Terrain_Source_Provenance.md`. Different datasets **must retain separate source identifiers**.

## Run

```powershell
# Reproducibility baseline. Python 3.8 geospatial venv in data repository.
& ..\data\.venv\Scripts\python.exe ..\data\tests\test_m1t_ham_dgm5.py -v

# Pilot: HH tiles 555/5938, 556/5938, 553/5924;
# SH 555/5939, 556/5939; NI 552/5924; WSV Scharhörn 463/5979.
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\prepare_ham_dgm5.py --mode pilot

# Only after inspecting pilot results, run all 880 Hamburg tiles + 4 supplementals:
& ..\data\.venv\Scripts\python.exe ..\data\scripts\m1t\prepare_ham_dgm5.py --mode all
```

A repeated run refuses to overwrite an existing manifest unless `--force` is specified. File checksums are validated before any resampling. The **original 1 m data is read-only**.

## Specification

- CRS: EPSG:25832, global 5 m grid aligned at coordinates divisible by 5.
- Mean aggregation: each 5 m cell corresponds to an aligned 5 × 5 block of source 1 m samples. Invalid pixels contribute neither to numerator nor denominator.
- Explicit invalid conditions: raster metadata mask, unmasked `-9999` sentinel (found in LGV rasters), and nonfinite values. Extreme unmasked values outside `[-1000, 2000]` metres trigger an error rather than being silently accepted.
- **Conservative baseline:** a 5 m elevation is accepted only when all 25 source samples are valid (`--min-source-fraction 1.0`); otherwise output nodata `-9999`.
- Each output elevation GeoTIFF is accompanied by a 5 m `*_valid_fraction.tif` whose pixels hold the fraction of valid underlying samples between 0 and 1. A separate sensitivity experiment may use e.g. `--min-source-fraction 0.96`, but must use a distinct run and be labelled as nonbaseline.
- Output tiling: keep source providers separate. Do not allow one provider to silently overwrite another. An explicit mosaic ordering/lineage rule is required when building regional mosaics.
- Avoid loading the whole DGM-W raster into memory: only the needed Scharhörn kilometre-square is read. All sources are processed in aligned 250-row chunks.

## Outputs

- Pilot: `processed/HAM/derived/dgm5_pilot/{HH,SH,NI,WSV}/*.tif` (7 elevation grids + 7 fraction grids) and `runs/ham_m1_citywide/qa/ham_dgm5_pilot_manifest.json`.
- Full: `processed/HAM/derived/dgm5_tiles/{HH,SH,NI,WSV}/*.tif` (884 elevation grids + 884 fraction grids), plus `runs/ham_m1_citywide/qa/ham_dgm5_citywide_manifest.json`.
- Manifest includes source identity, output checksums, source valid/invalid counts, unmasked `-9999` counts, and 5 m accepted/partial/empty cells.
- Large generated rasters belong in the research archive, **not Git**. Commit scripts, tests, this README, and the small QA manifest after review.

## Validation gates

1. `test_m1t_ham_dgm5.py` unit tests pass, including one `-9999` among 24 valid source pixels, metadata-masked nodata, empty cells, 5 m grid alignment, and actual GeoTIFF write/read.
2. Pilot reports the expected 7 tiles and exposes nonzero `unmasked_minus_9999_pixels` on the two Hamburg problem tiles. The output should contain no fabricated extreme-negative elevations.
3. Independently inspect selected pilot 5 m pixel means against raw 1 m windows. Inspect the output `valid_fraction` grids and check seam behaviour near the 27 boundary cases.
4. Full run processes 884 sources without dropped or duplicated tile IDs. **This is still not full building-level validity.** Follow with exact-ring 5 m pixel QA, source seam validation after aggregation, and the shared T50/T25 extractor, then numerical/spatial QA and archive.

## Known limitations

The 27 exceptions passed **native 1 m** ring QA, not 5 m QA. The other 341,503 buildings passed a source-tile footprint test, not exhaustive valid-pixel QA. Resampling to 5 m may introduce missing cells at water/administrative edges. Vertical datum equivalence remains dependent on source metadata and seam checks. Four datasets have different nominal vintage and acquisition methods. No flood-risk validation is implied by topographic coverage.
