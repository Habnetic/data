# RTM — Water Exposure Features (v0)

This document defines the **initial exposure features** derived from
hydrography data for the Rotterdam (RTM) study area.

These features are **not probabilities**.
They are deterministic spatial metrics used as **priors or inputs**
to Bayesian models.

---

## Study area
- Location: Rotterdam, NL
- CRS: EPSG:28992 (Amersfoort / RD New)
- Units: meters

All distances and buffers assume this CRS.

---

## Feature definitions

For each building *i*:

### 1. Distance to nearest water

**Name**: `d_water_i`

**Definition**:  
Minimum Euclidean distance (in meters) from a representative point of the building footprint to the nearest hydrography centerline (TOP50NL waterdeel_lijn).

**Source datasets**:
- Buildings: `processed/RTM/derived/buildings_rtm.gpkg`
- Hydrography: `processed/RTM/derived/hydrography_rtm.gpkg`

**Notes**:
- Centroids are used as a proxy for building location
- Water features are treated as exposure context, not hazard probability

---

### 2. Water length density (250 m)

**Name**: `water_len_250_i`

**Definition**:  
Total length (in meters) of hydrography features
within a 250 m radius buffer around the building centroid.

---

### 3. Water length density (500 m)

**Name**: `water_len_500_i`

**Definition**:  
Total length (in meters) of hydrography features
within a 500 m radius buffer around the building centroid.

---
### 4. Water length density (1000 m)

**Name**: `water_len_1000_i`

**Definition**:  
Total length (in meters) of hydrography features
within a 1000 m radius buffer around the building centroid.

---
## Interpretation constraints

- Higher values indicate **greater proximity or concentration of water**
- These features **do not represent flood probability**
- No temporal dynamics are included
- No hydraulic modeling is implied

These metrics serve as **exposure proxies** only.

---

## Status
- Version: v0
- Derived from: TOP50NL hydrography (waterdeel_lijn)
- Validated spatially in QGIS
- Ready for use in exploratory analysis and Bayesian modeling
- v0 water exposure features represent proximity and density relative to the permanent linear water network (rivers, canals, waterways), not inundation or flood hazard.
