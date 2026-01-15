from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

import geopandas as gpd

TARGET_CRS = "EPSG:28992"


@dataclass(frozen=True)
class Paths:
    raw_gpkg: Path
    out_gpkg: Path
    boundary_gpkg: Path | None = None
    boundary_layer: str | None = None
    raw_layer: str | None = None  # set if your GPKG has multiple layers


def list_layers(gpkg_path: Path) -> list[str]:
    try:
        import fiona  # type: ignore
    except ImportError as e:
        raise RuntimeError("Missing dependency 'fiona'. Install geopandas with fiona support.") from e
    return list(fiona.listlayers(gpkg_path))


def load_boundary(paths: Paths) -> gpd.GeoDataFrame:
    if paths.boundary_gpkg is None:
        raise ValueError("boundary_gpkg is None")
    b = gpd.read_file(paths.boundary_gpkg, layer=paths.boundary_layer)
    if b.crs is None:
        raise ValueError("Boundary CRS missing.")
    return b.to_crs(TARGET_CRS)


def normalize_hydrography(paths: Paths) -> gpd.GeoDataFrame:
    if not paths.raw_gpkg.exists():
        raise FileNotFoundError(f"Raw hydrography file not found: {paths.raw_gpkg}")

    gdf = gpd.read_file(paths.raw_gpkg, layer=paths.raw_layer, engine="pyogrio")

    if gdf.crs is None:
        raise ValueError("Raw hydrography CRS missing. Fix before proceeding.")

    gdf = gdf.to_crs(TARGET_CRS)

    # Keep line geometries (river/canal networks are usually lines)
    gdf = gdf[gdf.geometry.type.isin(["LineString", "MultiLineString"])].copy()

    # Standardize fields: these may differ by dataset/layer, so we do best-effort.
    rename_map = {}
    for cand in ["naam", "name", "NAME"]:
        if cand in gdf.columns:
            rename_map[cand] = "name"
            break

    for cand in ["type", "water_type", "WATER_TYPE", "categorie", "category"]:
        if cand in gdf.columns:
            rename_map[cand] = "water_type"
            break

    if rename_map:
        gdf = gdf.rename(columns=rename_map)

    gdf["source"] = "pdok_topnl"

    # A stable-ish id for downstream joins (replace later with a better id if provided)
    gdf["water_id"] = gdf.index.astype(str)

    # Optional clip to Rotterdam boundary
    if paths.boundary_gpkg and paths.boundary_gpkg.exists():
        boundary = load_boundary(paths)
        gdf = gpd.clip(gdf, boundary)

    # Minimal column set (keep extras if you want; being strict keeps outputs stable)
    keep_cols = [c for c in ["water_id", "source", "water_type", "name", "geometry"] if c in gdf.columns]
    gdf = gdf[keep_cols].copy()

    return gdf


def main() -> int:
    raw_gpkg = Path("raw/RTM/hazards/hydrography/downloads/hydrography.gpkg")
    out_gpkg = Path("processed/RTM/normalized/hydrography.gpkg")

    paths = Paths(
        raw_gpkg=raw_gpkg,
        out_gpkg=out_gpkg,
        boundary_gpkg=None,         # set later, e.g. Path("raw/RTM/boundaries/rotterdam.gpkg")
        boundary_layer=None,
        raw_layer="top50nl_waterdeel_lijn",             # if needed, set to a layer name
    )

    if not raw_gpkg.exists():
        print(f"\nRaw file missing: {raw_gpkg}")
        print("Put the PDOK TOPNL hydrography GeoPackage there (or edit the path in the script).")
        return 2

    # If multi-layer and you’re unsure, print layers:
    # print(list_layers(raw_gpkg))

    gdf = normalize_hydrography(paths)

    out_gpkg.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_gpkg, layer="hydrography", driver="GPKG")

    print(f"Wrote: {out_gpkg} (features: {len(gdf)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
