from pathlib import Path
from zipfile import ZipFile
from contextlib import ExitStack
from hashlib import sha256

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio

from rasterio.io import MemoryFile
from rasterio.merge import merge
from rasterio.features import geometry_mask
from shapely.geometry import mapping, box
from shapely.ops import unary_union

root = Path("../data").resolve()

hh_archive = (
    root / "raw/HAM/terrain/lgv_dgm1/"
    "dgm1_hh_2022-04-30.zip"
)

ni_file = (
    root / "raw/HAM/terrain/lgln_ni_dgm1/"
    "dgm1_32_552_5924_1_ni_2025.tif"
)

buildings_file = (
    root / "processed/HAM/derived/buildings_ham.gpkg"
)

output_dir = root / "runs/ham_m1_citywide/qa"
output_dir.mkdir(parents=True, exist_ok=True)

ids = {"9091", "9152", "9158"}

gdf = gpd.read_file(
    buildings_file,
    bbox=(552800, 5924600, 553300, 5925100)
)

gdf = gdf[
    gdf.bldg_id.astype(str).isin(ids)
].copy()

assert len(gdf) == 3
assert gdf.bldg_id.astype(str).is_unique
assert gdf.crs.to_epsg() == 25832

print("\nHAMBURG / NIEDERSACHSEN BOUNDARY QA")
print("=" * 55)

with ZipFile(hh_archive) as z, ExitStack() as stack:

    filename = "dgm1_32_553_5924_1_hh_2022.tif"

    matches = [
        name for name in z.namelist()
        if Path(name).name.lower() == filename.lower()
    ]

    if len(matches) != 1:
        raise ValueError(
            f"Expected one Hamburg source tile: {filename}"
        )

    memory = stack.enter_context(
        MemoryFile(z.read(matches[0]))
    )

    hh = stack.enter_context(memory.open())
    ni = stack.enter_context(rasterio.open(ni_file))

    for src in (hh, ni):
        assert src.crs.to_epsg() == 25832
        assert src.res == (1.0, 1.0)
        assert src.count == 1

    sources = [ni, hh]

    extent = unary_union([
        box(*src.bounds) for src in sources
    ])

    data, transform = merge(
        sources,
        bounds=(552000, 5924000, 554000, 5925000),
        res=(1, 1),
        nodata=-9999.0,
        method="first"
    )

elevation = data[0]

assert elevation.shape == (1000, 2000)

def check_ring(zone):
    """Return geometric and valid-pixel coverage."""

    geometric = (
        zone.intersection(extent).area / zone.area
    )

    inside = geometry_mask(
        [mapping(zone)],
        out_shape=elevation.shape,
        transform=transform,
        invert=True
    )

    valid = (
        inside
        & np.isfinite(elevation)
        & (elevation != -9999.0)
    )

    total = int(inside.sum())
    count = int(valid.sum())

    fraction = count / total if total else 0.0

    return geometric, fraction, count, total


records = []

for _, row in gdf.iterrows():

    geom = row.geometry

    if geom is None or geom.is_empty or not geom.is_valid:
        raise ValueError(f"Invalid geometry: {row.bldg_id}")

    local = geom.buffer(20).difference(geom)

    neighbourhood = (
        geom.buffer(100).difference(geom.buffer(20))
    )

    lg, lv, lc, lt = check_ring(local)
    ng, nv, nc, nt = check_ring(neighbourhood)

    passed = (
        lg >= 0.99
        and ng >= 0.99
        and lv >= 0.99
        and nv >= 0.99
        and lc >= 20
        and nc >= 20
    )

    records.append({
        "bldg_id": str(row.bldg_id),
        "local_geometric": lg,
        "local_valid_fraction": lv,
        "local_valid_pixels": lc,
        "local_total_pixels": lt,
        "neighbourhood_geometric": ng,
        "neighbourhood_valid_fraction": nv,
        "neighbourhood_valid_pixels": nc,
        "neighbourhood_total_pixels": nt,
        "passed": passed,
    })

df = pd.DataFrame(records)
df = df.sort_values("bldg_id")

output = output_dir / "ni_boundary_ring_qa_1m.csv"
df.to_csv(output, index=False)

print("\nBUILDING RESULTS")
print(
    df[
        [
            "bldg_id",
            "local_valid_fraction",
            "neighbourhood_valid_fraction",
            "passed"
        ]
    ].to_string(index=False)
)

print("\nSUMMARY")
print("Buildings tested:", len(df))
print("PASS:", int(df.passed.sum()))
print("FLAG:", int((~df.passed).sum()))

print("\nNiedersachsen source SHA-256:")

digest = sha256()
with ni_file.open("rb") as f:
    for chunk in iter(lambda: f.read(1024 * 1024), b""):
        digest.update(chunk)

print(digest.hexdigest())

print("\nOutput:", output)
print("BOUNDARY QA COMPLETE")
