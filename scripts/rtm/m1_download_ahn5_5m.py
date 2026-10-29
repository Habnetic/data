"""
Habnetic | Phase 4 M1-P04a
Download and validate AHN5 5 m terrain tiles for Rotterdam.

Input:
    runs/rtm_m1_citywide/ahn5_5m_tile_manifest_buffered.csv

Output:
    raw/RTM/terrain/ahn/ahn5_dtm_5m/*.TIF
    runs/rtm_m1_citywide/ahn5_5m_download_inventory.csv

Run:
    python scripts/rtm/m1_download_ahn5_5m.py

Existing valid files are reused. Downloads use temporary files
and are validated before being moved to their final location.
"""

import csv
import hashlib
import logging
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import rasterio
from pyproj import CRS


ROOT = Path(__file__).resolve().parents[2]

MANIFEST = (
    ROOT
    / "runs/rtm_m1_citywide/ahn5_5m_tile_manifest_buffered.csv"
)

DOWNLOAD_DIR = (
    ROOT
    / "raw/RTM/terrain/ahn/ahn5_dtm_5m"
)

INVENTORY = (
    ROOT
    / "runs/rtm_m1_citywide/ahn5_5m_download_inventory.csv"
)

CHUNK_SIZE = 1024 * 1024
MAX_ATTEMPTS = 3


def sha256_file(path: Path) -> str:
    """Calculate SHA256 without loading the file into memory."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        while True:
            chunk = file.read(CHUNK_SIZE)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def validate_raster(path: Path) -> dict:
    """Validate raster metadata and return an inventory record."""

    with rasterio.open(path) as src:

        crs = CRS.from_user_input(src.crs)

        horizontal = (
            crs.sub_crs_list[0]
            if crs.is_compound
            else crs
        )

        if horizontal.to_epsg() != 28992:
            raise ValueError(
                f"Unexpected horizontal CRS: {src.crs}"
            )

        if src.res != (5.0, 5.0):
            raise ValueError(
                f"Unexpected resolution: {src.res}"
            )

        if src.count != 1:
            raise ValueError(
                f"Unexpected band count: {src.count}"
            )

        if src.width <= 0 or src.height <= 0:
            raise ValueError("Invalid raster dimensions")

        return {
            "crs": str(src.crs),
            "width": src.width,
            "height": src.height,
            "resolution_m": src.res[0],
            "nodata": src.nodata,
            "bounds": str(tuple(src.bounds)),
        }


def download_file(url: str, destination: Path) -> None:
    """Download a file atomically with retry handling."""

    temporary = destination.with_name(
        destination.name + ".part"
    )

    for attempt in range(1, MAX_ATTEMPTS + 1):

        try:
            if temporary.exists():
                temporary.unlink()

            request = Request(
                url,
                headers={"User-Agent": "Habnetic-Research/1.0"},
            )

            with urlopen(request, timeout=90) as response:
                with temporary.open("wb") as output:

                    while True:
                        chunk = response.read(CHUNK_SIZE)

                        if not chunk:
                            break

                        output.write(chunk)

            if temporary.stat().st_size == 0:
                raise ValueError("Downloaded file is empty")

            # Validate before making the download permanent.
            validate_raster(temporary)

            temporary.replace(destination)

            return

        except Exception as exc:

            logging.warning(
                "Attempt %s/%s failed: %s",
                attempt,
                MAX_ATTEMPTS,
                exc,
            )

            if temporary.exists():
                temporary.unlink()

            if attempt == MAX_ATTEMPTS:
                raise

            time.sleep(2 * attempt)


def save_inventory(records: list) -> None:
    """Save the current download inventory."""

    if not records:
        return

    INVENTORY.parent.mkdir(parents=True, exist_ok=True)

    with INVENTORY.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "filename",
                "year",
                "url",
                "status",
                "size_mb",
                "sha256",
                "crs",
                "width",
                "height",
                "resolution_m",
                "nodata",
                "bounds",
                "error",
            ],
        )

        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    """Download all terrain tiles from the buffered manifest."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    DOWNLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with MANIFEST.open(
        newline="",
        encoding="utf-8-sig",
    ) as file:
        manifest = list(csv.DictReader(file))

    filenames = [row["filename"] for row in manifest]

    if len(filenames) != len(set(filenames)):
        raise ValueError("Manifest contains duplicate filenames")

    print("\n=== HABNETIC M1-P04a ===")
    print("AHN5 5 m terrain acquisition")
    print("============================")
    print("Tiles in manifest:", len(manifest))

    inventory = []
    failures = 0

    for index, row in enumerate(manifest, start=1):

        filename = row["filename"]
        url = row["url"]
        destination = DOWNLOAD_DIR / filename

        logging.info(
            "[%s/%s] %s",
            index,
            len(manifest),
            filename,
        )

        record = {
            "filename": filename,
            "year": row["year"],
            "url": url,
            "status": "",
            "size_mb": "",
            "sha256": "",
            "crs": "",
            "width": "",
            "height": "",
            "resolution_m": "",
            "nodata": "",
            "bounds": "",
            "error": "",
        }

        try:
            url_filename = Path(urlparse(url).path).name

            if url_filename != filename:
                raise ValueError(
                    "Manifest filename does not match URL"
                )

            if destination.exists():
                metadata = validate_raster(destination)
                status = "reused"
            else:
                download_file(url, destination)
                metadata = validate_raster(destination)
                status = "downloaded"

            record.update(metadata)

            record["status"] = status

            record["size_mb"] = round(
                destination.stat().st_size / (1024 ** 2),
                3,
            )

            record["sha256"] = sha256_file(destination)

            logging.info(
                "%s | %.2f MB",
                status.upper(),
                record["size_mb"],
            )

        except Exception as exc:

            failures += 1

            record["status"] = "failed"
            record["error"] = str(exc)

            logging.error(
                "FAILED | %s | %s",
                filename,
                exc,
            )

        inventory.append(record)

        # Preserve progress after every tile.
        save_inventory(inventory)

    print("\n=== ACQUISITION SUMMARY ===")

    print("Required:", len(manifest))
    print(
        "Downloaded:",
        sum(r["status"] == "downloaded" for r in inventory),
    )
    print(
        "Reused:",
        sum(r["status"] == "reused" for r in inventory),
    )
    print("Failed:", failures)

    print("\nInventory:")
    print(INVENTORY)

    if failures:
        raise SystemExit(
            f"Acquisition incomplete: {failures} failed tiles"
        )


if __name__ == "__main__":
    main()