# Phase 3 Data Build Plan
## Hamburg and Donostia
**Purpose:** define the practical next steps to build cross-city Phase 3 inputs using the Rotterdam pipeline as the reference implementation.

---

## 1. Current situation

Rotterdam is the reference city and already has:

- raw source structure
- processed boundary / buildings / hydrography
- water proximity priors
- pluvial building-level hazard
- `phase3_assets.parquet`
- Phase 3 preprocessing runner working in `resilient-housing-bayes`

Hamburg and Donostia currently have only placeholder folders.

This means the next task is **not** modelling.  
It is **data replication under the same measurement logic**.

---

## 2. Main rule

For Hamburg and Donostia, replicate the **Rotterdam data logic**, not the Rotterdam geography.

That means keeping fixed:

- same boundary → buildings → hydrography → hazard workflow
- same building-level join key concept (`bldg_id`)
- same exposure variables:
  - `dist_to_water_m`
  - `water_len_density_250m`
  - `water_len_density_500m`
  - `water_len_density_1000m`
- same pluvial hazard construction logic
- same final Phase 3 schema:
  - `bldg_id`
  - `dist_to_water_m`
  - `water_len_density_250m`
  - `water_len_density_500m`
  - `water_len_density_1000m`
  - `H_pluvial_v1_mm`

Do **not** add city-specific features in Phase 3.

---

## 3. Folder structure to use

Mirror the Rotterdam structure for both new cities.

### Raw
```text
raw/
├── HAM/
│   ├── boundaries/
│   ├── buildings/
│   ├── climate/
│   ├── hazards/
│   │   ├── hydrography/
│   │   ├── pluvial/
│   │   └── river_margin/
│   ├── socio/
│   └── terrain/
│       └── dem/
└── DON/
    ├── boundaries/
    ├── buildings/
    ├── climate/
    ├── hazards/
    │   ├── hydrography/
    │   ├── pluvial/
    │   └── river_margin/
    ├── socio/
    └── terrain/
        └── dem/
```

### Processed
```text
processed/
├── HAM/
│   ├── normalized/
│   ├── derived/
│   ├── priors/
│   ├── hazards/
│   │   └── pluvial/
│   └── phase3_assets.parquet
└── DON/
    ├── normalized/
    ├── derived/
    ├── priors/
    ├── hazards/
    │   └── pluvial/
    └── phase3_assets.parquet
```

---

## 4. Data needed for each city

Each city needs four core raw inputs.

### A. Boundary
Purpose:
- authoritative city clip
- defines benchmark extent
- used to clip buildings and hydrography

Target raw location:
```text
raw/<CITY>/boundaries/
```

Need:
- one municipal boundary file
- source metadata in `SOURCE.md`

---

### B. Buildings
Purpose:
- generate stable building asset layer
- basis for centroids and all downstream joins

Target raw location:
```text
raw/<CITY>/buildings/
```

Need:
- building footprints for city or wider region
- polygon geometry
- source metadata in `SOURCE.md`

---

### C. Hydrography
Purpose:
- derive exposure metrics from water network geometry

Target raw location:
```text
raw/<CITY>/hazards/hydrography/
```

Need:
- preferably line-based hydrography
- rivers, canals, channels, water network geometry
- source metadata in `SOURCE.md`

---

### D. Climate / pluvial hazard input
Purpose:
- create city-level pluvial hazard metric under the same logic as RTM

Target raw location:
```text
raw/<CITY>/climate/
```

Need:
- precipitation source comparable to RTM
- same temporal aggregation logic
- source metadata in `SOURCE.md`

Optional raw hazard staging:
```text
raw/<CITY>/hazards/pluvial/
```

---

## 5. Processed outputs required per city

Each city must eventually produce the following.

### 5.1 Normalized boundary
Example target:
```text
processed/<CITY>/normalized/boundary_<city>.gpkg
```

### 5.2 Normalized buildings
Example target:
```text
processed/<CITY>/normalized/buildings.gpkg
```

Requirements:
- deterministic `bldg_id`
- same logic as RTM

### 5.3 Derived buildings clipped to city boundary
Example target:
```text
processed/<CITY>/derived/buildings_<city>.gpkg
```

### 5.4 Normalized / clipped hydrography
Example targets:
```text
processed/<CITY>/normalized/hydrography.gpkg
processed/<CITY>/derived/hydrography_<city>.gpkg
```

### 5.5 Water proximity priors
Canonical target:
```text
processed/<CITY>/priors/building_water_proximity.parquet
```

Required columns:
- `bldg_id`
- `dist_to_water_m`
- `water_len_density_250m`
- `water_len_density_500m`
- `water_len_density_1000m`

### 5.6 Building-level pluvial hazard
Canonical target:
```text
processed/<CITY>/hazards/pluvial/H_pluvial_v1_buildings.parquet
```

Required columns:
- `bldg_id`
- `H_pluvial_v1_mm`

### 5.7 Final Phase 3 asset table
Canonical target:
```text
processed/<CITY>/phase3_assets.parquet
```

Required columns:
- `bldg_id`
- `dist_to_water_m`
- `water_len_density_250m`
- `water_len_density_500m`
- `water_len_density_1000m`
- `H_pluvial_v1_mm`

---

## 6. Script strategy

Do **not** duplicate-and-mutate blindly.

Use the RTM scripts as templates, but rename and generalize carefully.

### Existing RTM script families
Current RTM logic already exists in scripts such as:

- `scripts/rtm/normalize_boundary.py`
- `scripts/rtm/normalize_buildings.py`
- `scripts/rtm/normalize_hydrography.py`
- `scripts/rtm/clip_buildings_to_rtm.py`
- `scripts/rtm/clip_hydrography_to_rtm.py`
- `scripts/rtm/compute_building_water_exposure.py`
- `scripts/rtm/hazards/pluvial/...`
- `scripts/build_phase3_assets_rtm.py`

These should be treated as the reference implementation.

---

## 7. Recommended script creation plan

### Step 1 — keep RTM scripts untouched
Do not break the working Rotterdam pipeline just because new cities now exist.

### Step 2 — create city-specific copies first
For speed and clarity, create initial city-specific scripts:

#### Hamburg
```text
scripts/ham/
├── normalize_boundary.py
├── normalize_buildings.py
├── normalize_hydrography.py
├── clip_buildings_to_ham.py
├── clip_hydrography_to_ham.py
├── compute_building_water_exposure.py
└── hazards/
    └── pluvial/
        ├── 01_download_era5_land_tp.py
        ├── 03_year_check_and_concat.py
        ├── 04_compute_H_pluvial_v1_grid.py
        └── 05_map_H_pluvial_v1_to_buildings.py
```

#### Donostia
```text
scripts/don/
├── normalize_boundary.py
├── normalize_buildings.py
├── normalize_hydrography.py
├── clip_buildings_to_don.py
├── clip_hydrography_to_don.py
├── compute_building_water_exposure.py
└── hazards/
    └── pluvial/
        ├── 01_download_era5_land_tp.py
        ├── 03_year_check_and_concat.py
        ├── 04_compute_H_pluvial_v1_grid.py
        └── 05_map_H_pluvial_v1_to_buildings.py
```

### Step 3 — duplicate RTM scripts as templates
Start by copying the RTM scripts into `ham/` and `don/`.

Then edit only:
- city code
- input/output paths
- CRS
- source filenames
- clipping boundary names
- bounding boxes for climate downloads

Do **not** change:
- feature definitions
- buffer distances
- `bldg_id` logic
- pluvial hazard aggregation logic

---

## 8. What each new script must preserve

### Boundary normalization
Must preserve:
- authoritative city boundary
- declared city CRS
- deterministic output path

### Building normalization
Must preserve:
- polygon cleaning logic
- deterministic `bldg_id`
- same ID generation rule as RTM

### Hydrography normalization
Must preserve:
- line-based hydrography processing logic
- same geometry assumptions
- same clipping logic downstream

### Building water exposure
Must preserve:
- same centroid logic
- same nearest-water distance logic
- same buffer radii: 250 / 500 / 1000 m
- same output schema

### Pluvial hazard
Must preserve:
- same climate source family if possible
- same annual-max / aggregation logic
- same building mapping logic
- same final hazard column name: `H_pluvial_v1_mm`

---

## 9. Practical order of execution

Work Hamburg first. Donostia stays staged until Hamburg Phase 3 MVP is complete.

### Hamburg order
1. Download / store raw boundary
2. Download / store raw buildings
3. Download / store raw hydrography
4. Download / store raw climate files
5. Create `SOURCE.md` for each raw domain
6. Create `scripts/ham/` by copying RTM templates
7. Run boundary normalization
8. Run building normalization
9. Run hydrography normalization
10. Clip buildings to Hamburg boundary
11. Clip hydrography to Hamburg boundary
12. Compute water proximity priors
13. Build pluvial hazard grid / building-level hazard
14. Merge into `processed/HAM/phase3_assets.parquet`
15. Run:
    ```bash
    PYTHONPATH=src python -m rhb.phase3_transfer --city HAM
    ```

### Donostia order
Only after Hamburg:
- repeat the same sequence
- no new logic

---

## 10. Minimum metadata to create for each raw source

Each raw source folder should contain a `SOURCE.md` with:

- provider
- dataset name
- access URL / portal
- license
- retrieval date
- geometry / resolution
- source CRS
- intended use in Habnetic
- limitations

This is not optional bureaucracy. It is the only thing standing between you and future confusion.

---

## 11. Immediate next actions

### A. Folder preparation
Create or align:
- `raw/HAM/...`
- `raw/DON/...`
- `processed/HAM/...`
- `processed/DON/...`

mirroring RTM structure.

### B. Hamburg source search
Identify and collect:
- Hamburg municipal boundary
- Hamburg building footprints
- Hamburg hydrography
- Hamburg ERA5-Land-compatible precipitation inputs

### C. Script bootstrapping
Copy RTM scripts into:
- `scripts/ham/`
- `scripts/don/`

but only edit and run Hamburg now.

### D. First tactical milestone
Produce:
```text
processed/HAM/priors/building_water_proximity.parquet
processed/HAM/hazards/pluvial/H_pluvial_v1_buildings.parquet
processed/HAM/phase3_assets.parquet
```

Only then is Hamburg ready for the Phase 3 transfer runner.

---

## 12. Suggested first script tasks

### First scripts to clone for Hamburg
1. `normalize_boundary.py`
2. `normalize_buildings.py`
3. `normalize_hydrography.py`
4. `clip_buildings_to_rtm.py` → rename to `clip_buildings_to_ham.py`
5. `clip_hydrography_to_rtm.py` → rename to `clip_hydrography_to_ham.py`
6. `compute_building_water_exposure.py`
7. pluvial hazard mapping scripts
8. `build_phase3_assets_rtm.py` → future `build_phase3_assets_ham.py`

### First scripts to leave alone
- all RTM originals
- `phase3_transfer.py`
- `transfer_scaling.py`
- `support_diagnostics.py`

---

## 13. Closure criterion for this work package

This work package is complete when Hamburg has:

- raw boundary / buildings / hydrography / climate sources documented
- normalized and clipped spatial layers
- building water priors
- building-level pluvial hazard
- final `phase3_assets.parquet`
- successful execution through the existing Phase 3 transfer runner

Donostia is not required for this milestone.

---

## 14. Bottom line

The next useful step is not more theory.

It is:
1. collect Hamburg raw inputs,
2. clone the Rotterdam spatial scripts,
3. rebuild the same measurement system for Hamburg,
4. then run Phase 3 transfer honestly.

That is the experiment.
