from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd


RAW_OSM_PATH = Path("raw") / "DON" / "buildings" / "pais_vasco.gpkg"
BOUNDARY_PATH = Path("processed") / "DON" / "normalized" / "boundary.gpkg"

OUT_DIR = Path("processed") / "DON" / "derived"
OUT_PATH = OUT_DIR / "coastal_proxy_don.gpkg"

TARGET_CRS = "EPSG:25830"

COASTAL_FCLASSES = ["beach", "cliff"]


def read_boundary() -> gpd.GeoDataFrame | None:
    """Read DON boundary if available."""
    if not BOUNDARY_PATH.exists():
        print(f"[coast] boundary not found, skipping clip: {BOUNDARY_PATH}")
        return None

    boundary = gpd.read_file(BOUNDARY_PATH)
    boundary = boundary.to_crs(TARGET_CRS)

    if boundary.empty:
        raise ValueError(f"Boundary is empty: {BOUNDARY_PATH}")

    return boundary


def load_natural_polygons() -> gpd.GeoDataFrame:
    """Load OSM natural polygon layer."""
    if not RAW_OSM_PATH.exists():
        raise FileNotFoundError(f"Missing OSM GPKG: {RAW_OSM_PATH}")

    gdf = gpd.read_file(
        RAW_OSM_PATH,
        layer="gis_osm_natural_a_free",
    )

    if gdf.empty:
        raise ValueError("OSM natural polygon layer is empty.")

    if "fclass" not in gdf.columns:
        raise KeyError("Expected column 'fclass' in gis_osm_natural_a_free.")

    gdf = gdf.to_crs(TARGET_CRS)

    print("[coast] natural polygon fclasses:")
    print(gdf["fclass"].value_counts(dropna=False))

    return gdf


def build_coastal_proxy(
    natural: gpd.GeoDataFrame,
    boundary: gpd.GeoDataFrame | None,
    boundary_buffer_m: float = 2_000.0,
) -> gpd.GeoDataFrame:
    """
    Build a coastal proxy from beach and cliff polygons.

    This is not a sea polygon. It is a pragmatic coastline influence proxy
    used to correct distance-to-water calculations where the sea itself is
    absent from OSM water polygons.
    """
    coast = natural[natural["fclass"].isin(COASTAL_FCLASSES)].copy()

    if coast.empty:
        raise ValueError(
            f"No coastal features found with fclass in {COASTAL_FCLASSES}"
        )

    coast = coast[~coast.geometry.is_empty & coast.geometry.notna()].copy()
    coast["source"] = "osm_gis_osm_natural_a_free"
    coast["coastal_proxy_type"] = coast["fclass"]

    if boundary is not None:
        clip_geom = boundary.copy()
        clip_geom["geometry"] = clip_geom.geometry.buffer(boundary_buffer_m)

        coast = gpd.clip(coast, clip_geom)

        if coast.empty:
            raise ValueError(
                "Coastal proxy became empty after clipping. "
                "Increase boundary_buffer_m or inspect boundary geometry."
            )

    keep_cols = [
        "osm_id",
        "fclass",
        "name",
        "source",
        "coastal_proxy_type",
        "geometry",
    ]
    keep_cols = [c for c in keep_cols if c in coast.columns]

    coast = coast[keep_cols].copy()
    coast = coast.reset_index(drop=True)

    return coast


def save_outputs(coast: gpd.GeoDataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if OUT_PATH.exists():
        OUT_PATH.unlink()

    coast.to_file(OUT_PATH, layer="coastal_proxy_don", driver="GPKG")

    summary = {
        "n_features": int(len(coast)),
        "crs": str(coast.crs),
        "fclass_counts": coast["fclass"].value_counts(dropna=False).to_dict(),
        "output": str(OUT_PATH),
        "note": (
            "Coastal proxy extracted from OSM natural polygons "
            "using fclass in ['beach', 'cliff']. This is used because "
            "the sea polygon/coastline is absent from the current DON water layers."
        ),
    }

    summary_path = OUT_DIR / "coastal_proxy_don_summary.json"
    pd.Series(summary).to_json(summary_path, indent=2)

    print(f"[coast] saved: {OUT_PATH}")
    print(f"[coast] saved summary: {summary_path}")
    print(summary)


def main() -> None:
    print("[coast] extracting DON coastal proxy")

    boundary = read_boundary()
    natural = load_natural_polygons()
    coast = build_coastal_proxy(natural=natural, boundary=boundary)

    print(f"[coast] coastal proxy features: {len(coast):,}")
    print(coast[["fclass", "name"]].head(20))

    save_outputs(coast)

    print("[coast] done")


if __name__ == "__main__":
    main()