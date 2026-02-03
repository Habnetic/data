from pathlib import Path
import geopandas as gpd

ID_CANDIDATES = ["@id", "id", "osm_id", "osmid", "osm_way_id", "way_id"]  # removed "fid"

KEEP_COLS = [
    "geometry",
    "building",
    "building:levels",
    "building:height",
    "height",
    "building:material",
    "roof:shape",
    "roof:material",
    "roof:height",
    "roof:levels",
    "name",
    "addr:postcode",
]

def main():
    src = Path("raw/RTM/buildings/osm/buildings_zuid_holland.geojson")
    out = Path("processed/RTM/normalized/buildings.gpkg")

    gdf = gpd.read_file(src, engine="pyogrio")

    id_col = next((c for c in ID_CANDIDATES if c in gdf.columns), None)

    keep = []
    if id_col is not None:
        keep.append(id_col)
    keep += [c for c in KEEP_COLS if c in gdf.columns]
    gdf = gdf[keep].copy()

    gdf = gdf.to_crs("EPSG:28992")

    # Deterministic stable ID (do NOT name it fid)
    c = gdf.geometry.centroid
    gdf = gdf.assign(_cx=c.x, _cy=c.y, _area=gdf.geometry.area)
    gdf = gdf.sort_values(by=["_cx", "_cy", "_area"]).drop(columns=["_cx", "_cy", "_area"])
    gdf = gdf.reset_index(drop=True)

    gdf["bldg_id"] = (gdf.index + 1).astype("int64")

    out.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out, driver="GPKG", layer="buildings", engine="pyogrio", mode="w")

    print(f"Wrote {len(gdf)} buildings (cols={len(gdf.columns)}) → {out}")
    if id_col:
        print(f"Preserved source id column: {id_col}")
    else:
        print("No source id column found; using generated bldg_id only.")

if __name__ == "__main__":
    main()
