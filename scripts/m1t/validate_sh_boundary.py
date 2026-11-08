from pathlib import Path
from zipfile import ZipFile
from contextlib import ExitStack
from math import floor, ceil

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio

from rasterio.io import MemoryFile
from rasterio.merge import merge
from rasterio.features import geometry_mask
from rasterio.windows import Window, transform as window_transform
from shapely.geometry import mapping, box

root = Path("../data").resolve()

archive = (
    root / "raw/HAM/terrain/lgv_dgm1/"
    "dgm1_hh_2022-04-30.zip"
)

sh_dir = root / "processed/HAM/derived/dgm1_sh_1m"

qa_dir = root / "runs/ham_m1_citywide/qa"
qa_dir.mkdir(parents=True, exist_ok=True)

coverage_csv = qa_dir / "ham_tile_coverage_candidates.csv"

# Identify the 23 affected building IDs.
qa = pd.read_csv(coverage_csv)

exception_ids = set(
    qa.loc[
        qa.minimum_tile_coverage < 0.99,
        "bldg_id"
    ].astype(str)
)

# Read buildings in the relevant boundary area.
gdf = gpd.read_file(
    root / "processed/HAM/derived/buildings_ham.gpkg",
    bbox=(555800, 5938750, 556250, 5939150)
)

gdf = gdf[
    gdf.bldg_id.astype(str).isin(exception_ids)
].copy()

assert len(gdf) == 23, (
    f"Expected 23 buildings, found {len(gdf)}"
)

hh_tiles = [
    "dgm1_32_555_5938_1_hh_2022.tif",
    "dgm1_32_556_5938_1_hh_2022.tif",
]

sh_tiles = [
    "dgm1_32_555_5939_1_sh_2021.tif",
    "dgm1_32_556_5939_1_sh_2021.tif",
]

print("\nHAMBURG / SCHLESWIG-HOLSTEIN RING QA")
print("=" * 55)

with ZipFile(archive) as z, ExitStack() as stack:

    sources = []

    # Read Hamburg source tiles directly from the ZIP.
    for filename in hh_tiles:
        matches = [
            name for name in z.namelist()
            if Path(name).name.lower() == filename.lower()
        ]

        if len(matches) != 1:
            raise ValueError(
                f"Expected one Hamburg tile: {filename}"
            )

        memory = stack.enter_context(
            MemoryFile(z.read(matches[0]))
        )

        src = stack.enter_context(memory.open())
        sources.append(src)

    # Open the converted Schleswig-Holstein tiles.
    for filename in sh_tiles:
        path = sh_dir / filename

        if not path.exists():
            raise FileNotFoundError(path)

        sources.append(
            stack.enter_context(rasterio.open(path))
        )

    for src in sources:
        if src.crs.to_epsg() != 25832:
            raise ValueError(f"CRS mismatch: {src.name}")

        if src.res != (1.0, 1.0):
            raise ValueError(f"Resolution mismatch: {src.name}")

    # Temporary four-tile mosaic, 1 m resolution.
    elevation, transform = merge(
        sources,
        bounds=(555000, 5938000, 557000, 5940000),
        res=(1, 1),
        nodata=-9999.0,
        method="first"
    )

data = elevation[0]

assert data.shape == (2000, 2000)

def ring_coverage(zone):
    """Measure geometric and valid-pixel coverage."""

    extent = box(555000, 5938000, 557000, 5940000)

    geometric = (
        zone.intersection(extent).area / zone.area
    )

    xmin, ymin, xmax, ymax = zone.bounds

    c0 = max(0, floor(xmin - 555000))
    c1 = min(2000, ceil(xmax - 555000))

    r0 = max(0, floor(5940000 - ymax))
    r1 = min(2000, ceil(5940000 - ymin))

    window = Window(
        c0, r0,
        c1 - c0,
        r1 - r0
    )

    subset = data[r0:r1, c0:c1]

    inside = geometry_mask(
        [mapping(zone)],
        out_shape=subset.shape,
        transform=window_transform(window, transform),
        invert=True
    )

    valid = (
        inside
        & np.isfinite(subset)
        & (subset != -9999.0)
    )

    total = int(inside.sum())
    count = int(valid.sum())

    fraction = count / total if total else 0.0

    return geometric, fraction, count, total


records = []

for _, row in gdf.iterrows():

    geom = row.geometry

    local_ring = geom.buffer(20).difference(geom)

    neighbourhood_ring = (
        geom.buffer(100).difference(geom.buffer(20))
    )

    lg, lv, lc, lt = ring_coverage(local_ring)

    ng, nv, nc, nt = ring_coverage(
        neighbourhood_ring
    )

    passed = (
        lg >= 0.99
        and ng >= 0.99
        and lv >= 0.99
        and nv >= 0.99
    )

    records.append({
        "bldg_id": str(row.bldg_id),
        "local_geometric": lg,
        "local_valid_fraction": lv,
        "local_valid_pixels": lc,
        "neighbourhood_geometric": ng,
        "neighbourhood_valid_fraction": nv,
        "neighbourhood_valid_pixels": nc,
        "passed": passed,
    })

df = pd.DataFrame(records)

output = qa_dir / "sh_boundary_ring_qa_1m.csv"
df.to_csv(output, index=False)

print("\nBuildings tested:", len(df))
print("PASS:", int(df.passed.sum()))
print("FLAG:", int((~df.passed).sum()))

print("\nMinimum valid fractions:")
print(
    "Local:",
    round(df.local_valid_fraction.min(), 6)
)
print(
    "Neighbourhood:",
    round(df.neighbourhood_valid_fraction.min(), 6)
)

if not df.passed.all():
    print("\nBuildings requiring investigation:")
    print(
        df.loc[
            ~df.passed,
            [
                "bldg_id",
                "local_valid_fraction",
                "neighbourhood_valid_fraction"
            ]
        ].to_string(index=False)
    )

print("\nOutput:", output)
print("QA COMPLETE")
