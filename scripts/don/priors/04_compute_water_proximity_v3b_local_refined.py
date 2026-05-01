from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box
from shapely.strtree import STRtree


CITY = "DON"
TARGET_CRS = "EPSG:25830"

BUILDINGS_PATH = Path("processed") / CITY / "derived" / "buildings_don.gpkg"
BASE_HYDRO_PATH = Path("processed") / CITY / "derived" / "hydrography_don.gpkg"
COAST_PATH = Path("processed") / CITY / "derived" / "coastline_ne.gpkg"
OSM_GPKG_PATH = Path("raw") / CITY / "buildings" / "pais_vasco.gpkg"

V3_PATH = Path("processed") / CITY / "priors" / "building_water_proximity_v3.parquet"

OUT_PATH = (
    Path("processed")
    / CITY
    / "priors"
    / "building_water_proximity_v3b_local_refined.parquet"
)

SUMMARY_PATH = (
    Path("processed")
    / CITY
    / "priors"
    / "building_water_proximity_v3b_local_refined_summary.json"
)

WATERWAY_LAYER = "gis_osm_waterways_free"
WATER_POLYGON_LAYER = "gis_osm_water_a_free"

# Important: exclude stream/drain.
# Otherwise every tiny wet line becomes equal to the ocean. Brilliant, but wrong.
OSM_WATERWAY_CLASSES = {"river", "canal"}

# Keep only structural water polygons.
OSM_WATER_POLYGON_CLASSES = {"riverbank", "water", "reservoir"}

BUILDING_EXTENT_BUFFER_M = 5_000


def clean_gdf(gdf: gpd.GeoDataFrame, label: str) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()

    try:
        gdf["geometry"] = gdf.geometry.make_valid()
    except Exception:
        gdf["geometry"] = gdf.geometry.buffer(0)

    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()
    print(f"[clean] {label}: {len(gdf):,} geometries")
    return gdf


def ensure_crs(
    gdf: gpd.GeoDataFrame,
    target_crs: str,
    label: str,
) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        raise ValueError(f"{label} has no CRS")

    if str(gdf.crs) != target_crs:
        gdf = gdf.to_crs(target_crs)

    return gdf


def to_line_reference(
    gdf: gpd.GeoDataFrame,
    label: str,
) -> gpd.GeoDataFrame:
    """
    Convert geometry to line references.

    - Lines stay lines.
    - Polygons become boundaries.
    - Points are dropped.
    """
    gdf = clean_gdf(gdf, label).copy()

    line_mask = gdf.geometry.geom_type.isin(["LineString", "MultiLineString"])
    poly_mask = gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])

    line_part = gdf.loc[line_mask].copy()

    poly_part = gdf.loc[poly_mask].copy()
    if not poly_part.empty:
        poly_part["geometry"] = poly_part.geometry.boundary

    out = pd.concat([line_part, poly_part], ignore_index=True)
    out = gpd.GeoDataFrame(out, geometry="geometry", crs=gdf.crs)
    out = clean_gdf(out, f"{label} line-reference")

    if out.empty:
        raise ValueError(f"{label} produced no line-reference geometries")

    return out


def load_buildings() -> gpd.GeoDataFrame:
    print(f"[load] buildings: {BUILDINGS_PATH}")
    gdf = gpd.read_file(BUILDINGS_PATH)
    gdf = ensure_crs(gdf, TARGET_CRS, "buildings")
    gdf = clean_gdf(gdf, "buildings")

    if "bldg_id" not in gdf.columns:
        raise KeyError("buildings missing bldg_id")

    return gdf


def clip_to_building_extent(
    gdf: gpd.GeoDataFrame,
    buildings: gpd.GeoDataFrame,
    label: str,
    buffer_m: float = BUILDING_EXTENT_BUFFER_M,
) -> gpd.GeoDataFrame:
    minx, miny, maxx, maxy = buildings.total_bounds

    bbox_geom = box(
        minx - buffer_m,
        miny - buffer_m,
        maxx + buffer_m,
        maxy + buffer_m,
    )

    bbox = gpd.GeoDataFrame(geometry=[bbox_geom], crs=TARGET_CRS)

    try:
        clipped = gpd.clip(gdf, bbox)
    except Exception:
        clipped = gdf.cx[
            minx - buffer_m : maxx + buffer_m,
            miny - buffer_m : maxy + buffer_m,
        ].copy()

    clipped = clean_gdf(clipped, f"{label} clipped to building extent")
    return clipped


def load_base_hydrography() -> gpd.GeoDataFrame:
    print(f"[load] base hydrography: {BASE_HYDRO_PATH}")
    gdf = gpd.read_file(BASE_HYDRO_PATH)
    gdf = ensure_crs(gdf, TARGET_CRS, "base hydrography")
    gdf["water_source"] = "hydrography_don"
    return to_line_reference(gdf, "base hydrography")


def load_osm_waterways(buildings: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    print(f"[load] OSM waterways: {OSM_GPKG_PATH}::{WATERWAY_LAYER}")
    gdf = gpd.read_file(OSM_GPKG_PATH, layer=WATERWAY_LAYER)
    gdf = ensure_crs(gdf, TARGET_CRS, "OSM waterways")
    gdf = clean_gdf(gdf, "OSM waterways")

    if "fclass" not in gdf.columns:
        raise KeyError("OSM waterways missing fclass")

    print("[osm waterways] raw fclass counts:")
    print(gdf["fclass"].value_counts(dropna=False))

    gdf = gdf[gdf["fclass"].isin(OSM_WATERWAY_CLASSES)].copy()

    print("[osm waterways] filtered fclass counts:")
    print(gdf["fclass"].value_counts(dropna=False))

    gdf = clip_to_building_extent(
        gdf=gdf,
        buildings=buildings,
        label="OSM waterways",
    )

    gdf["water_source"] = "osm_waterways_filtered_river_canal"

    return to_line_reference(gdf, "OSM waterways filtered")


def load_osm_water_polygon_boundaries(
    buildings: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    print(f"[load] OSM water polygons: {OSM_GPKG_PATH}::{WATER_POLYGON_LAYER}")
    gdf = gpd.read_file(OSM_GPKG_PATH, layer=WATER_POLYGON_LAYER)
    gdf = ensure_crs(gdf, TARGET_CRS, "OSM water polygons")
    gdf = clean_gdf(gdf, "OSM water polygons")

    if "fclass" not in gdf.columns:
        raise KeyError("OSM water polygons missing fclass")

    print("[osm water polygons] raw fclass counts:")
    print(gdf["fclass"].value_counts(dropna=False))

    gdf = gdf[gdf["fclass"].isin(OSM_WATER_POLYGON_CLASSES)].copy()

    gdf = clip_to_building_extent(
        gdf=gdf,
        buildings=buildings,
        label="OSM water polygons",
    )

    print("[osm water polygons] filtered/clipped fclass counts:")
    print(gdf["fclass"].value_counts(dropna=False))

    gdf["water_source"] = "osm_water_a_free_filtered_boundary"

    return to_line_reference(gdf, "OSM water polygon boundaries filtered")


def load_coastline() -> gpd.GeoDataFrame:
    print(f"[load] coastline: {COAST_PATH}")
    gdf = gpd.read_file(COAST_PATH)
    gdf = ensure_crs(gdf, TARGET_CRS, "Natural Earth coastline")
    gdf["water_source"] = "natural_earth_coastline"
    return to_line_reference(gdf, "Natural Earth coastline")


def compute_nearest_distance(
    buildings: gpd.GeoDataFrame,
    targets: gpd.GeoDataFrame,
    label: str,
) -> np.ndarray:
    targets = clean_gdf(targets, label)
    target_geoms = list(targets.geometry.values)

    if not target_geoms:
        raise ValueError(f"No target geometries for {label}")

    tree = STRtree(target_geoms)
    distances = np.zeros(len(buildings), dtype=float)

    print(
        f"[distance] {label}: "
        f"buildings={len(buildings):,}, targets={len(target_geoms):,}"
    )

    for i, geom in enumerate(buildings.geometry.values):
        nearest = tree.nearest(geom)

        if isinstance(nearest, (int, np.integer)):
            nearest_geom = target_geoms[int(nearest)]
        else:
            nearest_geom = nearest

        distances[i] = geom.distance(nearest_geom)

        if (i + 1) % 10_000 == 0:
            print(f"[distance] {label}: {i + 1:,}/{len(buildings):,}")

    return distances


def write_summary(out: pd.DataFrame, source_counts: dict[str, int]) -> None:
    summary = {
        "city": CITY,
        "method": "v3b_local_refined_filtered",
        "description": (
            "DON local refinement using base hydrography, filtered OSM waterways "
            "(river/canal only), filtered OSM water polygon boundaries, and "
            "Natural Earth coastline. Streams and drains are excluded to avoid "
            "turning incidental water features into dominant exposure attractors."
        ),
        "n_buildings": int(len(out)),
        "source_counts": source_counts,
        "outputs": {
            "priors": str(OUT_PATH),
            "summary": str(SUMMARY_PATH),
        },
        "distance_summary": {
            col: {
                k: float(v)
                for k, v in out[col].describe().to_dict().items()
            }
            for col in [
                "dist_to_hydrography_m",
                "dist_to_osm_waterways_m",
                "dist_to_osm_water_polygons_m",
                "dist_to_coast_m",
                "dist_to_water_m",
            ]
        },
    }

    if V3_PATH.exists():
        old = pd.read_parquet(V3_PATH)[["bldg_id", "dist_to_water_m"]].rename(
            columns={"dist_to_water_m": "dist_to_water_m_v3"}
        )

        merged = out.merge(old, on="bldg_id", how="inner")
        delta = merged["dist_to_water_m"] - merged["dist_to_water_m_v3"]

        summary["comparison_to_v3"] = {
            "n_joined": int(len(merged)),
            "delta_m_describe": {
                k: float(v) for k, v in delta.describe().to_dict().items()
            },
            "share_reduced_by_more_than_10m": float((delta < -10).mean()),
            "share_reduced_by_more_than_50m": float((delta < -50).mean()),
            "share_reduced_by_more_than_100m": float((delta < -100).mean()),
            "share_increased_by_more_than_10m": float((delta > 10).mean()),
        }

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"[saved] summary: {SUMMARY_PATH}")


def main() -> None:
    print("[don-water-v3b-filtered] computing DON refined filtered water proximity")

    buildings = load_buildings()

    base_hydro = load_base_hydrography()
    osm_waterways = load_osm_waterways(buildings)
    osm_water_poly = load_osm_water_polygon_boundaries(buildings)
    coast = load_coastline()

    combined_inland = pd.concat(
        [base_hydro, osm_waterways, osm_water_poly],
        ignore_index=True,
    )
    combined_inland = gpd.GeoDataFrame(
        combined_inland,
        geometry="geometry",
        crs=TARGET_CRS,
    )
    combined_inland = clean_gdf(combined_inland, "combined inland water")

    combined_all = pd.concat(
        [combined_inland, coast],
        ignore_index=True,
    )
    combined_all = gpd.GeoDataFrame(
        combined_all,
        geometry="geometry",
        crs=TARGET_CRS,
    )
    combined_all = clean_gdf(combined_all, "combined all water")

    source_counts = {
        str(k): int(v)
        for k, v in combined_all["water_source"]
        .value_counts(dropna=False)
        .to_dict()
        .items()
    }

    print("[water sources]")
    print(combined_all["water_source"].value_counts(dropna=False))

    dist_hydro = compute_nearest_distance(
        buildings,
        base_hydro,
        "base hydrography",
    )
    dist_osm_waterways = compute_nearest_distance(
        buildings,
        osm_waterways,
        "filtered OSM waterways",
    )
    dist_osm_water_poly = compute_nearest_distance(
        buildings,
        osm_water_poly,
        "filtered OSM water polygon boundaries",
    )
    dist_coast = compute_nearest_distance(
        buildings,
        coast,
        "Natural Earth coastline",
    )
    dist_water = compute_nearest_distance(
        buildings,
        combined_all,
        "combined all water",
    )

    out = pd.DataFrame(
        {
            "bldg_id": buildings["bldg_id"].values,
            "dist_to_hydrography_m": dist_hydro,
            "dist_to_osm_waterways_m": dist_osm_waterways,
            "dist_to_osm_water_polygons_m": dist_osm_water_poly,
            "dist_to_coast_m": dist_coast,
            "dist_to_water_m": dist_water,
        }
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT_PATH, index=False)

    print(f"[saved] priors: {OUT_PATH}")
    print(out.describe())

    write_summary(out, source_counts=source_counts)

    print("[don-water-v3b-filtered] done")


if __name__ == "__main__":
    main()