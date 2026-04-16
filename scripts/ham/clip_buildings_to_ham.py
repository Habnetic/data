from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd


@dataclass(frozen=True)
class Paths:
    buildings_norm: Path = Path("processed/HAM/normalized/buildings.gpkg")
    buildings_layer: str = "buildings"

    boundary_norm: Path = Path("processed/HAM/normalized/boundary_ham.gpkg")
    boundary_layer: str | None = None  # None = first layer

    out_gpkg: Path = Path("processed/HAM/derived/buildings_ham.gpkg")
    out_layer: str = "buildings_ham"


def _read_any_layer(path: Path) -> gpd.GeoDataFrame:
    return gpd.read_file(path, engine="pyogrio")


def main() -> int:
    p = Paths()

    if not p.buildings_norm.exists():
        raise FileNotFoundError(f"Missing: {p.buildings_norm}")
    if not p.boundary_norm.exists():
        raise FileNotFoundError(f"Missing: {p.boundary_norm}")

    print("Reading buildings (normalized)...")
    buildings = gpd.read_file(p.buildings_norm, layer=p.buildings_layer, engine="pyogrio")
    buildings = buildings[~buildings.geometry.isna()].copy()

    # Require stable join key from normalization step
    if "bldg_id" not in buildings.columns:
        raise ValueError(
            "Missing 'bldg_id' in normalized buildings. "
            "Re-run scripts/ham/normalize_buildings.py (it must write bldg_id)."
        )

    print("Reading HAM boundary (normalized)...")
    boundary = _read_any_layer(p.boundary_norm)
    boundary = boundary[~boundary.geometry.isna()].copy()

    boundary = boundary.dissolve()  # one row
    if buildings.crs != boundary.crs:
        boundary = boundary.to_crs(buildings.crs)

    print("Clipping buildings to HAM boundary...")
    clipped = gpd.clip(buildings, boundary)

    clipped = clipped.reset_index(drop=True)
    clipped = clipped[~clipped.geometry.is_empty]
    clipped = clipped.set_geometry("geometry")

    p.out_gpkg.parent.mkdir(parents=True, exist_ok=True)

    print(f"Writing: {p.out_gpkg} (layer={p.out_layer}) ...")
    clipped.to_file(p.out_gpkg, driver="GPKG", layer=p.out_layer, engine="pyogrio", mode="w")

    print(f"Wrote {len(clipped)} buildings → {p.out_gpkg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())