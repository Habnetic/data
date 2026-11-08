"""Unit tests for numerical QA and review-candidate selection (Python 3.8+)."""
import importlib.util
from pathlib import Path
import sys
import unittest
import tempfile
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd

MODULE = Path(__file__).resolve().parents[1] / "scripts/m1t/qa_ham_citywide.py"
spec = importlib.util.spec_from_file_location("qa_ham_citywide", str(MODULE))
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)


def example():
    return pd.DataFrame({
        "bldg_id": ["1", "2", "3"],
        "terrain_region": ["mainland", "mainland", "western_islands"],
        "terrain_measured": [True] * 3,
        "local_z_50": [5., 6., 25.],
        "neighbourhood_z_50": [4., 6., 4.],
        "neighbourhood_z_25": [3., 5., 2.],
        "T50": [1., 0., 21.], "T25": [2., 1., 23.],
        "local_valid_pixels": [24, 25, 20],
        "local_total_pixels": [25, 25, 25],
        "local_coverage": [24/25, 1., 20/25],
        "neighbourhood_valid_pixels": [40, 40, 40],
        "neighbourhood_total_pixels": [40, 40, 40],
        "neighbourhood_coverage": [1., 1., 1.],
        "local_geometric_coverage": [1., 1., 1.],
        "neighbourhood_geometric_coverage": [1., 1., 1.],
    })


class TestCitywideQA(unittest.TestCase):
    def test_valid_numerics_are_consistent_without_100pct_pixels(self):
        result = qa.numerical_checks(example(), population=3)
        self.assertEqual(result["measured"], 3)
        self.assertEqual(result["valid_pixel_fraction"]["local"]["below_0_99"], 2)

    def test_wrong_t50_rejected(self):
        data = example()
        data.loc[0, "T50"] = 9
        with self.assertRaisesRegex(ValueError, "T50 formula"):
            qa.numerical_checks(data, population=3)

    def test_pixel_coverage_inconsistent_rejected(self):
        data = example()
        data.loc[0, "local_coverage"] = 1.
        with self.assertRaisesRegex(ValueError, "Pixel coverage mismatch"):
            qa.numerical_checks(data, population=3)

    def test_insufficient_measured_pixels_rejected(self):
        data = example()
        data.loc[0, "local_valid_pixels"] = 19
        data.loc[0, "local_coverage"] = 19/25
        with self.assertRaisesRegex(ValueError, "minimum valid-pixel"):
            qa.numerical_checks(data, population=3)

    def test_candidate_flags_are_diagnostic_not_rejections(self):
        result = qa.spatial_candidates(example(), top_n=1)
        row = result.loc[result.bldg_id == "3"].iloc[0]
        self.assertIn("T50_ge_8.0m", row.qa_reason)
        self.assertEqual(row.qa_status, "PENDING_MANUAL_REVIEW")

    def test_spatial_export_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            buildings = gpd.GeoDataFrame(
                {"bldg_id": ["1", "2", "3"]},
                geometry=[Point(0, 0), Point(5, 5), Point(10, 10)],
                crs="EPSG:25832",
            )
            path = root / "test_buildings.gpkg"
            buildings.to_file(str(path), driver="GPKG")
            candidates = qa.spatial_candidates(example(), top_n=1)
            qa.export_spatial_review(candidates, path, root / "qa",
                                     expected_ids=example().bldg_id, expected_population=3)
            output = gpd.read_file(root / "qa/ham_m1t_spatial_review.gpkg")
            self.assertEqual(len(output), len(candidates))
            self.assertEqual(set(output.bldg_id.astype(str)), set(candidates.bldg_id))

    def test_t25_below_t50_rejected(self):
        data = example()
        data.loc[0, "neighbourhood_z_25"] = 5
        data.loc[0, "T25"] = 0
        with self.assertRaisesRegex(ValueError, "T25 < T50"):
            qa.numerical_checks(data, population=3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
