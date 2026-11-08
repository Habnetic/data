# HAM M1-T: two targeted spatial QA cases

Purpose: explain the unusually low neighbourhood 25th percentile of **8629** and locate invalid 5 m pixels around **304428**. This is diagnostic evidence, not blanket validation.

From the `resilient-housing-bayes` folder on Windows:

```powershell
& ..\data\.venv\Scripts\python.exe `
    ..\data\scripts\m1t\diagnose_ham_8629_304428.py
```

Inputs (read only):

- `processed/HAM/derived/ham_dgm5_mainland_mosaic.tif`
- `runs/ham_m1_citywide/qa/ham_m1t_spatial_review.gpkg`

Outputs (new, never overwritten):

- `runs/ham_m1_citywide/qa/ham_targeted_diagnostics/ham_8629_304428_diagnostic.json`
- `ham_qa_footprints.gpkg`, two unambiguous Phase 3 building footprints.
- `ham_qa_neighbourhood_rings.gpkg`, exact 20–100 m rings.
- `ham_8629_low_quartile_pixel_centres.gpkg`, points identifying raster pixels at or below neighbourhood P25.
- `ham_304428_invalid_5m_cells.gpkg`, polygons marking invalid 5 m pixels inside the neighbourhood ring, where present.

Method: uses exactly `raster_geometry_mask(..., crop=True)` pixel-centre membership, as in the shared frozen terrain extraction method. Independent remeasurement is compared with known 8629 P25 ~8.6014 m and 304428 coverage ~0.993377. No imputation or raster edits. Geometric meaning and source quality still require interpretation. This does not by itself identify the physical cause of the terrain values.

Open the footprint, ring, low-quartile and invalid-pixel GeoPackages in QGIS (EPSG:25832) above the mainland DGM5. For 8629, locate whether the low pixels cluster on a physically plausible valley/slope or anomalous stripe. For 304428, compare invalid-pixel cells with the raster footprint boundary and check the building polygon itself. If rerunning, move or rename the existing `ham_targeted_diagnostics` output folder to keep independent runs separate.
