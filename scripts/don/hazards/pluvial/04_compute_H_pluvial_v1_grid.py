from __future__ import annotations

from pathlib import Path
import xarray as xr

AMAX_DIR = Path("processed/DON/hazards/pluvial")
OUT_PATH = Path("processed/DON/hazards/pluvial/H_pluvial_v1_grid.nc")

YEARS = list(range(1991, 2021))

# Smoke test version
# YEARS = [2020]


def main() -> None:
    files = [AMAX_DIR / f"era5_land_tp_amax_{y}_DON.nc" for y in YEARS]
    missing = [f for f in files if not f.exists()]
    if missing:
        raise SystemExit(f"Missing {len(missing)} annual AMAX files. First missing: {missing[0]}")

    dsets = [xr.open_dataset(f, engine="h5netcdf") for f in files]
    try:
        # Each dataset contains a single DataArray variable: tp_amax_mm
        amax = xr.concat([ds["tp_amax_mm"] for ds in dsets], dim="year")
        amax = amax.assign_coords(year=YEARS)

        H = amax.mean(dim="year", skipna=True)
        H.name = "H_pluvial_v1_mm"
        H.attrs["long_name"] = "Mean annual maximum 1-hour precipitation (1991–2020)"
        H.attrs["units"] = "mm"
        H.attrs["hazard_src"] = "ERA5-Land"
        H.attrs["hazard_metric"] = "mean_annual_max_1h_1991_2020"
        H.attrs["hazard_version"] = "v1"

        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        H.to_netcdf(OUT_PATH, engine="h5netcdf")
        print("Saved:", OUT_PATH)

        # Quick sanity stats
        print(
            "Sanity (mm):",
            "min", float(H.min()),
            "p50", float(H.quantile(0.50)),
            "p95", float(H.quantile(0.95)),
            "max", float(H.max()),
        )

    finally:
        for ds in dsets:
            ds.close()


if __name__ == "__main__":
    main()