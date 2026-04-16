from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import xarray as xr


RAW = Path("raw/DON/hazards/pluvial/ERA5_Land")
OUT = Path("processed/DON/hazards/pluvial")
OUT.mkdir(parents=True, exist_ok=True)


def is_leap(year: int) -> bool:
    """Gregorian leap year rule."""
    return (year % 4 == 0) and ((year % 100 != 0) or (year % 400 == 0))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "DON Phase 3: Validate ERA5-Land hourly tp monthly files for a given year, "
            "enforce strict hourly continuity, and compute annual maximum 1-hour precipitation "
            "(AMAX) in millimeters."
        )
    )
    p.add_argument(
        "--year",
        type=int,
        required=True,
        help="Year to process (e.g. 1992). Must have 12 monthly files present.",
    )
    p.add_argument(
        "--raw",
        type=Path,
        default=RAW,
        help=f"Raw monthly ERA5-Land directory (default: {RAW.as_posix()})",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=OUT,
        help=f"Output directory for annual AMAX netcdf (default: {OUT.as_posix()})",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    print("SCRIPT:", Path(__file__).resolve())
    print("ARGS year:", args.year)
    year: int = args.year
    raw_dir: Path = args.raw
    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(raw_dir.glob(f"era5_land_tp_hourly_{year}-*_DON.nc"))
    print(f"RAW dir: {raw_dir.resolve()}")
    print(f"OUT dir: {out_dir.resolve()}")
    print(f"Found {len(files)} files for {year}")
    for f in files:
        print(" ", f.name)

    if len(files) != 12:
        raise SystemExit(f"Need 12 monthly files for {year}, found {len(files)}")

    # Open monthly files as one dataset (no dask)
    ds = xr.open_mfdataset(
        files,
        combine="by_coords",
        parallel=False,
        chunks=None,
        engine="h5netcdf",
    )

    try:
        # Normalize time coord name
        if "valid_time" in ds.coords:
            ds = ds.rename({"valid_time": "time"})
        if "time" not in ds.coords:
            raise SystemExit("No 'time' coordinate found (expected 'time' or 'valid_time').")

        ds = ds.sortby("time")

        # --- continuity checks ---
        t = ds["time"].values
        print("Total hours:", len(t))

        if len(t) < 2:
            raise SystemExit("Not enough timesteps to validate continuity.")

        dt = np.diff(t).astype("timedelta64[h]")
        print("Min step (h):", dt.min())
        print("Max step (h):", dt.max())

        expected_hours = 8784 if is_leap(year) else 8760
        print("Expected hours:", expected_hours)

        if len(t) != expected_hours:
            raise SystemExit(f"Hour count mismatch: got {len(t)}, expected {expected_hours}")

        if not (dt.min() == np.timedelta64(1, "h") and dt.max() == np.timedelta64(1, "h")):
            raise SystemExit("Time is not strictly hourly continuous (gaps or duplicates).")

        # --- annual max computation (in mm) ---
        if "tp" not in ds.data_vars:
            raise SystemExit("Dataset missing expected variable 'tp' (total precipitation).")

        # ERA5-Land tp is typically in meters; Phase 3 hazard spec locks mm.
        tp_mm = ds["tp"] * 1000.0
        try:
            tp_mm.attrs.update(ds["tp"].attrs)
        except Exception:
            pass
        tp_mm.attrs["units"] = "mm"

        annual_max = tp_mm.max(dim="time", skipna=True)

        annual_max.name = "tp_amax_mm"
        annual_max.attrs["long_name"] = "Annual maximum 1-hour total precipitation"
        annual_max.attrs["units"] = "mm"
        annual_max.attrs["source"] = "ERA5-Land hourly (CDS), aggregated by Habnetic"
        annual_max.attrs["year"] = str(year)

        out_path = out_dir / f"era5_land_tp_amax_{year}_DON.nc"
        annual_max.to_netcdf(out_path, engine="h5netcdf")
        print("Saved:", out_path)

    finally:
        # Explicit close helps avoid Windows/HDF5 destructor spam
        ds.close()


if __name__ == "__main__":
    main()