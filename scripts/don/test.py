import pandas as pd

df = pd.read_parquet("processed/DON/priors/building_water_proximity_v3.parquet")

print(df[[
    "dist_to_hydrography_m",
    "dist_to_coast_m",
    "dist_to_water_m"
]].head(20))

print("\nEquality checks:")
print("water == coast:",
      (df["dist_to_water_m"] == df["dist_to_coast_m"]).mean())

print("water == hydro:",
      (df["dist_to_water_m"] == df["dist_to_hydrography_m"]).mean())