# 🌐 Habnetic Data

Open datasets and processed spatial data supporting the **Habnetic** open research project.

---

# Purpose

This repository contains the datasets used throughout the Habnetic research ecosystem.

It manages raw data, processed spatial layers, derived variables, and reproducible data products required by the Bayesian modelling framework.

The repository intentionally contains **data rather than modelling logic**. Statistical inference, conceptual definitions, and visualisation are maintained in the companion Habnetic repositories.

---

# Repository responsibilities

This repository provides:

* raw open datasets
* processed spatial datasets
* derived exposure variables
* reproducible intermediate products
* metadata describing provenance and processing

Responsibilities across the Habnetic ecosystem are intentionally separated:

* **Habnetic/data** → datasets and derived spatial products
* **Habnetic/docs** → concepts, terminology, methodology
* **resilient-housing-bayes** → Bayesian inference and statistical models
* **habnetic.github.io** → public communication

---

# Current research data

The current research focuses on urban flood prioritisation.

Study areas currently include:

* Rotterdam
* Hamburg
* Donostia-San Sebastián

The repository contains datasets supporting exposure modelling, hazard proxies, and posterior decision stability experiments.

---

# Repository structure

```text
data/
│
├── raw/
├── processed/
├── metadata/
├── exports/
└── README.md
```

Typical contents include:

* OpenStreetMap extracts
* administrative boundaries
* hydrography
* building footprints
* processed GeoPackages
* derived exposure priors
* metadata
* processing logs

---

# Data principles

The repository follows several principles:

* reproducible processing
* explicit provenance
* open-source datasets where possible
* version-controlled derived products
* consistent coordinate reference systems
* transparent processing pipelines

---

# Spatial reference systems

Each study area uses a single canonical coordinate reference system.

CRS definitions and processing conventions are maintained in the Habnetic documentation repository.

No spatial analysis should be performed outside the declared CRS for each study area.

---

# Stewardship

This repository was founded and is currently stewarded by **Mikel Martínez Mugica**.

Development is conducted openly under permissive open-source licenses. Strategic direction, data governance, repository organisation, and project stewardship currently remain under the stewardship of **Mikel Martínez Mugica**.

Contributions, corrections, and additional datasets are welcome.

---

# Data licensing

* Data sources remain subject to their original licenses.
* Attribution information is preserved whenever required.
* Derived datasets inherit upstream licensing constraints where applicable.
* No personal data is intentionally stored within this repository.

---

# Related repositories

* https://github.com/Habnetic/docs
* https://github.com/Habnetic/resilient-housing-bayes
* https://github.com/Habnetic/habnetic.github.io

---

# Links

🌐 Website: https://habnetic.org

🆔 ORCID: https://orcid.org/0009-0006-5170-4405

📫 Email: [info@habnetic.org](mailto:info@habnetic.org)

---

# License

Unless stated otherwise, the contents of this repository are released under the **MIT License**.

The **Habnetic** name, logo, visual identity, and branding assets are **not** covered by the MIT License and may not be reused without permission.

---

© 2026 Habnetic — Open research for posterior decision stability.
