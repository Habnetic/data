# 🌐 Habnetic Data

Canonical research data, provenance records, and reproducible data-preparation workflows for **Habnetic**.

Habnetic is an open research project exploring probabilistic decision-making under uncertainty, with urban flood-risk prioritisation as its first reference application.

---

## Purpose

This repository contains the data layer used across the Habnetic research ecosystem.

It stores selected **reviewed, versioned research inputs**, metadata, provenance records, and scripts used to construct research-ready spatial inputs. Most original third-party geodata and large generated outputs are retained locally, **not distributed through this repository**.

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

The repository documents sources and processing workflows supporting:

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

**DOI (October 2026, manuscript v1.1):**
https://doi.org/10.5281/zenodo.23599344

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

Original third-party downloads are kept locally by default. Where source bytes are not distributed, `SOURCE.md` and acquisition manifests record provider, product, version, date, location, and licence evidence when known. The original upstream licensing conditions still apply.

For example, `raw/HAM/boundaries/alkis_verwaltungsgrenzen_hamburg.GML` is retained **locally** and excluded from the current Git index; its source record remains public in `raw/HAM/boundaries/SOURCE.md`. Removing a file from the current Git index does not erase earlier commits.

### `processed/`

Canonical research-ready datasets used by Habnetic analyses.

Only selected processed products are versioned, subject to source and redistribution review. Generated intermediates are ignored by default.

**Selected files currently kept in Git:**

- `processed/DON/hazards/pluvial/H_pluvial_v1_buildings.parquet` (7,755 building-level hazard-proxy values);
- `processed/HAM/hazards/pluvial/H_pluvial_v1_buildings.parquet` (341,530 values);
- `processed/RTM/hazards/pluvial/H_pluvial_v1_buildings.parquet` (221,324 values);
- `processed/RTM/priors/building_water_proximity_v3.parquet` (221,324 IDs and derived hydrographic-distance fields).

The three `H_pluvial_v1_buildings.parquet` files contain building IDs, a numerical precipitation-derived hazard proxy, and provenance labels; they contain **no explicit geometry or coordinate columns**. Their precise original ERA5 dataset and historical use terms remain subject to lineage review.

**Local-only legacy file:** `processed/RTM/priors/building_water_proximity.parquet` combines OSM building attributes (including building tags, name and postal code) with derived exposure indicators. It is **excluded from current Git distribution**; the older [`priors/README.md`](processed/RTM/priors/README.md) has been updated to reflect its actual schema.

A reduced schema does not by itself settle database rights. The underlying building and hydrography sources and each public artefact must still be assessed before reuse or distribution.

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

Selected QA manifests and validation artefacts retained when useful for documenting a data-processing step. Bulk terrain batches, intermediate mosaics, and local diagnostics are not intended for automatic publication.

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

The `.gitignore` file defines the default storage policy **for untracked files**. It does not undo files already committed or remove blobs from historical Git commits.

### Publication boundary

- **Public by design:** Habnetic-authored code, processing methods, source references, licence notices, selected research inputs, and reviewed QA records.
- **Local by default:** raw geospatial datasets, complete building/terrain databases, bulk intermediate files, and legacy OSM attribute extracts.
- **Release only after review:** any building-level join, geospatial tile, download bundle, or derivative database that may contain or expose substantial third-party content.

A private Git repository does **not** automatically make files private when they are served by a website. In particular, files under a web application's public/static directory can be downloaded by visitors if that application is deployed. Access control and asset-level rights review are separate release requirements.

---

## Data Provenance

Every research dataset should be traceable to its source and transformation history.

Source documentation is stored primarily under:

```text
metadata/sources/
raw/<CITY>/**/SOURCE.md
```

Dataset-specific processing decisions should remain reproducible from the scripts and accompanying documentation.

When source data are kept local or cannot be redistributed, Habnetic should preserve enough metadata to reacquire and reconstruct derived inputs where the source terms and continued availability permit. A provider-wide licence statement is not sufficient evidence for an unidentified historical download.

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
- no intentional public redistribution of address/name attributes or other identifying building metadata without explicit review.

---

## Next Research Direction

Phase 4 extends the data layer while preserving the Phase 3 baseline. The M1 topography work has been completed and audited separately from the historical Phase 3 paper. Later milestones remain research directions rather than guaranteed releases.

The working progression is:

```text
M0 — Phase 3 baseline
M1 — + topography (completed)
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
- Phase 3 publication: https://doi.org/10.5281/zenodo.23599344
- ORCID: https://orcid.org/0009-0006-5170-4405

---

## Stewardship

This repository was founded and is currently stewarded by **Mikel Martinez Mugica**.

Contributions, corrections, provenance improvements, and additional open datasets are welcome.

---

## Data Licensing

**The repository's MIT licence applies to original Habnetic-authored code and documentation only, unless stated otherwise.** It does not relicense third-party geographic data, downloaded files, or derived datasets that remain subject to upstream rights and conditions.

Known or documented source families include:

- **Rotterdam buildings:** OpenStreetMap, via Geofabrik Zuid-Holland, subject to the **Open Database License (ODbL) 1.0**. See [`raw/RTM/buildings/osm/SOURCE.md`](raw/RTM/buildings/osm/SOURCE.md). Attribution, derived-database classification, and any applicable availability obligations must be assessed **per exported product**.
- **Hamburg administrative boundary:** LGV Hamburg, **Datenlizenz Deutschland Namensnennung 2.0 (DL-DE BY 2.0)**, as recorded in [`raw/HAM/boundaries/SOURCE.md`](raw/HAM/boundaries/SOURCE.md). The source GML is local-only in the current Git tree; source and transformation credit must be retained where used.
- **Pluvial hazard proxy:** a climate-data derivation described in the Phase 3 research. The exact historical ERA5 product, version, citation, and applicable licence still require verification before an unconditional redistribution claim.
- **RTM exposure indicators:** derived from building and hydrography inputs. The exact historical hydrography product/version and export-level obligations remain under review.

**Rights status is evidence-based, not automatic clearance.** A `SOURCE.md` record is an important provenance clue, but should be tied to the exact acquired file, its terms, its transformations, and the proposed public output.

The Habnetic name, logo, visual identity, and branding assets are not covered by the MIT licence and may not be reused for endorsement without permission.

---

## License

See [`LICENSE`](LICENSE) for repository-level licensing terms.

---

© 2026 Habnetic — Open research for probabilistic decision-making under uncertainty.
