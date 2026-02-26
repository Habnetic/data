from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr


GRID_PATH = Path("processed/RTM/hazards/pluvial/H_pluvial_v1_grid.nc")
BUILDINGS_PATH = Path("processed/RTM/derived/buildings_rtm.gpkg")
OUT_PATH = Path("processed/RTM/hazards/pluvial/H_pluvial_v1_buildings.parquet")


def fill_grid_nans_kdtree(H: xr.DataArray) -> xr.DataArray:
    """
    Fill NaNs in a 2D lat/lon grid by copying the value of the nearest non-NaN grid cell.
    Uses SciPy cKDTree if available, otherwise brute force (fine for a handful of NaNs).

    This is a pragmatic Phase 1 fix for isolated NaNs (e.g., land/sea mask artifacts).
    """
    lons = H["longitude"].values
    lats = H["latitude"].values

    # 2D coordinate arrays matching H shape (lat, lon)
    lon2d, lat2d = np.meshgrid(lons, lats)

    vals = np.asarray(H.values)
    nan_mask = np.isnan(vals)

    if not nan_mask.any():
        return H

    coords = np.column_stack([lon2d.ravel(), lat2d.ravel()])
    vals_flat = vals.ravel()

    valid_mask = ~np.isnan(vals_flat)
    nan_idx = np.where(~valid_mask)[0]

    if valid_mask.sum() == 0:
        raise SystemExit("Grid has no valid (non-NaN) cells to fill from.")

    # Try SciPy KDTree; fallback to brute force
    try:
        from scipy.spatial import cKDTree  # type: ignore

        tree = cKDTree(coords[valid_mask])
        _, nn = tree.query(coords[nan_idx], k=1)
        vals_flat[nan_idx] = vals_flat[valid_mask][nn]
    except Exception:
        valid_coords = coords[valid_mask]
        valid_vals = vals_flat[valid_mask]
        for i in nan_idx:
            d2 = np.sum((valid_coords - coords[i]) ** 2, axis=1)
            vals_flat[i] = valid_vals[int(np.argmin(d2))]

    filled = vals_flat.reshape(vals.shape)
    return H.copy(data=filled)


def main() -> None:
    if not GRID_PATH.exists():
        raise SystemExit(f"Missing grid file: {GRID_PATH}")

    if not BUILDINGS_PATH.exists():
        raise SystemExit(f"Missing buildings file: {BUILDINGS_PATH}")

    # --- Load hazard grid ---
    ds = xr.open_dataset(GRID_PATH, engine="h5netcdf")
    try:
        if "H_pluvial_v1_mm" not in ds.data_vars:
            raise SystemExit(f"Grid file missing 'H_pluvial_v1_mm'. Found: {list(ds.data_vars)}")

        H = ds["H_pluvial_v1_mm"]

        # Ensure expected coords exist
        if "longitude" not in H.coords or "latitude" not in H.coords:
            raise SystemExit(f"Expected coords 'longitude' and 'latitude'. Found: {list(H.coords)}")

        # Ensure monotonic coords for xarray interp
        H2 = H.sortby("longitude").sortby("latitude")

        lon_min = float(H2.longitude.min())
        lon_max = float(H2.longitude.max())
        lat_min = float(H2.latitude.min())
        lat_max = float(H2.latitude.max())

        grid_nan_count = int(H2.isnull().sum().item())
        print("Grid NaN count before fill:", grid_nan_count)

        if grid_nan_count > 0:
            H2_filled = fill_grid_nans_kdtree(H2)
            grid_nan_count_after = int(H2_filled.isnull().sum().item())
            print("Grid NaN count after fill:", grid_nan_count_after)
            if grid_nan_count_after > 0:
                raise SystemExit("Grid still contains NaNs after KDTree fill (unexpected).")
        else:
            H2_filled = H2

        # --- Load buildings (try pyogrio for speed; fallback otherwise) ---
        try:
            gdf = gpd.read_file(BUILDINGS_PATH, engine="pyogrio")
        except Exception:
            gdf = gpd.read_file(BUILDINGS_PATH)

        if "bldg_id" not in gdf.columns:
            raise SystemExit("buildings_rtm.gpkg missing 'bldg_id' column.")
        if gdf.crs is None:
            raise SystemExit("buildings_rtm.gpkg has no CRS. Expected EPSG:28992.")

        print("Loaded buildings:", len(gdf))
        print("Buildings CRS:", gdf.crs)

        # --- Centroids to WGS84 (ERA5 grid is lat/lon) ---
        centroids = gdf.geometry.centroid
        centroids_wgs = gpd.GeoSeries(centroids, crs=gdf.crs).to_crs("EPSG:4326")

        lons = centroids_wgs.x.to_numpy()
        lats = centroids_wgs.y.to_numpy()

        print("GRID lon range:", lon_min, lon_max)
        print("GRID lat range:", lat_min, lat_max)
        print("BLDG lon range:", float(lons.min()), float(lons.max()))
        print("BLDG lat range:", float(lats.min()), float(lats.max()))

        # Clamp to grid bounds to avoid outside-domain NaNs
        lons_c = np.clip(lons, lon_min, lon_max)
        lats_c = np.clip(lats, lat_min, lat_max)

        # --- Bilinear interpolation on filled grid ---
        H_interp = H2_filled.interp(
            longitude=("points", lons_c),
            latitude=("points", lats_c),
            method="linear",
        )
        hazard_vals = H_interp.to_numpy()

        nan_mask = pd.isna(hazard_vals)
        if nan_mask.any():
            print(f"NaNs after clamped bilinear: {int(nan_mask.sum())} — nearest fallback.")
            H_nn = H2_filled.interp(
                longitude=("points", lons_c),
                latitude=("points", lats_c),
                method="nearest",
            )
            hazard_vals[nan_mask] = H_nn.to_numpy()[nan_mask]

        if pd.isna(hazard_vals).any():
            raise SystemExit("NaNs remain after filled-grid interpolation. Inspect grid + building extent.")

        # --- Output table ---
        out_df = pd.DataFrame(
            {
                "bldg_id": gdf["bldg_id"].to_numpy(),
                "H_pluvial_v1_mm": hazard_vals.astype("float32"),
                "hazard_src": "ERA5-Land",
                "hazard_metric": "mean_annual_max_1h_1991_2020",
                "hazard_version": "v1",
            }
        )

        # Integrity checks
        if out_df["bldg_id"].isna().any():
            raise SystemExit("NaNs in bldg_id (unexpected).")
        if out_df["bldg_id"].duplicated().any():
            raise SystemExit("Duplicate bldg_id detected (unexpected).")
        if out_df["H_pluvial_v1_mm"].isna().any():
            raise SystemExit("NaNs in hazard column after interpolation (unexpected).")

        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        out_df.to_parquet(OUT_PATH, index=False)

        print("Saved:", OUT_PATH)
        print("Row count:", len(out_df))
        print(
            "Sanity (mm):",
            "min", float(out_df["H_pluvial_v1_mm"].min()),
            "p50", float(out_df["H_pluvial_v1_mm"].quantile(0.50)),
            "p95", float(out_df["H_pluvial_v1_mm"].quantile(0.95)),
            "max", float(out_df["H_pluvial_v1_mm"].max()),
        )

    finally:
        ds.close()


if __name__ == "__main__":
    main()