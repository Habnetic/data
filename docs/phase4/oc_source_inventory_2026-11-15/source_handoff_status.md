# Habnetic Operations Center | Local source-handoff status

Generated: 2026-11-15T19:55:19.924599+00:00
Workspace: `C:\Users\C.Price\Habnetic`

## Current evidence (not an Operations Center deployment claim)

- M1-G2 frozen artifacts: **81/81 physically found**.
- M1-G2 OC comparison Parquets + manifests: **12/12 physically found**.
- Phase 3/M0 core files (`asset_metrics`, `run_metadata`, `decision_metrics` for each city): **9/9 at expected paths**.
- Mandatory three original city GPKGs: **3/3**.

## Source-blocking missing paths

- No mandatory source **paths** missing at their expected locations. Schema, join, license and public-tile gates remain.

## Discovered historical and design file families

- `DISCOVERED_DESIGN_REFERENCE`: 2 files
- `DISCOVERED_EARLIER_M1`: 729 files
- `DISCOVERED_M1G2`: 6 files
- `DISCOVERED_PHASE3`: 217 files
- `DISCOVERED_PHASE4_OTHER`: 90 files
- `DISCOVERED_UNCLASSIFIED`: 278 files

## Git references (read-only)

- **science**: branch `phase4/m1g-cross-city`; HEAD `507adc4c0e899ba01b583c35e572eb2f0faf3d47`
  - `phase3-code-freeze-20261022`: FOUND -> `5e192548d938b5356d9c90af6e072e0f7f1d0bfc`
  - `phase4-m1-complete-v1.0`: FOUND -> `0db9629c01c1f8cdceb95c59fcbea2ad4b83dbef`
  - `phase4-m1g2-scientific-audit-2026-11-15`: FOUND -> `507adc4c0e899ba01b583c35e572eb2f0faf3d47`
- **data**: branch `phase4/m1t-ham-don`; HEAD `b3878587997a98a32cbd0eaf39f00d9a6054c412`
  - `phase4-m1g2-data-gis-closure-2026-11-15`: FOUND -> `b3878587997a98a32cbd0eaf39f00d9a6054c412`
- **docs**: branch `main`; HEAD `701083f805e10cec494937efcd4c25d02f8eddfb`

## What the scanner deliberately does not certify

- It does not validate geometry joins, full DEM provenance or data redistribution licenses.
- It does not infer missing historic posterior metrics from a different experiment.
- It does not run Bayesian sampling, download data, alter Git or generate public tiles.
- Optional JFJ/CON/LUN datasets are future feasibility inputs, not required urban-app files.

## Next engineering action

Resolve any Phase 3 file-path candidates in `inventory.csv` and review their actual Parquet columns; map the original M0 outputs to building geometry. Build the first DON M1-G2 spatial join once licenses are understood.
