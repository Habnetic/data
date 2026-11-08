"""Compare shared M1-T extractor with frozen Rotterdam M1 reference values."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
COLUMNS = [
    "local_z_50", "neighbourhood_z_50", "neighbourhood_z_25",
    "T50", "T25", "local_valid_pixels", "local_total_pixels",
    "local_coverage", "neighbourhood_valid_pixels",
    "neighbourhood_total_pixels", "neighbourhood_coverage",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    recent = ROOT / "runs/rtm_m1t_regression/terrain_pilot"
    frozen = ROOT / "runs/rtm_m1_citywide/terrain_batches"
    new_files = sorted(recent.glob("terrain_*.parquet"))
    old_files = sorted(frozen.glob("terrain_*.parquet"))
    if not new_files or not old_files:
        raise FileNotFoundError("Missing M1-T pilot or frozen RTM batch files")
    new = pd.concat((pd.read_parquet(str(p)) for p in new_files), ignore_index=True)
    old = pd.concat((pd.read_parquet(str(p)) for p in old_files[:1]), ignore_index=True)
    new = new.iloc[:args.limit]
    old = old.iloc[:args.limit]
    if new["bldg_id"].tolist() != old["bldg_id"].tolist():
        raise AssertionError("Frozen M1 and M1-T building identifiers/order differ")
    measured = new["terrain_measured"] & old["terrain_measured"]
    print("Compared buildings:", len(new))
    print("Both measured:", int(measured.sum()))
    print("M1-T geometric QA withheld:", int((old["terrain_measured"] & ~new["terrain_measured"]).sum()))
    if int(measured.sum()) == 0:
        raise AssertionError("No jointly measured buildings in regression sample")
    for field in COLUMNS:
        a = new.loc[measured, field].to_numpy(dtype=float)
        b = old.loc[measured, field].to_numpy(dtype=float)
        if not np.allclose(a, b, rtol=0, atol=1e-8, equal_nan=True):
            largest = float(np.nanmax(np.abs(a - b)))
            raise AssertionError("Regression mismatch for {} (max delta {})".format(field, largest))
        print("PASS:", field)
    print("RTM REGRESSION: PASS (conditional on M1-T geometric QA)")


if __name__ == "__main__":
    main()
