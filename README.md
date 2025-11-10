# 🌐 Habnetic Data

Open datasets and metadata supporting research within the **Habnetic** ecosystem.

---

## 🧭 Purpose
This repository curates public and derived datasets for studying **housing resilience**, **urban adaptation**, and **probabilistic design**.  
It includes both raw external sources (NASA, ESA, UN-Habitat, OSM) and processed, structured data ready for Bayesian modeling.

---

## 🗂 Repository Structure
```
data/
├── raw/ → Unmodified open datasets from external portals
├── processed/ → Cleaned and harmonized versions for analysis
├── metadata/ → Documentation, licenses, and provenance files
└── data_catalog.md → Overview of sources and access details
```

---

## ⚙️ Data Ethics & Licensing
- All data is open-access or redistributed under compatible public licenses.  
- Attribution and license details are maintained in `metadata/` for each source.  
- Derived datasets follow the **MIT License** where applicable, or mirror the most restrictive source license.

---

## 📊 Planned Data Domains
| Domain | Examples | Source |
|--------|-----------|---------|
| **Building Stock** | typologies, materials, retrofitting | UN-Habitat, SwissGeo, OpenStreetMap |
| **Hazards** | earthquake, flood, heatwave intensity | NASA EarthData, ESA Copernicus |
| **Climate** | temperature, rainfall, sea-level rise | NOAA, CMIP, WorldClim |
| **Socioeconomic** | cost, reconstruction time, displacement | World Bank, OECD, EMDAT |

---

## 🌍 Related Repositories
- [Resilient Housing Bayes](https://github.com/Habnetic/resilient-housing-bayes)
- [Habnetic Docs](https://github.com/Habnetic/docs)
- [Habnetic Website](https://habnetic.org)

---

© 2025 Habnetic — Open Research for Resilient Futures
