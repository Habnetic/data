# 🌐 Habnetic Data

Open datasets and metadata supporting research within the **Habnetic** ecosystem.

---

## 🧭 Purpose
This repository curates public and derived datasets for studying **housing resilience**, **urban adaptation**, and **probabilistic design**.

It contains:
- raw external datasets (e.g. OSM, CBS, PDOK, NASA, ESA)
- normalized and derived spatial layers
- metadata required to ensure **reproducibility and numerical correctness**

All modeling logic, theory, and interpretation live outside this repository.

---

## 🗂 Repository Structure

```
data/
│ data_catalog.md
│ LICENSE
│ README.md
│
├── metadata/
│ │ targets.yaml
│ │ crs_registry.yaml
│ │
│ └── sources/
│ RTM_sources.md
│ SFO_sources.md
│ SYN_sources.md
│
├── processed/
│ ├── RTM/
│ │ ├── normalized/
│ │ │ hydrography.gpkg
│ │ │ boundary_rtm.gpkg
│ │ │ buildings.gpkg
│ │ ├── derived/
│ │ │ hydrography_rtm.gpkg
│ │ │ buildings_rtm.gpkg
│ │ └── priors/
│ │ (generated exposure priors)
│ ├── SFO/
│ │ ├── normalized/
│ │ ├── derived/
│ │ └── priors/
│ └── SYN/
│ ├── normalized/
│ ├── derived/
│ └── priors/
│
└── raw/
├── RTM/
│ ├── buildings/
│ │ └── osm/
│ │ └── SOURCE.md
│ ├── climate/
│ ├── hazards/
│ ├── socio/
│ └── boundaries/
│ └── rotterdam_municipality/
│ └── SOURCE.md
├── SFO/
│ ├── buildings/
│ ├── climate/
│ ├── hazards/
│ └── socio/
└── SYN/
├── buildings/
├── climate/
├── hazards/
└── socio/
```


---

## 🧠 Spatial reference (CRS)

All spatial datasets in this repository follow a **one-CRS-per-study-area** rule.

- CRS choices are recorded in  
  `metadata/crs_registry.yaml`
- The rationale and rules are documented in  
  **Habnetic Docs → Reference → CRS Policy**

👉 See: https://github.com/Habnetic/docs

No spatial analysis should be performed unless datasets are normalized to the declared CRS for their study area.

---

## ⚙️ Data ethics & licensing
- All data is open-access or redistributed under compatible public licenses.
- Attribution and license details are maintained in `metadata/sources/`.
- Derived datasets inherit the most restrictive upstream license where applicable.
- No personal data is intentionally stored in this repository.

---

## 📊 Data domains (non-exhaustive)

| Domain | Examples | Sources |
|------|---------|--------|
| **Buildings** | footprints, height proxies, typologies | OpenStreetMap, national cadastres |
| **Hazards** | flood proximity, seismic context, heat | PDOK, FEMA, Copernicus |
| **Climate** | temperature, precipitation, sea level | NOAA, CMIP, WorldClim |
| **Socioeconomic** | costs, exposure, displacement | World Bank, OECD |

---

## 🌍 Related repositories
- https://github.com/Habnetic/docs  
- https://github.com/Habnetic/resilient-housing-bayes  
- https://habnetic.org  

---

## License
Unless otherwise stated, the contents of this repository are licensed under the MIT License.

The Habnetic name and logo are not licensed for reuse or endorsement.

---

© 2026 Habnetic — Open Research for Resilient Futures
