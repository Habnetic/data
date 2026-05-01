from pathlib import Path
import pandas as pd

DATA_ROOT = Path.cwd()  # run from data repo root

don_root = DATA_ROOT / "processed" / "DON"

priors_base_path = don_root / "priors" / "building_water_proximity.parquet"
priors_distance_path = don_root / "priors" / "building_water_proximity_v2_coast.parquet"
hazard_path = don_root / "hazards" / "pluvial" / "H_pluvial_v1_buildings.parquet"
output_path = don_root / "phase3_assets.parquet"

print(f"Loading base priors from: {priors_base_path}")
print(f"Loading v3 distance priors from: {priors_distance_path}")
print(f"Loading hazard from: {hazard_path}")

df_base = pd.read_parquet(priors_base_path)
df_v3 = pd.read_parquet(priors_distance_path)
df_haz = pd.read_parquet(hazard_path)

density_cols = [
    "bldg_id",
    "water_len_density_250m",
    "water_len_density_500m",
    "water_len_density_1000m",
]

distance_cols = [
    "bldg_id",
    "dist_to_water_m",
]

missing_base = [c for c in density_cols if c not in df_base.columns]
missing_v3 = [c for c in distance_cols if c not in df_v3.columns]

if missing_base:
    raise KeyError(f"Missing density columns in base priors: {missing_base}")
if missing_v3:
    raise KeyError(f"Missing distance columns in v3 priors: {missing_v3}")

df_exp = df_base[density_cols].merge(
    df_v3[distance_cols],
    on="bldg_id",
    how="inner",
    validate="one_to_one",
)

print("Exposure columns:")
print(df_exp.columns.tolist())
df_haz = pd.read_parquet(hazard_path)

print("Exposure columns:")
print(df_exp.columns.tolist())

print("Hazard columns:")
print(df_haz.columns.tolist())

# Required exposure columns
exposure_cols = [
    "bldg_id",
    "dist_to_water_m",
    "water_len_density_250m",
    "water_len_density_500m",
    "water_len_density_1000m",
]

missing_exp = [c for c in exposure_cols if c not in df_exp.columns]
if missing_exp:
    raise KeyError(f"Missing required exposure columns: {missing_exp}")

# Identify hazard column
hazard_candidates = [
    "H_pluvial_v1_mm",
    "H_pluvial_v1",
    "H",
    "hazard",
]

hazard_col = None
for c in hazard_candidates:
    if c in df_haz.columns:
        hazard_col = c
        break

if hazard_col is None:
    raise KeyError(
        "Could not identify hazard column in H_pluvial_v1_buildings.parquet. "
        f"Available columns: {df_haz.columns.tolist()}"
    )

if "bldg_id" not in df_haz.columns:
    raise KeyError("Hazard file is missing required key column: bldg_id")

df_exp_small = df_exp[exposure_cols].copy()
df_haz_small = df_haz[["bldg_id", hazard_col]].copy()

df = df_exp_small.merge(df_haz_small, on="bldg_id", how="inner", validate="one_to_one")

# Standardize hazard column name for Phase 3
if hazard_col != "H_pluvial_v1_mm":
    df = df.rename(columns={hazard_col: "H_pluvial_v1_mm"})

# Basic validation
if df["bldg_id"].duplicated().any():
    raise ValueError("Duplicate bldg_id values found after merge")

required_final = [
    "bldg_id",
    "dist_to_water_m",
    "water_len_density_250m",
    "water_len_density_500m",
    "water_len_density_1000m",
    "H_pluvial_v1_mm",
]

missing_final = [c for c in required_final if c not in df.columns]
if missing_final:
    raise KeyError(f"Missing required final columns: {missing_final}")

for c in required_final[1:]:
    if df[c].isna().any():
        n_missing = int(df[c].isna().sum())
        raise ValueError(f"Column {c} contains {n_missing} missing values")

print(f"Final row count: {len(df):,}")
print(df[required_final].head())

output_path.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(output_path, index=False)

print(f"Saved: {output_path}")