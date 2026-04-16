from pathlib import Path
import geopandas as gpd

TARGET_CRS = "EPSG:25832"

RAW_GPKG = Path("raw/HAM/buildings/hamburg.gpkg")
RAW_LAYER = "gis_osm_buildings_a_free"

OUT_GPKG = Path("processed/HAM/normalized/buildings.gpkg")
OUT_LAYER = "buildings"

ID_CANDIDATES = ["osm_id", "@id", "id", "osmid", "osm_way_id", "way_id"]

KEEP_COLS = [
    "geometry",
    "osm_id",
    "code",
    "fclass",
    "name",
    "type",
]


def main() -> int:
    if not RAW_GPKG.exists():
        raise FileNotFoundError(f"Missing raw buildings file: {RAW_GPKG}")

    gdf = gpd.read_file(RAW_GPKG, layer=RAW_LAYER, engine="pyogrio")

    if gdf.empty:
        raise ValueError("Buildings layer is empty.")

    if gdf.crs is None:
        raise ValueError("Buildings CRS missing.")

    id_col = next((c for c in ID_CANDIDATES if c in gdf.columns), None)

    keep = []
    if id_col is not None and id_col not in keep:
        keep.append(id_col)
    keep += [c for c in KEEP_COLS if c in gdf.columns and c not in keep]

    gdf = gdf[keep].copy()

    # Keep only polygonal building geometries
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()

    if gdf.empty:
        raise ValueError("No polygonal building geometries remain after filtering.")

    # Reproject to Hamburg working CRS
    gdf = gdf.to_crs(TARGET_CRS)

    # Basic geometry cleanup
    gdf = gdf[gdf.geometry.notna()].copy()
    gdf["geometry"] = gdf.geometry.make_valid()
    gdf = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    gdf = gdf[~gdf.geometry.is_empty].copy()
    gdf = gdf[~gdf.geometry.is_empty].copy()

    if gdf.empty:
        raise ValueError("No valid building geometries remain after cleanup.")

    # Deterministic stable ID (same logic as RTM, do NOT call it fid)
    c = gdf.geometry.centroid
    gdf = gdf.assign(_cx=c.x, _cy=c.y, _area=gdf.geometry.area)
    gdf = gdf.sort_values(by=["_cx", "_cy", "_area"]).drop(columns=["_cx", "_cy", "_area"])
    gdf = gdf.reset_index(drop=True)

    gdf["bldg_id"] = (gdf.index + 1).astype("int64")

    OUT_GPKG.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(OUT_GPKG, layer=OUT_LAYER, driver="GPKG", engine="pyogrio", mode="w")

    print(f"Wrote {len(gdf)} buildings (cols={len(gdf.columns)}) → {OUT_GPKG}")
    print(f"CRS: {gdf.crs}")
    if id_col:
        print(f"Preserved source id column: {id_col}")
    else:
        print("No source id column found; using generated bldg_id only.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())