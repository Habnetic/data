"""Targeted, read-only Hamburg M1-T spatial QA for buildings 8629 and 304428.

Usage from resilient-housing-bayes:
    & ../data/.venv/Scripts/python.exe ../data/scripts/m1t/diagnose_ham_8629_304428.py

Outputs vector QA layers, a JSON report, and no raster modifications.
Uses the SAME raster_geometry_mask pixel-centre membership as extract_terrain.py.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import raster_geometry_mask
from rasterio.transform import xy
from shapely.geometry import Point, box, mapping

ROOT = Path(__file__).resolve().parents[2]
QA = ROOT / "runs/ham_m1_citywide/qa"
REVIEW = QA / "ham_m1t_spatial_review.gpkg"
RASTER = ROOT / "processed/HAM/derived/ham_dgm5_mainland_mosaic.tif"
OUTPUT = QA / "ham_targeted_diagnostics"
IDS = ("8629", "304428")


def inspect_ring(src, polygon):
    """Return raster pixels classified with the frozen extractor's ring mask."""
    outside, _, window = raster_geometry_mask(src, [mapping(polygon)], crop=True)
    arr = src.read(1, window=window, masked=True)
    inside = ~outside
    valid = inside & ~np.ma.getmaskarray(arr) & np.isfinite(arr.data)
    # Final Hamburg DGM5 uses a defined nodata mask. This is an extra safeguard.
    valid &= arr.data != -9999.0
    return arr.data, inside, valid, src.window_transform(window)


def pixels_to_gdf(rows, cols, transform, *, valid_values=None, kind="cell"):
    geometries = []
    values = []
    for r, c in zip(rows.tolist(), cols.tolist()):
        x, y = xy(transform, int(r), int(c), offset="center")
        geometries.append(Point(x, y) if kind == "point" else box(x - 2.5, y - 2.5, x + 2.5, y + 2.5))
        if valid_values is not None:
            values.append(float(valid_values[r, c]))
    data = {"elevation_m": values} if valid_values is not None else {"invalid_pixel": [1] * len(geometries)}
    return gpd.GeoDataFrame(data, geometry=geometries, crs="EPSG:25832")


def write_layer(gdf, filename, layer):
    if gdf.empty:
        return None
    output = OUTPUT / filename
    if output.exists():
        raise FileExistsError("Refusing to overwrite existing diagnostic: {}".format(output))
    gdf.to_file(str(output), driver="GPKG", layer=layer)
    return str(output)


def main():
    for path in (REVIEW, RASTER):
        if not path.is_file():
            raise FileNotFoundError(path)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT / "ham_8629_304428_diagnostic.json"
    if report_path.exists():
        raise FileExistsError("Refusing to overwrite existing report: {}".format(report_path))

    review = gpd.read_file(str(REVIEW))
    selection = review.loc[review.bldg_id.astype(str).isin(IDS)].copy()
    if len(selection) != 2 or set(selection.bldg_id.astype(str)) != set(IDS):
        raise ValueError("Expected both unique building IDs in spatial review layer")
    if selection.crs is None or selection.crs.to_epsg() != 25832:
        raise ValueError("Unexpected GeoPackage CRS")

    selection["bldg_id"] = selection.bldg_id.astype(str)
    footprint_output = write_layer(selection[["bldg_id", "geometry"]], "ham_qa_footprints.gpkg", "footprints")
    ring_records = []
    results = {}

    with rasterio.open(str(RASTER)) as src:
        if src.crs.to_epsg() != 25832 or not np.allclose(src.res, (5, 5)):
            raise ValueError("Expected Hamburg EPSG:25832 at 5 m")
        for _, row in selection.iterrows():
            bldg_id = row.bldg_id
            footprint = row.geometry
            local_20 = footprint.buffer(20)
            neighbourhood = footprint.buffer(100).difference(local_20)
            ring_records.append({"bldg_id": bldg_id, "geometry": neighbourhood})
            data, inside, valid, transform = inspect_ring(src, neighbourhood)
            values = data[valid]
            total_pixels = int(inside.sum())
            valid_pixels = int(valid.sum())
            if valid_pixels < 20:
                raise ValueError("Insufficient valid elevation pixels for {}".format(bldg_id))
            statistics = {
                "footprint_area_m2": float(footprint.area),
                "footprint_bounds": list(map(float, footprint.bounds)),
                "neighbourhood_pixels": total_pixels,
                "neighbourhood_valid_pixels": valid_pixels,
                "neighbourhood_invalid_pixels": total_pixels - valid_pixels,
                "neighbourhood_valid_fraction": valid_pixels / total_pixels,
                "neighbourhood_min_m": float(values.min()),
                "neighbourhood_p25_m": float(np.percentile(values, 25)),
                "neighbourhood_median_m": float(np.median(values)),
                "neighbourhood_max_m": float(values.max()),
            }
            results[bldg_id] = statistics

            if bldg_id == "8629":
                lower_quartile = valid & (data <= statistics["neighbourhood_p25_m"])
                rows, cols = np.where(lower_quartile)
                points = pixels_to_gdf(rows, cols, transform, valid_values=data, kind="point")
                statistics["lower_quartile_pixel_count"] = len(points)
                statistics["lower_quartile_pixel_layer"] = write_layer(
                    points, "ham_8629_low_quartile_pixel_centres.gpkg", "low_quartile"
                )
                print("8629: neighbourhood P25 {:.4f} m; lower-quartile pixels {}".format(
                    statistics["neighbourhood_p25_m"], len(points)
                ))
            elif bldg_id == "304428":
                invalid = inside & ~valid
                rows, cols = np.where(invalid)
                squares = pixels_to_gdf(rows, cols, transform, kind="cell")
                statistics["invalid_pixel_layer"] = write_layer(
                    squares, "ham_304428_invalid_5m_cells.gpkg", "invalid_pixels"
                )
                print("304428: valid coverage {:.4%}; invalid cells {}; footprint area {:.2f} m²".format(
                    statistics["neighbourhood_valid_fraction"], len(squares), footprint.area
                ))

    rings = gpd.GeoDataFrame(ring_records, geometry="geometry", crs="EPSG:25832")
    rings_output = write_layer(rings, "ham_qa_neighbourhood_rings.gpkg", "neighbourhood_rings")
    report = {
        "status": "DIAGNOSTIC_ONLY_NOT_SPATIAL_VALIDATION",
        "raster": str(RASTER),
        "review_geopackage": str(REVIEW),
        "footprint_layer": footprint_output,
        "ring_layer": rings_output,
        "buildings": results,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("\nLoad diagnostic layers into QGIS from:", OUTPUT)
    print("Report:", report_path)
    print("No original data modified.")


if __name__ == "__main__":
    main()
