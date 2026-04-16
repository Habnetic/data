from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd

TARGET_CRS = "EPSG:25830"


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

    # Keep line geometries
    gdf = gdf[gdf.geometry.type.isin(["LineString", "MultiLineString"])].copy()

    # Standardize fields
    rename_map = {}
    for cand in ["naam", "name", "NAME"]:
        if cand in gdf.columns:
            rename_map[cand] = "name"
            break

    for cand in ["type", "water_type", "WATER_TYPE", "categorie", "category", "SUBTYPE_EU", "SUBTYPE_ES"]:
        if cand in gdf.columns:
            rename_map[cand] = "water_type"
            break

    if rename_map:
        gdf = gdf.rename(columns=rename_map)

    gdf["source"] = "gipuzkoa_hydrography"

    # Stable-ish id for downstream work
    if "B5MCODE" in gdf.columns:
        gdf["water_id"] = gdf["B5MCODE"].astype(str)
    elif "gid" in gdf.columns:
        gdf["water_id"] = gdf["gid"].astype(str)
    elif "gml_id" in gdf.columns:
        gdf["water_id"] = gdf["gml_id"].astype(str)
    else:
        gdf["water_id"] = gdf.index.astype(str)

    # Optional clip to Donostia boundary
    if paths.boundary_gpkg and paths.boundary_gpkg.exists():
        boundary = load_boundary(paths)
        gdf = gpd.clip(gdf, boundary)

    keep_cols = [c for c in ["water_id", "source", "water_type", "name", "geometry"] if c in gdf.columns]
    gdf = gdf[keep_cols].copy()

    return gdf


def main() -> int:
    raw_gpkg = Path("raw/DON/hazards/hydrography/gipuzkoa_rivers_streams.gpkg")
    out_gpkg = Path("processed/DON/normalized/hydrography.gpkg")

    paths = Paths(
        raw_gpkg=raw_gpkg,
        out_gpkg=out_gpkg,
        boundary_gpkg=None,
        boundary_layer=None,
        raw_layer="GFA_DSET_HYD",
    )

    if not raw_gpkg.exists():
        print(f"\nRaw file missing: {raw_gpkg}")
        print("Put the Gipuzkoa hydrography GeoPackage there (or edit the path in the script).")
        return 2

    gdf = normalize_hydrography(paths)

    out_gpkg.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_gpkg, layer="hydrography", driver="GPKG", engine="pyogrio", mode="w")

    print(f"Wrote: {out_gpkg} (features: {len(gdf)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())