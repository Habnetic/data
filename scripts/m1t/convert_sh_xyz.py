from pathlib import Path
from zipfile import ZipFile
from hashlib import sha256
import json

import numpy as np
import rasterio
from rasterio.transform import from_origin

root = Path("../data").resolve()

source_dir = root / "raw/HAM/terrain/lvermgeo_sh"
output_dir = root / "processed/HAM/derived/dgm1_sh_1m"
manifest_dir = root / "runs/ham_m1_citywide/qa"

output_dir.mkdir(parents=True, exist_ok=True)
manifest_dir.mkdir(parents=True, exist_ok=True)

sources = [
    {
        "zip": "Mehrfachdownload_nY2H30_FnpEbr.zip",
        "tile": "dgm1_32_555_5939_1_sh_2021.xyz",
        "sha256": "907B0A0A9C297CBBCE2B69533F0822A7FA9746F96B20C5B745D06CF92A3B8E83",
        "x": 555000,
        "y": 5939000,
    },
    {
        "zip": "Mehrfachdownload_3S6dxh_eZFhh0.zip",
        "tile": "dgm1_32_556_5939_1_sh_2021.xyz",
        "sha256": "174CB0C6D6B771D559BBBCFF2C9FE6ECA82BFD469CE9D92E12A4EB6F232E5298",
        "x": 556000,
        "y": 5939000,
    },
]

def file_hash(path):
    digest = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

records = []

for source in sources:

    archive = source_dir / source["zip"]

    if file_hash(archive).upper() != source["sha256"]:
        raise ValueError(f"Archive checksum mismatch: {archive.name}")

    with ZipFile(archive) as z:

        if z.testzip() is not None:
            raise ValueError(f"Invalid ZIP: {archive.name}")

        with z.open(source["tile"]) as f:
            xyz = np.loadtxt(f, dtype=np.float64)

    if xyz.shape != (1000000, 3):
        raise ValueError(
            f"Unexpected XYZ dimensions: {xyz.shape}"
        )

    # Verify every pixel centre, not just the first records.
    index = np.arange(1000000)

    expected_x = source["x"] + 0.5 + (index % 1000)
    expected_y = source["y"] + 999.5 - (index // 1000)

    if not np.allclose(
        xyz[:, 0], expected_x, atol=0.001, rtol=0
    ):
        raise ValueError("X coordinate grid mismatch")

    if not np.allclose(
        xyz[:, 1], expected_y, atol=0.001, rtol=0
    ):
        raise ValueError("Y coordinate grid mismatch")

    values = xyz[:, 2]

    # Conservative screening for invalid or sentinel elevations.
    invalid = (
        ~np.isfinite(values)
        | (values < -1000)
        | (values > 1000)
    )

    if invalid.any():
        raise ValueError(
            f"{source['tile']}: "
            f"{int(invalid.sum())} suspicious elevations. "
            "Inspect source values before conversion."
        )

    raster = values.reshape(1000, 1000).astype("float32")

    output = output_dir / source["tile"].replace(".xyz", ".tif")

    transform = from_origin(
        source["x"],
        source["y"] + 1000,
        1,
        1
    )

    with rasterio.open(
        output,
        "w",
        driver="GTiff",
        height=1000,
        width=1000,
        count=1,
        dtype="float32",
        crs="EPSG:25832",
        transform=transform,
        nodata=-9999.0,
        compress="deflate",
        predictor=3,
        tiled=True,
        blockxsize=256,
        blockysize=256,
    ) as dst:
        dst.write(raster, 1)

    # Verify the written raster.
    with rasterio.open(output) as check:

        assert check.crs.to_epsg() == 25832
        assert check.res == (1.0, 1.0)
        assert np.array_equal(check.read(1), raster)

    record = {
        "source_archive": source["zip"],
        "source_sha256": source["sha256"],
        "source_member": source["tile"],
        "output": output.relative_to(root).as_posix(),
        "output_sha256": file_hash(output),
        "pixel_count": 1000000,
        "resolution_m": 1,
        "crs": "EPSG:25832",
        "min_elevation": float(values.min()),
        "max_elevation": float(values.max()),
        "status": "PASS",
    }

    records.append(record)

    print("\nTILE:", source["tile"])
    print("Elevation range:", record["min_elevation"],
          "to", record["max_elevation"])
    print("Output:", output)
    print("QA: PASS")

manifest = manifest_dir / "sh_dgm1_conversion_manifest.json"

manifest.write_text(
    json.dumps(
        {
            "city": "HAM",
            "phase": "M1-T",
            "source": "Schleswig-Holstein DGM1 2021",
            "conversion": "XYZ pixel centres to 1 m GeoTIFF",
            "records": records,
        },
        indent=2
    ) + "\n",
    encoding="utf-8"
)

print("\nSCHLESWIG-HOLSTEIN CONVERSION: PASS")
print("Tiles:", len(records))
print("Manifest:", manifest)
