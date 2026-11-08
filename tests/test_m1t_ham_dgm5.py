"""Synthetic and georeferencing checks for Hamburg's 5 m terrain preparation."""
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "m1t"))
from prepare_ham_dgm5 import aggregate_5m, convert_source


class AggregateTests(unittest.TestCase):
    def test_all_valid_and_grid_averaging(self):
        source = np.arange(100, dtype="float32").reshape(10, 10)
        out, fractions = aggregate_5m(source)
        self.assertEqual(out.shape, (2, 2))
        self.assertAlmostEqual(out[0, 0], float(source[:5, :5].mean()))
        self.assertAlmostEqual(out[1, 1], float(source[5:, 5:].mean()))
        self.assertTrue(np.all(fractions == 1.0))

    def test_unmasked_minus_9999_never_enters_mean(self):
        source = np.full((5, 5), 15.0, dtype="float32")
        source[0, 0] = -9999.0
        strict, fraction = aggregate_5m(source)
        self.assertEqual(float(strict[0, 0]), -9999.0)
        self.assertAlmostEqual(float(fraction[0, 0]), 24 / 25)
        relaxed, fraction = aggregate_5m(source, minimum_valid_fraction=0.96)
        self.assertEqual(float(relaxed[0, 0]), 15.0)

    def test_declared_nodata_mask_honoured(self):
        source = np.ma.array(np.full((5, 5), 20.0), mask=False)
        source[1, 2] = np.ma.masked
        out, fraction = aggregate_5m(source)
        self.assertEqual(float(out[0, 0]), -9999.0)
        self.assertAlmostEqual(float(fraction[0, 0]), 0.96)

    def test_all_invalid(self):
        out, fraction = aggregate_5m(np.full((5, 5), -9999.0))
        self.assertEqual(float(out[0, 0]), -9999.0)
        self.assertEqual(float(fraction[0, 0]), 0.0)

    def test_bad_block_shape_rejected(self):
        with self.assertRaises(ValueError):
            aggregate_5m(np.zeros((9, 10)))

    def test_real_raster_io_alignment_and_sentinel(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            native = temp / "native.tif"
            derived = temp / "derived.tif"
            data = np.full((10, 10), 15.0, dtype="float32")
            data[0, 0] = -9999.0  # Source *declares different* nodata.
            data[5:, 5:] = 42.0
            with rasterio.open(
                native, "w", driver="GTiff", width=10, height=10,
                count=1, dtype="float32", crs="EPSG:25832",
                transform=from_origin(555000, 5939000, 1, 1),
                nodata=-3.4028234663852886e38,
            ) as dst:
                dst.write(data, 1)
            with rasterio.open(native) as src:
                stats = convert_source(src, derived, 1.0, chunk_rows=5)
            with rasterio.open(derived) as result:
                out = result.read(1, masked=True)
                self.assertEqual(result.res, (5, 5))
                self.assertEqual(tuple(result.bounds),
                                 (555000, 5938990, 555010, 5939000))
                self.assertTrue(np.ma.getmaskarray(out)[0, 0])
                self.assertEqual(float(out[1, 1]), 42)
            with rasterio.open(
                temp / "derived_valid_fraction.tif") as result:
                frac = result.read(1)
                self.assertAlmostEqual(float(frac[0, 0]), 0.96)
            self.assertEqual(stats["unmasked_minus_9999_pixels"], 1)
            self.assertEqual(stats["accepted_5m_cells"], 3)


if __name__ == "__main__":
    unittest.main()
