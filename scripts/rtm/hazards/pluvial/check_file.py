import numpy as np
import xarray as xr

path = r"raw/RTM/hazards/pluvial/ERA5_Land/era5_land_tp_hourly_1991-01_RTM.nc"

ds = xr.open_dataset(path)  # or engine="cfgrib" / "h5netcdf" if needed
tp = ds["tp"].values

print("dims:", ds.dims)
print("nan count:", np.isnan(tp).sum())
print("finite fraction:", np.isfinite(tp).mean())
print("max (m):", float(np.nanmax(tp)))
print("mean (m):", float(np.nanmean(tp)))


import numpy as np

tp = ds["tp"].rename({"valid_time": "time"})
dead_lon = tp.notnull().any(dim=("time","latitude"))
print(ds["longitude"].values[~dead_lon.values])
