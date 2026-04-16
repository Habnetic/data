from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd

TARGET_CRS = "EPSG:25832"


@dataclass(frozen=True)
class Paths:
    raw_file: Path
    out_gpkg: Path
    raw_layer: str | None = None  # if needed later


def normalize_hydrography(paths: Paths) -> gpd.GeoDataFrame:
    if not paths.raw_file.exists():
        raise FileNotFoundError(f"Raw hydrography file not found: {paths.raw_file}")

    gdf = gpd.read_file(paths.raw_file, layer=paths.raw_layer, engine="pyogrio")

    if gdf.crs is None:
        raise ValueError("Raw hydrography CRS missing. Fix before proceeding.")

    # Reproject to Hamburg working CRS
    gdf = gdf.to_crs(TARGET_CRS)

    # Keep line geometries only
    gdf = gdf[gdf.geometry.type.isin(["LineString", "MultiLineString"])].copy()

    if gdf.empty:
        raise ValueError("No line geometries found in raw hydrography dataset.")

    # Standardize fields where possible
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

    gdf["source"] = "basis_gewaessernetz_hamburg"

    # Stable downstream identifier
    if "gid" in gdf.columns:
        gdf["water_id"] = gdf["gid"].astype(str)
    elif "gml_id" in gdf.columns:
        gdf["water_id"] = gdf["gml_id"].astype(str)
    else:
        gdf["water_id"] = gdf.index.astype(str)

    # Minimal stable schema
    keep_cols = [c for c in ["water_id", "source", "water_type", "name", "geometry"] if c in gdf.columns]
    gdf = gdf[keep_cols].copy()

    return gdf


def main() -> int:
    raw_file = Path("raw/HAM/hazards/hydrography/basis_gewaessernetz_hamburg.xml")
    out_gpkg = Path("processed/HAM/normalized/hydrography.gpkg")

    paths = Paths(
        raw_file=raw_file,
        out_gpkg=out_gpkg,
        raw_layer=None,
    )

    if not raw_file.exists():
        print(f"\nRaw file missing: {raw_file}")
        print("Put the Hamburg hydrography XML there (or edit the path in the script).")
        return 2

    gdf = normalize_hydrography(paths)

    out_gpkg.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out_gpkg, layer="hydrography", driver="GPKG", engine="pyogrio")

    print(f"Wrote: {out_gpkg} (features: {len(gdf)})")
    print(f"CRS: {gdf.crs}")
    print(f"Columns: {list(gdf.columns)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())