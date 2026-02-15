from __future__ import annotations

from pathlib import Path
import os
import zipfile

import cdsapi


def find_repo_root(start: Path) -> Path:
    """
    Walk upwards until we find something that looks like the project root.
    In your setup, the repo root is already .../Habnetic/data.
    """
    for p in [start, *start.parents]:
        if (p / ".git").exists() or (p / "pyproject.toml").exists() or (p / "README.md").exists():
            return p
    # Fallback: 5 levels up from this file (matches data/scripts/... layout)
    return start.parents[5]


def is_zip_file(path: Path) -> bool:
    try:
        with path.open("rb") as f:
            return f.read(4) == b"PK\x03\x04"
    except FileNotFoundError:
        return False


def extract_zip(zip_path: Path, out_dir: Path) -> list[Path]:
    extracted: list[Path] = []
    with zipfile.ZipFile(zip_path, "r") as z:
        for name in z.namelist():
            z.extract(name, out_dir)
            extracted.append(out_dir / name)
    return extracted


# --- Resolve "repo root" robustly (works no matter where you run from) ---
SCRIPT_PATH = Path(__file__).resolve()
DEFAULT_ROOT = find_repo_root(SCRIPT_PATH)
REPO_ROOT = Path(os.environ.get("HABNETIC_ROOT", DEFAULT_ROOT)).resolve()

# In your structure, REPO_ROOT already is .../Habnetic/data
# So raw data lives at: <REPO_ROOT>/raw/...
OUT = REPO_ROOT / "raw" / "RTM" / "hazards" / "pluvial" / "ERA5_Land"
OUT.mkdir(parents=True, exist_ok=True)

# --- Request parameters ---
years = range(1991, 2021)
months = [f"{m:02d}" for m in range(1, 13)]
days = [f"{d:02d}" for d in range(1, 32)]
times = [f"{h:02d}:00" for h in range(0, 24)]

# CDS bbox order: North, West, South, East
area = [52.05, 4.00, 51.85, 4.65]


def main() -> None:
    print(f"Repo root: {REPO_ROOT}")
    print(f"Writing raw ERA5-Land files to: {OUT}")

    c = cdsapi.Client()

    for y in years:
        for m in months:
            # We WANT a .nc, but CDS may still return a zip.
            # We'll save to .nc and detect/unzip if needed.
            target = OUT / f"era5_land_tp_hourly_{y}-{m}_RTM.nc"

            # Skip if we already have a sensible .nc (or extracted .nc)
            if target.exists() and target.stat().st_size > 1_000_000 and not is_zip_file(target):
                print(f"Skip (exists): {target.name}")
                continue

            # If previous run left a tiny/partial file OR a zip disguised as .nc, remove it and re-download
            if target.exists():
                if target.stat().st_size <= 1_000_000:
                    print(f"Remove partial/tiny: {target.name} ({target.stat().st_size} bytes)")
                    target.unlink()
                elif is_zip_file(target):
                    print(f"Remove zipped payload: {target.name}")
                    target.unlink()

            print(f"Requesting {y}-{m} -> {target.name}")
            c.retrieve(
                "reanalysis-era5-land",
                {
                    "variable": "total_precipitation",
                    "year": str(y),
                    "month": m,
                    "day": days,  # CDS ignores invalid days (e.g., 31 in Feb)
                    "time": times,
                    "area": area,
                    # Match the CDS UI concepts:
                    "data_format": "netcdf",
                    "download_format": "unarchived",
                },
                str(target),
            )

            # CDS sometimes still returns a ZIP even if you ask for unarchived.
            if is_zip_file(target):
                zip_path = target.with_suffix(".zip")
                target.rename(zip_path)
                print(f"Received ZIP payload. Renamed to: {zip_path.name}")

                extracted = extract_zip(zip_path, OUT)
                print(f"Extracted {len(extracted)} file(s) from {zip_path.name}")

                # Remove the zip after extraction
                zip_path.unlink()

                # If the zip contained a .nc, rename it to our canonical target name
                nc_candidates = [p for p in extracted if p.suffix.lower() == ".nc"]
                if nc_candidates:
                    # Take the first .nc file and rename to canonical name
                    extracted_nc = nc_candidates[0]
                    if extracted_nc.name != target.name:
                        if target.exists():
                            target.unlink()
                        extracted_nc.rename(target)
                        print(f"Canonicalized extracted NC to: {target.name}")
                else:
                    print("WARNING: ZIP did not contain a .nc file. Inspect extracted contents.")

    print("Done.")


if __name__ == "__main__":
    main()
