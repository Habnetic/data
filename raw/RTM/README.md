# RTM — Raw Data

This directory contains **raw input datasets** for the Rotterdam (RTM) case study.

“Raw” means:
- sourced directly from external providers
- minimally transformed (if at all)
- preserved for traceability and reproducibility

These datasets are **not used directly** in analysis or modeling.

---

## Case study focus
Rotterdam is used as a benchmark site for:
- coastal, riverine, and pluvial flooding context
- water-adjacent urban exposure
- dense port and infrastructure environments
- resilience-oriented urban analysis

---

## Folder structure
Each subfolder corresponds to a data domain:

- `buildings/` — building footprints and basic attributes  
- `climate/` — climatic forcing data (e.g. precipitation, wind)  
- `hazards/` — hazard context and regulatory constraints  
- `terrain/` — elevation and terrain context (e.g. DEM)  
- `socio/` — socioeconomic indicators (where available)  

Each dataset subfolder must contain a `SOURCE.md` documenting:
- provider and dataset name
- license
- retrieval date
- geometry / resolution
- intended use and limitations

---

## Important notes
- Raw datasets may cover **larger extents than Rotterdam** (e.g. national coverage).
- Spatial scoping (clipping, filtering) happens only in `processed/RTM/`.
- Large raw binaries are excluded from Git and referenced via metadata.

---

## Modeling intent
Data in this folder supports:
- exposure feature derivation
- prior definition
- contextual validation

It does **not** represent:
- hazard probabilities
- damage estimates
- risk outcomes

Those are produced downstream, explicitly and reproducibly.
