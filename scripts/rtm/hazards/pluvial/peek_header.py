from pathlib import Path

p = Path(r"raw/RTM/hazards/pluvial/ERA5_Land/era5_land_tp_hourly_1991-01_RTM.nc")
b = p.read_bytes()[:4]
print("magic:", b)
