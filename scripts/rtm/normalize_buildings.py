from pathlib import Path
import geopandas as gpd


KEEP_COLS = [
    # core
    "geometry",
    # useful building attributes if present
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

    # Keep only columns that actually exist in the file
    keep = [c for c in KEEP_COLS if c in gdf.columns]
    gdf = gdf[keep]

    # Reproject to RD New (meters)
    gdf = gdf.to_crs("EPSG:28992")

    out.parent.mkdir(parents=True, exist_ok=True)
    # Name the layer explicitly
    gdf.to_file(out, driver="GPKG", layer="buildings", engine="pyogrio")

    print(f"Wrote {len(gdf)} buildings (cols={len(gdf.columns)}) → {out}")


if __name__ == "__main__":
    main()
