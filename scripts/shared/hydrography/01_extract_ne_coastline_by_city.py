from __future__ import annotations

import json
import urllib.request
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd


NATURAL_EARTH_URL = (
    "https://naturalearth.s3.amazonaws.com/"
    "10m_physical/ne_10m_coastline.zip"
)

RAW_DIR = Path("raw") / "shared" / "natural_earth"
ZIP_PATH = RAW_DIR / "ne_10m_coastline.zip"
EXTRACT_DIR = RAW_DIR / "ne_10m_coastline"
SHP_PATH = EXTRACT_DIR / "ne_10m_coastline.shp"

CITY_CONFIGS = {
    "RTM": {
        "crs": "EPSG:28992",
        "boundary_candidates": [
            Path("processed") / "RTM" / "normalized" / "boundary_rtm.gpkg",  # <-- real one
            Path("processed") / "RTM" / "normalized" / "boundary.gpkg",
            Path("processed") / "RTM" / "derived" / "boundary_rtm.gpkg",
            Path("processed") / "RTM" / "derived" / "boundary.gpkg",
            Path("processed") / "RTM" / "boundary.gpkg",
        ],
        "output": Path("processed") / "RTM" / "derived" / "coastline_ne.gpkg",
    },
    "HAM": {
        "crs": "EPSG:25832",
        "boundary_candidates": [
            Path("processed") / "HAM" / "normalized" / "boundary_ham.gpkg",
            Path("processed") / "HAM" / "normalized" / "boundary.gpkg",
            Path("processed") / "HAM" / "derived" / "boundary_ham.gpkg",
            Path("processed") / "HAM" / "derived" / "boundary.gpkg",
            Path("processed") / "HAM" / "boundary.gpkg",
        ],
        "output": Path("processed") / "HAM" / "derived" / "coastline_ne.gpkg",
    },
    "DON": {
        "crs": "EPSG:25830",
        "boundary_candidates": [
            Path("processed") / "DON" / "normalized" / "boundary_don.gpkg",  # <-- real one
            Path("processed") / "DON" / "normalized" / "boundary.gpkg",
            Path("processed") / "DON" / "derived" / "boundary_don.gpkg",
            Path("processed") / "DON" / "derived" / "boundary.gpkg",
            Path("processed") / "DON" / "boundary.gpkg",
        ],
        "output": Path("processed") / "DON" / "derived" / "coastline_ne.gpkg",
    },
}

BOUNDARY_BUFFER_M = 20_000.0


def download_natural_earth() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if ZIP_PATH.exists():
        print(f"[ne] zip already exists: {ZIP_PATH}")
        return

    print(f"[ne] downloading: {NATURAL_EARTH_URL}")
    print(f"[ne] to: {ZIP_PATH}")

    urllib.request.urlretrieve(NATURAL_EARTH_URL, ZIP_PATH)

    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"Download failed: {ZIP_PATH}")


def extract_zip() -> None:
    if SHP_PATH.exists():
        print(f"[ne] shapefile already exists: {SHP_PATH}")
        return

    if not ZIP_PATH.exists():
        raise FileNotFoundError(f"Missing Natural Earth zip: {ZIP_PATH}")

    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[ne] extracting: {ZIP_PATH}")
    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        zf.extractall(EXTRACT_DIR)

    if not SHP_PATH.exists():
        raise FileNotFoundError(f"Expected shapefile not found after extraction: {SHP_PATH}")


def load_ne_coastline() -> gpd.GeoDataFrame:
    download_natural_earth()
    extract_zip()

    coast = gpd.read_file(SHP_PATH)

    if coast.empty:
        raise ValueError("Natural Earth coastline layer is empty.")

    if coast.crs is None:
        coast = coast.set_crs("EPSG:4326")

    print(f"[ne] loaded coastline: {len(coast):,} features | CRS={coast.crs}")
    return coast


def find_existing_boundary_path(city: str, candidates: list[Path]) -> Path:
    for path in candidates:
        if path.exists():
            return path

    checked = "\n".join(f"- {p}" for p in candidates)
    raise FileNotFoundError(
        f"No boundary file found for {city}. Checked:\n{checked}"
    )


def load_boundary(city: str, config: dict) -> gpd.GeoDataFrame:
    boundary_path = find_existing_boundary_path(
        city=city,
        candidates=config["boundary_candidates"],
    )

    print(f"[{city}] boundary: {boundary_path}")

    boundary = gpd.read_file(boundary_path)

    if boundary.empty:
        raise ValueError(f"{city} boundary is empty: {boundary_path}")

    if boundary.crs is None:
        raise ValueError(f"{city} boundary has no CRS: {boundary_path}")

    boundary = boundary.to_crs(config["crs"])
    boundary = boundary[~boundary.geometry.is_empty & boundary.geometry.notna()].copy()

    if boundary.empty:
        raise ValueError(f"{city} boundary has no valid geometry.")

    return boundary


def clean_geometries(gdf: gpd.GeoDataFrame, label: str) -> gpd.GeoDataFrame:
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()].copy()

    # Remove geometries with non-finite bounds
    finite_mask = []
    for geom in gdf.geometry:
        try:
            bounds = geom.bounds
            finite_mask.append(all(pd.notna(x) and abs(x) != float("inf") for x in bounds))
        except Exception:
            finite_mask.append(False)

    gdf = gdf[finite_mask].copy()

    # Repair invalid geometries where possible
    gdf["geometry"] = gdf.geometry.make_valid()
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()].copy()

    print(f"[clean] {label}: {len(gdf):,} valid geometries")
    return gdf

def extract_city_coastline(
    city: str,
    coast_ne: gpd.GeoDataFrame,
    boundary: gpd.GeoDataFrame,
    target_crs: str,
    buffer_m: float = BOUNDARY_BUFFER_M,
) -> gpd.GeoDataFrame:
    """
    Clip Natural Earth coastline to a buffered city boundary.

    The buffer is intentional: coastline often lies just outside the land boundary.
    """
    coast = coast_ne.to_crs(target_crs)
    coast = clean_geometries(coast, f"{city} Natural Earth coastline")

    boundary = boundary.to_crs(target_crs)
    boundary = clean_geometries(boundary, f"{city} boundary")

    # Merge boundary into one geometry, repair it, then buffer
    boundary_union = boundary.geometry.unary_union

    try:
        boundary_union = gpd.GeoSeries([boundary_union], crs=target_crs).make_valid().iloc[0]
    except Exception:
        boundary_union = boundary_union.buffer(0)

    clip_geom = boundary_union.buffer(buffer_m)
    clip_area = gpd.GeoDataFrame(geometry=[clip_geom], crs=target_crs)
    clip_area = clean_geometries(clip_area, f"{city} buffered clip area")

    # Cheap bbox prefilter before clipping, because apparently geometry enjoys suffering.
    minx, miny, maxx, maxy = clip_area.total_bounds
    coast_prefiltered = coast.cx[minx:maxx, miny:maxy].copy()

    if coast_prefiltered.empty:
        print(f"[{city}] WARNING: no coastline found in bbox with {buffer_m:.0f}m buffer")
        return coast_prefiltered

    try:
        city_coast = gpd.clip(coast_prefiltered, clip_area)
    except Exception as exc:
        print(f"[{city}] WARNING: gpd.clip failed: {exc}")
        print(f"[{city}] falling back to intersects-only coastline selection")
        mask = coast_prefiltered.intersects(clip_area.geometry.iloc[0])
        city_coast = coast_prefiltered[mask].copy()

    city_coast = clean_geometries(city_coast, f"{city} clipped coastline")

    if city_coast.empty:
        print(f"[{city}] WARNING: no coastline found with {buffer_m:.0f}m buffer")
        return city_coast

    city_coast["source"] = "Natural Earth 10m coastline"
    city_coast["city"] = city
    city_coast["buffer_m"] = buffer_m

    keep_cols = ["city", "source", "buffer_m", "geometry"]
    city_coast = city_coast[keep_cols].reset_index(drop=True)

    return city_coast

def save_city_coastline(city: str, gdf: gpd.GeoDataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        output_path.unlink()

    if gdf.empty:
        print(f"[{city}] not saving empty coastline")
        return

    gdf.to_file(output_path, layer="coastline_ne", driver="GPKG")

    summary = {
        "city": city,
        "source": "Natural Earth 10m coastline",
        "n_features": int(len(gdf)),
        "crs": str(gdf.crs),
        "total_bounds": [float(x) for x in gdf.total_bounds],
        "buffer_m": BOUNDARY_BUFFER_M,
        "output": str(output_path),
        "note": (
            "Natural Earth coastline clipped to buffered city boundary. "
            "Used as a consistent coastal distance proxy across Phase 3 cities."
        ),
    }

    summary_path = output_path.with_name("coastline_ne_summary.json")
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"[{city}] saved coastline: {output_path}")
    print(f"[{city}] saved summary: {summary_path}")
    print(f"[{city}] bounds: {gdf.total_bounds}")


def main() -> None:
    print("[ne] extracting Natural Earth coastline by city")

    coast_ne = load_ne_coastline()

    rows = []

    for city, config in CITY_CONFIGS.items():
        print(f"\n[{city}] processing")

        boundary = load_boundary(city, config)

        city_coast = extract_city_coastline(
            city=city,
            coast_ne=coast_ne,
            boundary=boundary,
            target_crs=config["crs"],
            buffer_m=BOUNDARY_BUFFER_M,
        )

        save_city_coastline(
            city=city,
            gdf=city_coast,
            output_path=config["output"],
        )

        rows.append(
            {
                "city": city,
                "n_features": int(len(city_coast)),
                "crs": config["crs"],
                "output": str(config["output"]),
                "empty": bool(city_coast.empty),
            }
        )

    summary_df = pd.DataFrame(rows)
    summary_path = Path("processed") / "shared" / "natural_earth_coastline_city_summary.csv"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(summary_path, index=False)

    print(f"\n[ne] saved cross-city summary: {summary_path}")
    print(summary_df)
    print("[ne] done")


if __name__ == "__main__":
    main()