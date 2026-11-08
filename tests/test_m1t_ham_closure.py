"""Small deterministic unit tests for Hamburg M1-T closure checks."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/m1t/finalize_ham_m1t.py"
spec = importlib.util.spec_from_file_location("ham_closure", str(SCRIPT))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ClosureChecks(unittest.TestCase):
    def make_metadata(self):
        summary = {"minimum": 1.0, "below_0_99": 0}
        numeric = {
            "city": "HAM", "phase": "M1-T", "all_numeric_checks_pass": True,
            "batch_hashes_verified": True, "rows": 341530, "measured": 341530,
            "missing": 0, "region_counts": module.EXPECTED_REGIONS,
            "spatial_candidates": 398,
            "valid_pixel_fraction": {"local": summary, "neighbourhood":
                                    {"minimum": .993377, "below_0_99": 0}},
        }
        extraction = {"city": "HAM", "mode": "all", "population": 341530,
                      "selected_buildings": 341530,
                      "outputs": [{"count": 1000}] * 341 + [{"count": 530}],
                      "rasters": {"mainland": {}, "western_islands": {}}}
        diagnostic = {"status": "DIAGNOSTIC_ONLY_NOT_SPATIAL_VALIDATION",
                      "buildings": {"8629": {"neighbourhood_p25_m": 8.6014,
                                             "lower_quartile_pixel_count": 300},
                                    "304428": {"neighbourhood_valid_fraction": .993377,
                                               "neighbourhood_invalid_pixels": 12}}}
        candidate_rows = []
        for k in range(398):
            x = str(k) if k >= 6 else list(sorted(module.REVIEW_IDS))[k]
            candidate_rows.append({"bldg_id": x, "T50": 0.0, "T25": 0.0})
        register = [dict(bldg_id=k, T50_m=0.0, T25_m=0.0,
                         evidence_files="HAM_8937_OSM.png") for k in sorted(module.REVIEW_IDS)]
        return numeric, extraction, diagnostic, candidate_rows, register

    def test_valid_synthetic_reports_pass(self):
        q, e, d, c, r = self.make_metadata()
        report = module.validate_reports(q, e, d, c, r)
        self.assertEqual(report["measured"], 341530)
        self.assertEqual(report["unreviewed_count"], 392)

    def test_fails_unmeasured(self):
        q, e, d, c, r = self.make_metadata()
        q["measured"] = 341529
        with self.assertRaisesRegex(ValueError, "Population/measurement"):
            module.validate_reports(q, e, d, c, r)

    def test_fails_wrong_quartile(self):
        q, e, d, c, r = self.make_metadata()
        d["buildings"]["8629"]["neighbourhood_p25_m"] = 34
        with self.assertRaisesRegex(ValueError, "8629 low quartile"):
            module.validate_reports(q, e, d, c, r)

    def test_fails_untested_coverage(self):
        q, e, d, c, r = self.make_metadata()
        q["valid_pixel_fraction"]["neighbourhood"]["minimum"] = .97
        with self.assertRaisesRegex(ValueError, "Valid coverage"):
            module.validate_reports(q, e, d, c, r)

    def test_sha256_known_string(self):
        from hashlib import sha256
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "text"
            path.write_bytes(b"habnetic test")
            self.assertEqual(module.file_hash(path), sha256(b"habnetic test").hexdigest())


if __name__ == "__main__":
    unittest.main(verbosity=2)
