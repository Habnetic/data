"""Fast routing checks for Hamburg's two validated raster regions."""
import importlib.util
from pathlib import Path
import unittest

import geopandas as gpd
from shapely.geometry import Point

MODULE = Path(__file__).resolve().parents[1] / "scripts/m1t/extract_ham_terrain_regions.py"
spec = importlib.util.spec_from_file_location("extract_ham_terrain_regions", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class RegionTests(unittest.TestCase):
    def test_mainland_and_western_route(self):
        self.assertEqual(mod.region_for_geometry(Point(555000, 5930000)), "mainland")
        self.assertEqual(mod.region_for_geometry(Point(463419, 5979456)), "western_islands")

    def test_unsupported_middle_x_rejected(self):
        with self.assertRaises(ValueError):
            mod.region_for_geometry(Point(520000, 5930000))

    def test_mainland_pilot_preserves_order(self):
        frame = gpd.GeoDataFrame({"bldg_id": ["1", "10", "11", "12"]},
                                 geometry=[Point(463400, 5979000), Point(553000, 5924000),
                                           Point(554000, 5924000), Point(555000, 5924000)],
                                 crs="EPSG:25832")
        result = mod.select_buildings(frame, "pilot-mainland", 2)
        self.assertEqual(result.bldg_id.tolist(), ["10", "11"])

    def test_western_pilot_includes_control_building(self):
        frame = gpd.GeoDataFrame({"bldg_id": ["2", "3", "1", "10"]},
                                 geometry=[Point(466000, 5974000), Point(467000, 5974000),
                                           Point(463400, 5979000), Point(555000, 5924000)],
                                 crs="EPSG:25832")
        result = mod.select_buildings(frame, "pilot-western", 2)
        self.assertEqual(set(result.bldg_id), {"2", "1"})


if __name__ == "__main__":
    unittest.main()
