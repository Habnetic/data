from pathlib import Path
import geopandas as gpd

TARGET_CRS = "EPSG:25830"

RAW_GPKG = Path("raw/DON/boundaries/gipuzkoa_municipal_boundaries.gpkg")

OUT_GPKG = Path("processed/DON/normalized/boundary_don.gpkg")
OUT_LAYER = "boundary"

TARGET_CODE = "20069"
CODE_COL = "CODMUNIINE"
TARGET_NAME = "Donostia / San Sebastián"


def main() -> int:
    if not RAW_GPKG.exists():
        raise FileNotFoundError(f"Missing raw boundary file: {RAW_GPKG}")

    gdf = gpd.read_file(RAW_GPKG, engine="pyogrio")

    if gdf.crs is None:
        raise ValueError("Boundary CRS missing.")

    don = gdf[gdf[CODE_COL].astype(str).str.strip() == TARGET_CODE].copy()
    if don.empty:
        examples = gdf[CODE_COL].astype(str).dropna().unique().tolist()[:30]
        raise ValueError(f"'{TARGET_CODE}' not found in '{CODE_COL}'. Examples: {examples}")

    don = don.to_crs(TARGET_CRS)

    # Dissolve to single geometry
    don["__one__"] = 1
    don = don.dissolve(by="__one__").reset_index(drop=True)

    # Keep only clean minimal output schema
    don = don[["geometry"]].copy()
    don["name"] = TARGET_NAME
    don["codmuniine"] = TARGET_CODE

    OUT_GPKG.parent.mkdir(parents=True, exist_ok=True)
    don.to_file(OUT_GPKG, layer=OUT_LAYER, driver="GPKG", engine="pyogrio", mode="w")

    print(f"Wrote boundary: {OUT_GPKG} (features: {len(don)})")
    print(f"Bounds: {don.total_bounds}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())