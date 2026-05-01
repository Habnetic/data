from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.strtree import STRtree


TARGET_CRS = "EPSG:25830"

BUILDINGS_PATH = Path("processed") / "DON" / "derived" / "buildings_don.gpkg"
HYDROGRAPHY_PATH = Path("processed") / "DON" / "derived" / "hydrography_don.gpkg"
COASTAL_PROXY_PATH = Path("processed") / "DON" / "derived" / "coastal_proxy_don.gpkg"

OLD_PRIORS_PATH = (
    Path("processed") / "DON" / "priors" / "building_water_proximity.parquet"
)

OUT_DIR = Path("processed") / "DON" / "priors"
OUT_PATH = OUT_DIR / "building_water_proximity_v2_coast.parquet"
SUMMARY_PATH = OUT_DIR / "building_water_proximity_v2_coast_summary.json"

BUFFER_RADII_M = [250, 500, 1000]


def load_layer(path: Path, label: str) -> gpd.GeoDataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")

    gdf = gpd.read_file(path)

    if gdf.empty:
        raise ValueError(f"{label} is empty: {path}")

    if gdf.crs is None:
        raise ValueError(f"{label} has no CRS: {path}")

    gdf = gdf.to_crs(TARGET_CRS)
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()].copy()

    if gdf.empty:
        raise ValueError(f"{label} has no valid geometries after cleanup: {path}")

    print(f"[load] {label}: {len(gdf):,} features | CRS={gdf.crs}")
    return gdf


def explode_to_geometries(gdf: gpd.GeoDataFrame) -> list:
    """Return valid individual geometries for STRtree."""
    exploded = gdf.explode(index_parts=False).reset_index(drop=True)
    geoms = [geom for geom in exploded.geometry.values if geom is not None and not geom.is_empty]

    if not geoms:
        raise ValueError("No valid geometries found after explode.")

    return geoms


def nearest_distances(building_geoms: list, target_geoms: list, label: str) -> np.ndarray:
    """
    Compute nearest distances from buildings to target geometries.

    Compatible with Shapely versions where STRtree.nearest returns either
    a geometry or an integer index.
    """
    print(f"[distance] building count={len(building_geoms):,}")
    print(f"[distance] target count for {label}={len(target_geoms):,}")

    tree = STRtree(target_geoms)

    distances = np.empty(len(building_geoms), dtype="float64")

    for i, geom in enumerate(building_geoms):
        nearest = tree.nearest(geom)

        # Shapely 2 may return an integer index instead of the geometry itself.
        if isinstance(nearest, (int, np.integer)):
            nearest_geom = target_geoms[int(nearest)]
        else:
            nearest_geom = nearest

        distances[i] = geom.distance(nearest_geom)

        if (i + 1) % 25_000 == 0:
            print(f"[distance] {label}: processed {i + 1:,}/{len(building_geoms):,}")

    return distances


def water_length_density(
    buildings: gpd.GeoDataFrame,
    water_lines: gpd.GeoDataFrame,
    radius_m: int,
) -> np.ndarray:
    """
    Compute water geometry length inside a buffer around each building centroid.

    Compatible with Shapely versions where STRtree.query returns either
    geometries or integer indices.
    """
    print(f"[density] radius={radius_m}m")

    water_geoms = explode_to_geometries(water_lines)
    tree = STRtree(water_geoms)

    centroids = buildings.geometry.centroid
    out = np.empty(len(buildings), dtype="float64")

    for i, centroid in enumerate(centroids):
        buffer = centroid.buffer(radius_m)
        candidates = tree.query(buffer)

        if len(candidates) == 0:
            out[i] = 0.0
        else:
            length = 0.0

            for candidate in candidates:
                if isinstance(candidate, (int, np.integer)):
                    geom = water_geoms[int(candidate)]
                else:
                    geom = candidate

                inter = geom.intersection(buffer)
                if not inter.is_empty:
                    length += inter.length

            area = np.pi * radius_m**2
            out[i] = length / area

        if (i + 1) % 25_000 == 0:
            print(f"[density] r={radius_m}: processed {i + 1:,}/{len(buildings):,}")

    return out


def build_combined_water_lines(
    hydrography: gpd.GeoDataFrame,
    coastal_proxy: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """
    Build one line-like water reference.

    - hydrography geometries are already line-like
    - coastal proxy polygons are converted to boundaries
    """
    hydro = hydrography.copy()
    hydro["water_source"] = "hydrography_don"

    coast = coastal_proxy.copy()
    coast["geometry"] = coast.geometry.boundary
    coast["water_source"] = "coastal_proxy_don"

    keep_cols = ["water_source", "geometry"]

    combined = pd.concat(
        [
            hydro[keep_cols],
            coast[keep_cols],
        ],
        ignore_index=True,
    )

    combined = gpd.GeoDataFrame(combined, geometry="geometry", crs=TARGET_CRS)
    combined = combined[~combined.geometry.is_empty & combined.geometry.notna()].copy()

    if combined.empty:
        raise ValueError("Combined water reference is empty.")

    print(f"[water] combined line-like water features: {len(combined):,}")
    print(combined["water_source"].value_counts())

    return combined


def summarize_distances(df: pd.DataFrame) -> dict:
    summary: dict = {}

    for col in [
        "dist_to_hydrography_m",
        "dist_to_coast_m",
        "dist_to_water_m",
    ]:
        values = df[col].dropna()
        summary[col] = {
            "min": float(values.min()),
            "p01": float(values.quantile(0.01)),
            "p05": float(values.quantile(0.05)),
            "p10": float(values.quantile(0.10)),
            "p50": float(values.quantile(0.50)),
            "p90": float(values.quantile(0.90)),
            "p95": float(values.quantile(0.95)),
            "p99": float(values.quantile(0.99)),
            "max": float(values.max()),
            "mean": float(values.mean()),
        }

    return summary


def compare_with_old(new_df: pd.DataFrame) -> None:
    if not OLD_PRIORS_PATH.exists():
        print(f"[compare] old priors not found, skipping: {OLD_PRIORS_PATH}")
        return

    old = pd.read_parquet(OLD_PRIORS_PATH)

    if "bldg_id" not in old.columns or "dist_to_water_m" not in old.columns:
        print("[compare] old priors missing required columns, skipping")
        return

    comp = old[["bldg_id", "dist_to_water_m"]].merge(
        new_df[["bldg_id", "dist_to_water_m"]],
        on="bldg_id",
        suffixes=("_old", "_v2"),
        how="inner",
    )

    comp["delta_m"] = comp["dist_to_water_m_v2"] - comp["dist_to_water_m_old"]

    print("\n[compare] old vs v2 distance_to_water_m")
    print(comp[["dist_to_water_m_old", "dist_to_water_m_v2", "delta_m"]].describe())

    print("\n[compare] share reduced by >10m:")
    print(float((comp["delta_m"] < -10).mean()))

    print("\n[compare] share reduced by >100m:")
    print(float((comp["delta_m"] < -100).mean()))


def main() -> None:
    print("[don-water-v2] computing DON water proximity with coastal proxy")

    buildings = load_layer(BUILDINGS_PATH, "DON buildings")
    hydrography = load_layer(HYDROGRAPHY_PATH, "DON hydrography")
    coastal_proxy = load_layer(COASTAL_PROXY_PATH, "DON coastal proxy")

    if "bldg_id" not in buildings.columns:
        raise KeyError(f"Buildings missing bldg_id: {BUILDINGS_PATH}")

    buildings = buildings[["bldg_id", "geometry"]].copy()
    buildings = buildings.drop_duplicates(subset=["bldg_id"]).reset_index(drop=True)

    water_lines = build_combined_water_lines(hydrography, coastal_proxy)

    building_geoms = list(buildings.geometry.values)

    hydro_geoms = explode_to_geometries(hydrography)
    coast_geoms = explode_to_geometries(coastal_proxy)

    dist_hydro = nearest_distances(
        building_geoms=building_geoms,
        target_geoms=hydro_geoms,
        label="hydrography",
    )

    dist_coast = nearest_distances(
        building_geoms=building_geoms,
        target_geoms=coast_geoms,
        label="coastal_proxy",
    )

    dist_water = np.minimum(dist_hydro, dist_coast)

    out = pd.DataFrame(
        {
            "bldg_id": buildings["bldg_id"].to_numpy(),
            "dist_to_hydrography_m": dist_hydro,
            "dist_to_coast_m": dist_coast,
            "dist_to_water_m": dist_water,
        }
    )

    for radius in BUFFER_RADII_M:
        col = f"water_len_density_{radius}m"
        out[col] = water_length_density(
            buildings=buildings,
            water_lines=water_lines,
            radius_m=radius,
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT_PATH, index=False)

    summary = {
        "city": "DON",
        "version": "v2_coast",
        "n_buildings": int(len(out)),
        "target_crs": TARGET_CRS,
        "inputs": {
            "buildings": str(BUILDINGS_PATH),
            "hydrography": str(HYDROGRAPHY_PATH),
            "coastal_proxy": str(COASTAL_PROXY_PATH),
        },
        "outputs": {
            "priors": str(OUT_PATH),
        },
        "distance_summary": summarize_distances(out),
        "note": (
            "dist_to_water_m is min(distance to inland hydrography, "
            "distance to coastal proxy). Coastal proxy is derived from "
            "OSM natural polygons with fclass beach/cliff."
        ),
    }

    pd.Series(summary).to_json(SUMMARY_PATH, indent=2)

    print(f"\n[don-water-v2] saved priors: {OUT_PATH}")
    print(f"[don-water-v2] saved summary: {SUMMARY_PATH}")

    compare_with_old(out)

    print("[don-water-v2] done")


if __name__ == "__main__":
    main()