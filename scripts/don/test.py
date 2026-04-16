import pandas as pd

df = pd.read_parquet("processed/DON/hazards/pluvial/H_pluvial_v1_buildings.parquet")

print(df.shape)
print(df.columns.tolist())
print(df["H_pluvial_v1_mm"].describe(percentiles=[0.1, 0.5, 0.9, 0.99]))
print("duplicate bldg_id:", df["bldg_id"].duplicated().sum())
print("NaNs:", df["H_pluvial_v1_mm"].isna().sum())