from __future__ import annotations

from pathlib import Path
import os
import zipfile
import argparse

import cdsapi


def find_repo_root(start: Path) -> Path:
    """
    Walk upwards until we find something that looks like the project root.
    In your setup, the repo root is already .../Habnetic/data.
    """
    for p in [start, *start.parents]:
        if (p / ".git").exists() or (p / "pyproject.toml").exists() or (p / "README.md").exists():
            return p
    return start.parents[5]


def magic4(path: Path) -> bytes:
    try:
        with path.open("rb") as f:
            return f.read(4)
    except FileNotFoundError:
        return b""


def is_zip_file(path: Path) -> bool:
    return magic4(path) == b"PK\x03\x04"


def is_hdf5_file(path: Path) -> bool:
    # NetCDF4 files are HDF5 containers; HDF5 magic is b"\x89HDF"
    return magic4(path) == b"\x89HDF"


def extract_zip(zip_path: Path, out_dir: Path) -> list[Path]:
    extracted: list[Path] = []
    with zipfile.ZipFile(zip_path, "r") as z:
        for name in z.namelist():
            z.extract(name, out_dir)
            extracted.append(out_dir / name)
    return extracted


def looks_like_valid_era5_nc(path: Path) -> bool:
    """
    Cheap structural check:
    - must be HDF5 (NetCDF4)
    - and should contain 'tp' variable when opened
    """
    if not path.exists():
        return False
    if not is_hdf5_file(path):
        return False

    # Lazy import to avoid forcing xarray dependency on download-only use
    try:
        import xarray as xr
        ds = xr.open_dataset(path, engine="h5netcdf")
        ok = ("tp" in ds.data_vars) and (len(ds.dims) >= 2)
        ds.close()
        return bool(ok)
    except Exception:
        return False


# --- Resolve "repo root" robustly ---
SCRIPT_PATH = Path(__file__).resolve()
DEFAULT_ROOT = find_repo_root(SCRIPT_PATH)
REPO_ROOT = Path(os.environ.get("HABNETIC_ROOT", DEFAULT_ROOT)).resolve()

OUT = REPO_ROOT / "raw" / "RTM" / "hazards" / "pluvial" / "ERA5_Land"
OUT.mkdir(parents=True, exist_ok=True)

years = range(1991, 2021)
months = [f"{m:02d}" for m in range(1, 13)]
days = [f"{d:02d}" for d in range(1, 32)]
times = [f"{h:02d}:00" for h in range(0, 24)]

# CDS bbox order: North, West, South, East
area = [52.05, 4.00, 51.85, 4.65]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Redownload even if file looks valid.")
    args = parser.parse_args()

    print(f"Repo root: {REPO_ROOT}")
    print(f"Writing raw ERA5-Land files to: {OUT}")
    print(f"Force redownload: {args.force}")

    c = cdsapi.Client()

    for y in years:
        for m in months:
            target = OUT / f"era5_land_tp_hourly_{y}-{m}_RTM.nc"

            if not args.force and looks_like_valid_era5_nc(target):
                print(f"Skip (valid): {target.name}")
                continue

            # Clean up known-bad states before (re)downloading
            if target.exists():
                if is_zip_file(target):
                    print(f"Remove zipped payload: {target.name}")
                    target.unlink()
                elif not is_hdf5_file(target):
                    print(f"Remove non-HDF5 file: {target.name}")
                    target.unlink()
                else:
                    # HDF5 but failed the structural check (can't open / missing tp)
                    print(f"Remove unreadable/invalid HDF5: {target.name}")
                    target.unlink()

            print(f"Requesting {y}-{m} -> {target.name}")
            c.retrieve(
                "reanalysis-era5-land",
                {
                    "variable": "total_precipitation",
                    "year": str(y),
                    "month": m,
                    "day": days,
                    "time": times,
                    "area": area,
                    "data_format": "netcdf",
                    "download_format": "unarchived",
                },
                str(target),
            )

            # CDS may still return ZIP even if you ask for unarchived
            if is_zip_file(target):
                zip_path = target.with_suffix(".zip")
                target.rename(zip_path)
                print(f"Received ZIP payload. Renamed to: {zip_path.name}")

                extracted = extract_zip(zip_path, OUT)
                print(f"Extracted {len(extracted)} file(s) from {zip_path.name}")
                zip_path.unlink()

                nc_candidates = [p for p in extracted if p.suffix.lower() == ".nc"]
                if nc_candidates:
                    extracted_nc = nc_candidates[0]
                    if extracted_nc.name != target.name:
                        if target.exists():
                            target.unlink()
                        extracted_nc.rename(target)
                        print(f"Canonicalized extracted NC to: {target.name}")
                else:
                    print("WARNING: ZIP did not contain a .nc file. Inspect extracted contents.")

            # Final sanity: confirm we got something valid
            if looks_like_valid_era5_nc(target):
                print(f"OK: {target.name}")
            else:
                print(f"WARNING: downloaded file does not look valid: {target.name}")

    print("Done.")


if __name__ == "__main__":
    main()
