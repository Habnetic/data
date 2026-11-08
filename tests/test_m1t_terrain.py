"""Standalone synthetic raster tests for the M1-T terrain extractor."""
import importlib.util
from pathlib import Path

import numpy as np
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from shapely.geometry import box

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/m1t/extract_terrain.py"
spec = importlib.util.spec_from_file_location("habnetic_m1t_extract", str(SCRIPT))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_flat_raster_zero_relative_terrain():
    values = np.full((120, 120), 42.0, dtype="float32")
    with MemoryFile() as mem:
        with mem.open(
            driver="GTiff", width=120, height=120, count=1,
            dtype="float32", crs="EPSG:25830", transform=from_origin(0, 600, 5, 5),
            nodata=-9999.0,
        ) as dataset:
            dataset.write(values, 1)
            result = module.extract_building(dataset, "A", box(250, 250, 270, 270), box(*dataset.bounds))
            assert result["terrain_measured"]
            assert result["T50"] == 0.0
            assert result["T25"] == 0.0
            assert np.isclose(result["local_geometric_coverage"], 1.0)
            assert np.isclose(result["neighbourhood_geometric_coverage"], 1.0)


def test_edge_rejects_even_if_accessible_pixels_valid():
    values = np.full((120, 120), 42.0, dtype="float32")
    with MemoryFile() as mem:
        with mem.open(
            driver="GTiff", width=120, height=120, count=1,
            dtype="float32", crs="EPSG:25830", transform=from_origin(0, 600, 5, 5),
            nodata=-9999.0,
        ) as dataset:
            dataset.write(values, 1)
            result = module.extract_building(dataset, "B", box(250, 590, 270, 610), box(*dataset.bounds))
            assert not result["terrain_measured"]
            assert np.isnan(result["T50"])
            assert result["local_geometric_coverage"] < 0.99


def test_nodata_causes_failed_min_pixel_count():
    values = np.full((120, 120), -9999.0, dtype="float32")
    with MemoryFile() as mem:
        with mem.open(
            driver="GTiff", width=120, height=120, count=1,
            dtype="float32", crs="EPSG:25830", transform=from_origin(0, 600, 5, 5),
            nodata=-9999.0,
        ) as dataset:
            dataset.write(values, 1)
            result = module.extract_building(dataset, "C", box(250, 250, 270, 270), box(*dataset.bounds))
            assert not result["terrain_measured"]
            assert result["local_valid_pixels"] == 0
            assert np.isnan(result["T25"])


def test_rtm_compound_crs_is_accepted():
    values = np.full((120, 120), 42.0, dtype="float32")
    with MemoryFile() as mem:
        with mem.open(
            driver="GTiff", width=120, height=120, count=1,
            dtype="float32", crs="EPSG:7415", transform=from_origin(0, 600, 5, 5),
            nodata=-9999.0,
        ) as dataset:
            dataset.write(values, 1)
            assert dataset.crs.to_epsg() == 7415
            module.check_raster(dataset, module.CITY_CONFIG["RTM"])


def test_unrelated_crs_rejected_for_rotterdam():
    import pytest
    values = np.full((120, 120), 42.0, dtype="float32")
    with MemoryFile() as mem:
        with mem.open(
            driver="GTiff", width=120, height=120, count=1,
            dtype="float32", crs="EPSG:25830", transform=from_origin(0, 600, 5, 5),
            nodata=-9999.0,
        ) as dataset:
            dataset.write(values, 1)
            with pytest.raises(ValueError, match="Raster CRS mismatch"):
                module.check_raster(dataset, module.CITY_CONFIG["RTM"])


def test_don_crs_stays_strict():
    values = np.full((120, 120), 42.0, dtype="float32")
    with MemoryFile() as mem:
        with mem.open(
            driver="GTiff", width=120, height=120, count=1,
            dtype="float32", crs="EPSG:25830", transform=from_origin(0, 600, 5, 5),
            nodata=-9999.0,
        ) as dataset:
            dataset.write(values, 1)
            module.check_raster(dataset, module.CITY_CONFIG["DON"])
