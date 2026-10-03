# 🌐 Habnetic Data

Canonical research data, provenance records, and reproducible data-preparation workflows for **Habnetic**.

Habnetic is an open research project exploring probabilistic decision-making under uncertainty, with urban flood-risk prioritisation as its first reference application.

---

## Purpose

This repository contains the data layer used across the Habnetic research ecosystem.

It stores selected source data, canonical processed datasets, metadata, provenance records, and scripts used to construct research-ready spatial inputs.

The repository is intentionally separate from statistical inference and publication source files:

- **Habnetic/data** → data, provenance, and data-preparation workflows
- **Habnetic/docs** → methodology, theory, decisions, and research history
- **resilient-housing-bayes** → Bayesian inference, experiments, and decision-stability code
- **habnetic-papers** → publication source and archival material
- **habnetic.org** → public-facing project website

---

## Current Research Data

The current reference application is urban flood-risk prioritisation.

Study areas:

- **RTM** — Rotterdam
- **HAM** — Hamburg
- **DON** — Donostia / San Sebastián

The repository includes data supporting:

- administrative boundaries;
- building footprints;
- hydrography;
- pluvial-hazard proxies;
- water-proximity / exposure variables;
- canonical processed building-level hazard inputs;
- source and CRS metadata;
- reproducible data-building scripts.

Phase 3 used harmonised processed inputs for RTM, HAM, and DON to support cross-city decision-stability stress testing.

---

## Phase 3 Publication

The Phase 3 research is published as:

**Posterior-Based Decision Stability under Cross-City Stress Testing in Urban Flood Risk Prioritisation**

Mikel Martinez Mugica  
Independent Researcher, Habnetic  
2026

**DOI:**  
https://doi.org/10.5281/zenodo.23110714

**ORCID:**  
https://orcid.org/0009-0006-5170-4405

The modelling and inference code associated with the publication lives in:

https://github.com/Habnetic/resilient-housing-bayes

---

## Repository Structure

```text
data/
│
├── metadata/
│   ├── priors/
│   ├── sources/
│   ├── crs_registry.yaml
│   └── targets.yaml
│
├── processed/
│   ├── DON/
│   ├── HAM/
│   └── RTM/
│
├── raw/
│   ├── DON/
│   ├── HAM/
│   ├── RTM/
│   └── shared/
│
├── runs/
│   └── selected QA and validation artefacts
│
├── scripts/
│   ├── don/
│   ├── ham/
│   ├── rtm/
│   └── shared/
│
├── data_catalog.md
├── requirements.txt
├── LICENSE
└── README.md
```

Historical planning and working notes may also remain in the repository when they document how published datasets were produced.

---

## Data Layers

### `raw/`

Source material and source documentation.

Large downloads and formats that are impractical or inappropriate to version are excluded through `.gitignore`. Where raw data are not stored directly, `SOURCE.md` files record their origin and acquisition context.

Original upstream licensing conditions still apply.

### `processed/`

Canonical research-ready datasets used by Habnetic analyses.

Only selected processed products needed for reproducibility are versioned. Generated intermediates are ignored by default.

Current versioned products include building-level pluvial-hazard inputs for RTM, HAM, and DON, together with selected Rotterdam prior / exposure products.

### `metadata/`

Provenance and data-governance information, including:

- source records;
- CRS definitions;
- target definitions;
- prior documentation.

### `scripts/`

Reproducible data-preparation workflows.

These scripts perform operations such as:

- downloading source data;
- clipping and normalising city layers;
- harmonising hydrography and buildings;
- constructing exposure variables;
- computing and mapping hazard proxies;
- assembling Phase 3 city-level assets.

Statistical inference does **not** belong here. It is maintained in `resilient-housing-bayes`.

### `runs/`

Selected QA and validation artefacts retained when useful for documenting a data-processing step.

---

## Reproducibility Policy

Habnetic distinguishes between:

1. **source data**;
2. **processed canonical inputs**;
3. **generated intermediates**;
4. **model outputs**.

Not every local file is intended for Git.

As a general rule:

- small source files may be versioned when redistribution is appropriate;
- large downloads are excluded and documented through provenance files;
- selected processed datasets required for reproducibility may be versioned;
- disposable intermediates are ignored;
- statistical posterior outputs belong in the research-code workflow rather than this repository.

The `.gitignore` file defines the current repository-level storage policy.

---

## Data Provenance

Every research dataset should be traceable to its source and transformation history.

Source documentation is stored primarily under:

```text
metadata/sources/
raw/<CITY>/**/SOURCE.md
```

Dataset-specific processing decisions should remain reproducible from the scripts and accompanying documentation.

When source data cannot be redistributed, Habnetic should preserve enough metadata to reacquire and reconstruct the derived dataset where licensing and availability permit.

---

## Coordinate Reference Systems

Spatial analysis should use the declared CRS for each study area.

Canonical CRS definitions are stored in:

[`metadata/crs_registry.yaml`](metadata/crs_registry.yaml)

CRS transformations should be explicit and reproducible. Silent reprojection or undocumented coordinate assumptions should be avoided.

---

## Data Principles

The data workflow follows several principles:

- explicit provenance;
- reproducible processing;
- open data where practical and legally permitted;
- consistent spatial reference systems;
- versioned canonical research inputs;
- clear separation between source, processed, and generated data;
- preservation of upstream licensing and attribution requirements;
- no intentional storage of personal data.

---

## Next Research Direction

Phase 4 will extend the data layer incrementally while preserving the Phase 3 baseline.

The working progression is:

```text
M0 — Phase 3 baseline
M1 — + topography
M2 — + more realistic hazard representation
M3 — + improved vulnerability / exposure
M4 — + observed outcomes
```

New data layers should be added only with explicit provenance, units, CRS, processing steps, and a reproducible path from source to research-ready input.

---

## Related Repositories

- Documentation: https://github.com/Habnetic/docs
- Research code: https://github.com/Habnetic/resilient-housing-bayes
- Habnetic organisation: https://github.com/Habnetic
- Website: https://habnetic.org
- Phase 3 publication: https://doi.org/10.5281/zenodo.23110714
- ORCID: https://orcid.org/0009-0006-5170-4405

---

## Stewardship

This repository was founded and is currently stewarded by **Mikel Martinez Mugica**.

Contributions, corrections, provenance improvements, and additional open datasets are welcome.

---

## Data Licensing

Source datasets remain subject to their original licences and attribution requirements.

Derived datasets may inherit upstream licensing constraints. Inclusion in this repository does not replace or override the licence of the original data provider.

Unless otherwise stated, Habnetic-authored code and documentation in this repository are released under the repository licence.

The Habnetic name, logo, visual identity, and branding assets are not covered by that licence and may not be reused for endorsement without permission.

---

## License

See [`LICENSE`](LICENSE) for repository-level licensing terms.

---

© 2026 Habnetic — Open research for probabilistic decision-making under uncertainty.
