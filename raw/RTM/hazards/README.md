# RTM Hazards — Raw Data

This folder contains **raw hazard-related datasets** for the Rotterdam (RTM) case study.

The datasets here represent **hazard context and regulatory constraints**, not probabilistic hazard realizations.
They are used to derive exposure indicators and priors in downstream modeling.

## Scope
Included data may cover:
- Hydrography (rivers, canals, waterways)
- Regulatory river margins and setback zones
- Flood-related spatial constraints (where available)

## Out of scope (at v0)
- Flood depth rasters
- Return-period probability maps
- Hydrodynamic simulations

## Data philosophy
- Raw files are kept as close as possible to the original source.
- Large binaries are stored outside Git (see `.gitignore`).
- Each dataset subfolder must include a `SOURCE.md` describing provenance, license, and usage intent.

## Usage
Data in this folder is **not used directly** in analysis.
It is normalized and clipped into `processed/RTM/` via reproducible scripts.

This separation is intentional.
