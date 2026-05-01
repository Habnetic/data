import fiona
from pathlib import Path

files = [
    Path("processed/DON/derived/hydrography_don.gpkg"),
    Path("raw/DON/buildings/pais_vasco.gpkg"),
]

for f in files:
    print("\n" + str(f))
    print(fiona.listlayers(f))