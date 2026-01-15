from pathlib import Path
import geopandas as gpd

TARGET_CRS = "EPSG:28992"

RAW_GPKG = Path("raw/RTM/boundaries/rotterdam_municipality/cbsgebiedsindelingen2025.gpkg")
RAW_LAYER = "gemeente_niet_gegeneraliseerd"

OUT_GPKG = Path("processed/RTM/normalized/boundary_rtm.gpkg")
OUT_LAYER = "boundary"

TARGET_NAME = "Rotterdam"
NAME_COL = "statnaam"


def main() -> int:
    if not RAW_GPKG.exists():
        raise FileNotFoundError(f"Missing raw boundary file: {RAW_GPKG}")

    gdf = gpd.read_file(RAW_GPKG, layer=RAW_LAYER, engine="pyogrio")

    if gdf.crs is None:
        raise ValueError("Boundary CRS missing.")

    rtm = gdf[gdf[NAME_COL].astype(str).str.strip() == TARGET_NAME].copy()
    if rtm.empty:
        # Show a few example names to help debug
        examples = gdf[NAME_COL].astype(str).dropna().unique().tolist()[:30]
        raise ValueError(f"'{TARGET_NAME}' not found in '{NAME_COL}'. Examples: {examples}")

    rtm = rtm.to_crs(TARGET_CRS)

    # Dissolve to single geometry
    rtm["__one__"] = 1
    rtm = rtm.dissolve(by="__one__").drop(columns="__one__", errors="ignore")

    # Minimal attributes
    rtm["name"] = TARGET_NAME

    OUT_GPKG.parent.mkdir(parents=True, exist_ok=True)
    rtm.to_file(OUT_GPKG, layer=OUT_LAYER, driver="GPKG")

    print(f"Wrote boundary: {OUT_GPKG} (features: {len(rtm)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
