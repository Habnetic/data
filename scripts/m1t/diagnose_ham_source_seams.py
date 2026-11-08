"""Diagnose invalid elevation values at Hamburg's 1 m source seams.

Run from any directory with the data repository's geospatial Python environment:
    python data/scripts/m1t/diagnose_ham_source_seams.py

Inputs: existing Hamburg LGV ZIP, converted SH GeoTIFFs, and NI GeoTIFF.
Output: separate v2 QA JSON; original raster data and v1 QA are unchanged.
"""

from __future__ import annotations

import json
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import rasterio
from rasterio.io import MemoryFile

ROOT = Path(__file__).resolve().parents[2]
HH_ZIP = ROOT / "raw/HAM/terrain/lgv_dgm1/dgm1_hh_2022-04-30.zip"
SH_DIR = ROOT / "processed/HAM/derived/dgm1_sh_1m"
NI_DIR = ROOT / "raw/HAM/terrain/lgln_ni_dgm1"
OUTPUT = ROOT / "runs/ham_m1_citywide/qa/ham_cross_source_seam_diagnostic_v2.json"

# QA-only plausible range, NOT a scientific correction or a final source mask.
# Any pixel outside this range needs inspection. Values around -9999 are invalid.
MIN_QA_ELEVATION_M = -1000.0
MAX_QA_ELEVATION_M = 1000.0

PAIRS = [
    {
        "name": "HH_SH_555",
        "hh": "dgm1_32_555_5938_1_hh_2022.tif",
        "other": SH_DIR / "dgm1_32_555_5939_1_sh_2021.tif",
        "direction": "north",
        "near_buildings_coordinate_range_m": (555850, 556000),
    },
    {
        "name": "HH_SH_556",
        "hh": "dgm1_32_556_5938_1_hh_2022.tif",
        "other": SH_DIR / "dgm1_32_556_5939_1_sh_2021.tif",
        "direction": "north",
        "near_buildings_coordinate_range_m": (556000, 556200),
    },
    {
        "name": "HH_NI_552",
        "hh": "dgm1_32_553_5924_1_hh_2022.tif",
        "other": NI_DIR / "dgm1_32_552_5924_1_ni_2025.tif",
        "direction": "west",
        "near_buildings_coordinate_range_m": (5924600, 5925000),
    },
]


def read_source(src: rasterio.io.DatasetReader) -> tuple[np.ndarray, dict]:
    """Load a 1-km tile and separately audit metadata and stored values."""
    if src.crs is None or src.crs.to_epsg() != 25832:
        raise ValueError(f"Unexpected CRS: {src.name}: {src.crs}")
    if not np.allclose(src.res, (1.0, 1.0), atol=1e-8):
        raise ValueError(f"Unexpected pixel size: {src.name}: {src.res}")
    if (src.height, src.width) != (1000, 1000) or src.count != 1:
        raise ValueError(f"Unexpected raster shape/bands: {src.name}")

    raw = src.read(1).astype("float64")
    metadata_mask = src.read_masks(1) == 0
    huge = np.isfinite(raw) & ((raw < MIN_QA_ELEVATION_M) | (raw > MAX_QA_ELEVATION_M))
    suspect = metadata_mask | ~np.isfinite(raw) | huge | (raw == -9999.0)

    info = {
        "file": Path(src.name).name,
        "metadata_nodata": src.nodata,
        "metadata_masked_pixel_count": int(np.count_nonzero(metadata_mask)),
        "exact_minus_9999_pixel_count": int(np.count_nonzero(raw == -9999.0)),
        "minus_9999_not_metadata_masked_count": int(np.count_nonzero((raw == -9999.0) & ~metadata_mask)),
        "outside_exploratory_range_count": int(np.count_nonzero(huge)),
        "other_nonfinite_count": int(np.count_nonzero(~np.isfinite(raw))),
        "provisionally_valid_pixel_count": int(np.count_nonzero(~suspect)),
        "qa_range_m": [MIN_QA_ELEVATION_M, MAX_QA_ELEVATION_M],
    }
    clean = raw.copy()
    clean[suspect] = np.nan
    return clean, info


def seam_statistics(
    hh: np.ndarray, other: np.ndarray, direction: str, coord: np.ndarray,
    interval: tuple[int, int]
) -> dict:
    """Compare four valid pixels spanning each seam position."""
    if direction == "north":
        # Source order: HH lower tile, supplementary tile immediately north.
        hh_edge, hh_interior = hh[0, :], hh[1, :]
        other_edge, other_interior = other[-1, :], other[-2, :]
        signed_step = other_edge - hh_edge  # northward
        reference_step = ((hh_edge - hh_interior) + (other_interior - other_edge)) / 2
    elif direction == "west":
        # Source order: supplementary western tile, HH eastern tile.
        hh_edge, hh_interior = hh[:, 0], hh[:, 1]
        other_edge, other_interior = other[:, -1], other[:, -2]
        signed_step = hh_edge - other_edge  # eastward
        reference_step = ((hh_interior - hh_edge) + (other_edge - other_interior)) / 2
    else:
        raise ValueError(direction)

    valid = (
        np.isfinite(hh_edge) & np.isfinite(hh_interior)
        & np.isfinite(other_edge) & np.isfinite(other_interior)
    )
    candidate = coord >= interval[0]
    candidate &= coord < interval[1]

    def describe(mask: np.ndarray) -> dict:
        values = (signed_step - reference_step)[mask]
        result = {
            "total_positions": int(mask.size if mask is valid else int(np.count_nonzero(candidate))),
            "valid_four_pixel_comparisons": int(values.size),
            "dropped_positions": int(np.count_nonzero(~valid if mask is valid else candidate & ~valid)),
        }
        if values.size == 0:
            result["interpretation"] = "INCONCLUSIVE: no valid 4-pixel comparisons"
            return result
        result.update({
            "median_gradient_adjusted_residual_m": float(np.median(values)),
            "p95_abs_residual_m": float(np.percentile(np.abs(values), 95)),
            "p99_abs_residual_m": float(np.percentile(np.abs(values), 99)),
            "max_abs_residual_m": float(np.max(np.abs(values))),
            "interpretation": (
                "EXPLORATORY ONLY: insufficient near-building comparisons for stable summary"
                if values.size < 30 else
                "EXPLORATORY ONLY: requires geospatial and vertical-reference interpretation"
            ),
        })
        return result

    return {
        "all_1000_positions": describe(valid),
        "near_affected_buildings": {
            "coordinate_interval_m": list(interval),
            **describe(valid & candidate),
        },
    }


def main() -> None:
    if not HH_ZIP.is_file():
        raise FileNotFoundError(HH_ZIP)

    results: dict[str, dict] = {}
    with ZipFile(HH_ZIP) as archive, ExitStack() as stack:
        indexed = {}
        for member in archive.namelist():
            if member.lower().endswith(".tif"):
                key = Path(member).name.lower()
                if key in indexed:
                    raise ValueError(f"Duplicate filename in ZIP: {key}")
                indexed[key] = member

        for item in PAIRS:
            if not item["other"].is_file():
                raise FileNotFoundError(item["other"])
            hh_member = indexed.get(item["hh"].lower())
            if hh_member is None:
                raise ValueError(f"Missing Hamburg source tile {item['hh']}")

            with MemoryFile(archive.read(hh_member)) as mem:
                with mem.open() as hh_src, rasterio.open(item["other"]) as other_src:
                    if item["direction"] == "north":
                        aligned = (
                            abs(hh_src.bounds.top - other_src.bounds.bottom) < 0.01
                            and abs(hh_src.bounds.left - other_src.bounds.left) < 0.01
                        )
                        coords = hh_src.bounds.left + np.arange(1000) + 0.5
                    else:
                        aligned = (
                            abs(other_src.bounds.right - hh_src.bounds.left) < 0.01
                            and abs(other_src.bounds.bottom - hh_src.bounds.bottom) < 0.01
                        )
                        coords = hh_src.bounds.top - np.arange(1000) - 0.5
                    if not aligned:
                        raise ValueError(f"Misaligned tiles: {item['name']}")

                    hh_grid, hh_info = read_source(hh_src)
                    other_grid, other_info = read_source(other_src)
                    summary = seam_statistics(
                        hh_grid, other_grid, item["direction"], coords,
                        item["near_buildings_coordinate_range_m"],
                    )
                    results[item["name"]] = {
                        "hh_source": hh_info,
                        "supplementary_source": other_info,
                        "seam": summary,
                    }

            global_stats = summary["all_1000_positions"]
            local_stats = summary["near_affected_buildings"]
            print(f"\n{item['name']}")
            print("HH unmasked -9999:", hh_info["minus_9999_not_metadata_masked_count"])
            print("Other unmasked -9999:", other_info["minus_9999_not_metadata_masked_count"])
            print("Clean seam positions:", global_stats["valid_four_pixel_comparisons"], "/ 1000")
            print("Near buildings:", local_stats["valid_four_pixel_comparisons"],
                  "/", local_stats["total_positions"])
            print("Global median residual (m):", global_stats.get("median_gradient_adjusted_residual_m"))
            print("Near-building median residual (m):", local_stats.get("median_gradient_adjusted_residual_m"))
            print("Near-building P95 abs residual (m):", local_stats.get("p95_abs_residual_m"))

    report = {
        "city": "HAM",
        "phase": "M1-T",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "analysis": "1m four-neighbor gradient-adjusted seam diagnostic after provisional invalid-value exclusion",
        "exploratory_valid_elevation_range_m": [MIN_QA_ELEVATION_M, MAX_QA_ELEVATION_M],
        "does_not_apply_vertical_corrections": True,
        "warning": "This does not establish vertical datum equivalence, accuracy, or suitability for 5m merging.",
        "results": results,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print("\nHAMBURG SEAM DIAGNOSTIC V2: COMPLETED (NOT A PASS CERTIFICATE)")
    print("Output:", OUTPUT)


if __name__ == "__main__":
    main()
