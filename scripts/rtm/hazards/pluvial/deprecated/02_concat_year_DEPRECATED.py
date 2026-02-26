from pathlib import Path
import xarray as xr

RAW = Path("raw/RTM/hazards/pluvial/ERA5_Land")

year = 1991

files = sorted(RAW.glob(f"era5_land_tp_hourly_{year}-*.nc"))

print("Files found:", len(files))
for f in files:
    print("  ", f.name)

# Open all monthly datasets
ds = xr.open_mfdataset(
    files,
    combine="by_coords",
    parallel=False,
)

# Normalize time coordinate name
if "valid_time" in ds.coords:
    ds = ds.rename({"valid_time": "time"})

print(ds)

# Optional: sort by time (safety)
ds = ds.sortby("time")

# Save concatenated year
OUT = Path("processed/RTM/hazards/pluvial")
OUT.mkdir(parents=True, exist_ok=True)

out_path = OUT / f"era5_land_tp_hourly_{year}_RTM.nc"
ds.to_netcdf(out_path)

print("Saved:", out_path)
