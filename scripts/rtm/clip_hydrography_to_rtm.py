from pathlib import Path
import geopandas as gpd

TARGET_CRS = "EPSG:28992"

HYDRO_IN = Path("processed/RTM/normalized/hydrography.gpkg")
HYDRO_LAYER = "hydrography"

BOUNDARY_IN = Path("processed/RTM/normalized/boundary_rtm.gpkg")
BOUNDARY_LAYER = "boundary"

OUT_GPKG = Path("processed/RTM/derived/hydrography_rtm.gpkg")
OUT_LAYER = "hydrography_rtm"


def main() -> int:
    if not HYDRO_IN.exists():
        raise FileNotFoundError(f"Missing input hydrography: {HYDRO_IN}")
    if not BOUNDARY_IN.exists():
        raise FileNotFoundError(f"Missing boundary: {BOUNDARY_IN}")

    # Read boundary (single polygon)
    boundary = gpd.read_file(BOUNDARY_IN, layer=BOUNDARY_LAYER, engine="pyogrio")
    if boundary.crs is None:
        raise ValueError("Boundary CRS missing.")
    boundary = boundary.to_crs(TARGET_CRS)

    # Read hydrography
    hydro = gpd.read_file(HYDRO_IN, layer=HYDRO_LAYER, engine="pyogrio")
    if hydro.crs is None:
        raise ValueError("Hydrography CRS missing.")
    hydro = hydro.to_crs(TARGET_CRS)

    n_before = len(hydro)

    # Clip
    clipped = gpd.clip(hydro, boundary)

    # Clean geometry (optional but helps)
    clipped = clipped[~clipped.geometry.is_empty].copy()
    clipped = clipped[clipped.geometry.notna()].copy()

    n_after = len(clipped)

    OUT_GPKG.parent.mkdir(parents=True, exist_ok=True)
    clipped.to_file(OUT_GPKG, layer=OUT_LAYER, driver="GPKG")

    print(f"Hydrography features before: {n_before}")
    print(f"Hydrography features after : {n_after}")
    print(f"Wrote: {OUT_GPKG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
