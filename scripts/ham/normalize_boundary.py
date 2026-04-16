from pathlib import Path
import geopandas as gpd

TARGET_CRS = "EPSG:25832"

RAW_GML = Path("raw/HAM/boundaries/alkis_verwaltungsgrenzen_hamburg.gml")

OUT_GPKG = Path("processed/HAM/normalized/boundary_ham.gpkg")
OUT_LAYER = "boundary"

TARGET_NAME = "Hamburg"


def main() -> int:
    if not RAW_GML.exists():
        raise FileNotFoundError(f"Missing raw boundary file: {RAW_GML}")

    gdf = gpd.read_file(RAW_GML, engine="pyogrio")

    if gdf.crs is None:
        gdf = gdf.set_crs(TARGET_CRS)

    if len(gdf) != 1:
        raise ValueError(f"Expected exactly 1 boundary feature, got {len(gdf)}")

    ham = gdf.copy()
    ham = ham.to_crs(TARGET_CRS)

    # Dissolve to single geometry
    ham["__one__"] = 1
    ham = ham.dissolve(by="__one__", as_index=False).drop(columns="__one__", errors="ignore")

    # Minimal attributes
    ham["name"] = TARGET_NAME

    OUT_GPKG.parent.mkdir(parents=True, exist_ok=True)
    ham.to_file(OUT_GPKG, layer=OUT_LAYER, driver="GPKG")

    print(f"Wrote boundary: {OUT_GPKG} (features: {len(ham)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())