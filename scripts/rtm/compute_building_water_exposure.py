#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.strtree import STRtree


def read_gpkg(path: Path) -> gpd.GeoDataFrame:
    gdf = gpd.read_file(path, engine="pyogrio")
    if gdf.crs is None:
        raise ValueError(f"{path} has no CRS. Expected EPSG:28992.")
    return gdf


def ensure_crs(gdf: gpd.GeoDataFrame, epsg: int = 28992) -> gpd.GeoDataFrame:
    if gdf.crs.to_epsg() != epsg:
        gdf = gdf.to_crs(epsg)
    return gdf


def safe_representative_points(polys: gpd.GeoSeries) -> gpd.GeoSeries:
    return polys.representative_point()


def compute_nearest_water_distance_m(
    building_points: gpd.GeoSeries,
    water_lines: gpd.GeoSeries,
) -> np.ndarray:
    geoms = [g for g in water_lines.values if g and not g.is_empty]
    tree = STRtree(geoms)

    out = np.full(len(building_points), np.nan, dtype="float64")

    for i, pt in enumerate(building_points.values):
        if pt is None or pt.is_empty:
            continue

        if hasattr(tree, "query_nearest"):
            _, dist = tree.query_nearest(pt, return_distance=True)
            if np.ndim(dist) > 0:
                dist = dist[0]
            out[i] = float(dist)
        else:
            out[i] = pt.distance(tree.nearest(pt))

    return out


def compute_water_length_density(
    buildings: gpd.GeoDataFrame,
    water: gpd.GeoDataFrame,
    radius_m: float,
    chunk_size: int = 25_000,
) -> pd.Series:
    buffer_area = np.pi * radius_m**2
    out = pd.Series(0.0, index=buildings.index, dtype="float64")

    for start in range(0, len(buildings), chunk_size):
        end = min(start + chunk_size, len(buildings))
        chunk = buildings.iloc[start:end].copy()

        chunk["geometry"] = chunk["rep_pt"].buffer(radius_m)

        pairs = gpd.sjoin(
            chunk[["geometry"]],
            water[["geometry"]],
            how="left",
            predicate="intersects",
        ).dropna(subset=["index_right"])

        if pairs.empty:
            continue

        pairs["index_right"] = pairs["index_right"].astype(int)

        left = chunk.loc[pairs.index].geometry
        right = water.loc[pairs["index_right"]].geometry.values

        inter_len = left.values.intersection(right).length

        tmp = (
            pd.DataFrame({"bldg_idx": pairs.index, "len_m": inter_len})
            .groupby("bldg_idx")["len_m"]
            .sum()
        )

        out.loc[tmp.index] = tmp.values / buffer_area

    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--buildings", type=Path, required=True)
    ap.add_argument("--water", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--chunk-size", type=int, default=25_000)
    args = ap.parse_args()

    buildings = ensure_crs(read_gpkg(args.buildings))
    water = ensure_crs(read_gpkg(args.water))

    if "bldg_id" not in buildings.columns:
        raise ValueError("Missing bldg_id in buildings input.")

    buildings = buildings[~buildings.geometry.is_empty & buildings.geometry.notna()].copy()
    water = water[~water.geometry.is_empty & water.geometry.notna()].copy()

    if args.sample and args.sample > 0:
        buildings = buildings.sample(args.sample, random_state=42).copy()

    buildings["rep_pt"] = safe_representative_points(buildings.geometry)

    buildings["dist_to_water_m"] = compute_nearest_water_distance_m(
        buildings["rep_pt"], water.geometry
    )

    for r in (250, 500, 1000):
        buildings[f"water_len_density_{r}m"] = compute_water_length_density(
            buildings, water, float(r), args.chunk_size
        ).values

    # FINAL OUTPUT: attributes only + stable ID
    out = buildings.drop(columns=["geometry", "rep_pt"], errors="ignore").copy()

    # Final sanity
    if "bldg_id" not in out.columns:
        raise RuntimeError("bldg_id disappeared before output.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(args.out, index=False)

    print("Saved:", args.out)
    print(out["dist_to_water_m"].describe(percentiles=[0.1, 0.5, 0.9]).to_string())


if __name__ == "__main__":
    main()
