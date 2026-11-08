from pathlib import Path
from zipfile import ZipFile
from rasterio.io import MemoryFile
import rasterio
import numpy as np
import json

root = Path("../data").resolve()

archive = root / (
    "raw/HAM/terrain/lgv_dgm1/"
    "dgm1_hh_2022-04-30.zip"
)

sh_dir = root / "processed/HAM/derived/dgm1_sh_1m"
ni_dir = root / "raw/HAM/terrain/lgln_ni_dgm1"
qa_dir = root / "runs/ham_m1_citywide/qa"
qa_dir.mkdir(parents=True, exist_ok=True)

pairs = [
    (
        "HH_SH_555",
        "dgm1_32_555_5938_1_hh_2022.tif",
        sh_dir / "dgm1_32_555_5939_1_sh_2021.tif",
        "north",
    ),
    (
        "HH_SH_556",
        "dgm1_32_556_5938_1_hh_2022.tif",
        sh_dir / "dgm1_32_556_5939_1_sh_2021.tif",
        "north",
    ),
    (
        "HH_NI_552",
        "dgm1_32_553_5924_1_hh_2022.tif",
        ni_dir / "dgm1_32_552_5924_1_ni_2025.tif",
        "west",
    ),
]

def read_grid(src):
    if src.crs.to_epsg() != 25832:
        raise ValueError(f"Unexpected CRS: {src.name}")

    if src.res != (1.0, 1.0):
        raise ValueError(f"Unexpected resolution: {src.name}")

    if (src.height, src.width) != (1000, 1000):
        raise ValueError(f"Unexpected dimensions: {src.name}")

    return src.read(1, masked=True).astype("float64").filled(np.nan)

def compare(hh, other, direction):

    if direction == "north":
        # Positive direction is northward.
        hh_edge = hh[0, :]
        hh_gradient = hh[0, :] - hh[1, :]

        other_edge = other[-1, :]
        other_gradient = other[-2, :] - other[-1, :]

        seam_difference = other_edge - hh_edge

    elif direction == "west":
        # Positive direction is eastward.
        hh_edge = hh[:, 0]
        hh_gradient = hh[:, 1] - hh[:, 0]

        other_edge = other[:, -1]
        other_gradient = other[:, -1] - other[:, -2]

        seam_difference = hh_edge - other_edge

    else:
        raise ValueError(direction)

    expected_step = (hh_gradient + other_gradient) / 2
    residual = seam_difference - expected_step

    valid = (
        np.isfinite(seam_difference)
        & np.isfinite(residual)
    )

    if not valid.any():
        raise ValueError("No valid boundary comparisons")

    diff = seam_difference[valid]
    res = residual[valid]

    return {
        "valid_comparisons": int(valid.sum()),
        "total_positions": int(len(valid)),
        "median_seam_difference_m": float(np.median(diff)),
        "median_gradient_adjusted_residual_m": float(np.median(res)),
        "p95_absolute_residual_m": float(np.percentile(np.abs(res), 95)),
        "p99_absolute_residual_m": float(np.percentile(np.abs(res), 99)),
        "max_absolute_residual_m": float(np.max(np.abs(res))),
    }

records = {}

with ZipFile(archive) as z:

    for label, hh_filename, supplementary, direction in pairs:

        matches = [
            name for name in z.namelist()
            if Path(name).name == hh_filename
        ]

        if len(matches) != 1:
            raise ValueError(f"Missing Hamburg tile: {hh_filename}")

        with MemoryFile(z.read(matches[0])) as mem:
            with mem.open() as hh_src:
                with rasterio.open(supplementary) as other_src:

                    hh_grid = read_grid(hh_src)
                    other_grid = read_grid(other_src)

                    # Verify that tile footprints are truly adjacent.
                    if direction == "north":
                        aligned = (
                            abs(hh_src.bounds.top - other_src.bounds.bottom) < 0.01
                            and abs(hh_src.bounds.left - other_src.bounds.left) < 0.01
                        )
                    else:
                        aligned = (
                            abs(other_src.bounds.right - hh_src.bounds.left) < 0.01
                            and abs(other_src.bounds.bottom - hh_src.bounds.bottom) < 0.01
                        )

                    if not aligned:
                        raise ValueError(f"Grid alignment failure: {label}")

                    result = compare(hh_grid, other_grid, direction)
                    records[label] = result

                    print(f"\n{label}")
                    print("Valid comparisons:", result["valid_comparisons"])
                    print(
                        "Median residual (m):",
                        round(result["median_gradient_adjusted_residual_m"], 4)
                    )
                    print(
                        "P95 absolute residual (m):",
                        round(result["p95_absolute_residual_m"], 4)
                    )
                    print(
                        "P99 absolute residual (m):",
                        round(result["p99_absolute_residual_m"], 4)
                    )

output = qa_dir / "ham_cross_source_seam_qa.json"

output.write_text(
    json.dumps({
        "city": "HAM",
        "phase": "M1-T",
        "resolution_m": 1,
        "method": "Adjacent-pixel differences adjusted by mean within-source gradient",
        "note": (
            "Exploratory boundary consistency screening. "
            "Not proof of vertical-datum equivalence or absolute accuracy."
        ),
        "results": records,
    }, indent=2) + "\n",
    encoding="utf-8"
)

print("\nHAMBURG CROSS-SOURCE SEAM AUDIT COMPLETE")
print("Output:", output)
