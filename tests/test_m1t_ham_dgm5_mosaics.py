"""Synthetic integration tests for Hamburg 5m mosaic builder. Run as a script."""

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "m1t"))
from build_ham_dgm5_mosaics import build_region, filenames, inspect_tiles, region_bounds


def write_tile(root, name, x, y, provenance, elevation=15.0, frac=1.0):
    folder = root / "test_tiles"
    folder.mkdir(exist_ok=True)
    ep = folder / (name + ".tif")
    fp = folder / (name + "_valid_fraction.tif")
    prof = dict(driver="GTiff", width=200, height=200, count=1,
                crs="EPSG:25832", transform=from_origin(x, y+1000, 5, 5),
                dtype="float32", nodata=-9999.0)
    z = np.full((200, 200), elevation, dtype="float32")
    f = np.full((200, 200), frac, dtype="float32")
    if frac < 1:
        z[:] = -9999.0
    with rasterio.open(ep, "w", **prof) as dst:
        dst.write(z, 1)
    prof["nodata"] = None
    with rasterio.open(fp, "w", **prof) as dst:
        dst.write(f, 1)
    return dict(elevation_path=ep.relative_to(root).as_posix(),
                fraction_path=fp.relative_to(root).as_posix(), source=provenance)


class MosaicTests(unittest.TestCase):
    def test_split_and_validity_and_gap(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            entries = [
                write_tile(root, "hh_a", 555000, 5938000, "LGV_HH_2022", 10.0),
                write_tile(root, "sh_b", 555000, 5939000, "LVERMGEO_SH_2021", 15.0),
                write_tile(root, "hh_c", 557000, 5938000, "LGV_HH_2022", 50.0, 0.5),
                write_tile(root, "wsv", 463000, 5979000, "WSV_DGMW_2022_SCHARHOERN", 3.0),
            ]
            groups = inspect_tiles(root, entries)
            self.assertEqual(len(groups["mainland"]), 3)
            self.assertEqual(len(groups["western_islands"]), 1)
            self.assertEqual(region_bounds(groups["mainland"]),
                             (555000, 5938000, 558000, 5940000))
            outputs = filenames(root / "derived", "mainland")
            report = build_region(groups["mainland"], outputs)
            self.assertEqual(report["tile_count"], 3)
            with rasterio.open(outputs["elevation"]) as elev, rasterio.open(
                    outputs["source_id"]) as sources, rasterio.open(
                    outputs["valid_fraction"]) as fraction:
                a = elev.read(1)
                s = sources.read(1)
                f = fraction.read(1)
                self.assertEqual(a.shape, (400, 600))
                self.assertTrue(np.all(a[200:400, 0:200] == 10.0))
                self.assertTrue(np.all(a[0:200, 0:200] == 15.0))
                self.assertTrue(np.all(a[:, 200:400] == -9999.0))
                self.assertTrue(np.all(s[:, 200:400] == 0))
                self.assertTrue(np.all(s[200:400, 400:600] == 1))
                self.assertTrue(np.all(f[200:400, 400:600] == 0.5))
                self.assertTrue(np.all(a[200:400, 400:600] == -9999.0))
            west = filenames(root / "derived", "western_islands")
            w_report = build_region(groups["western_islands"], west)
            self.assertEqual(w_report["valid_elevation_cells"],
                             {"WSV_DGMW_2022_SCHARHOERN": 40000})

    def test_overlap_fill_invalid_primary_and_preserve_valid_primary(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            hh = write_tile(root, "hh", 555000, 5939000, "LGV_HH_2022", 10.0)
            sh = write_tile(root, "sh", 555000, 5939000, "LVERMGEO_SH_2021", 17.0)
            # Primary LGV is valid in first half; second half is nodata.
            with rasterio.open(root / hh["elevation_path"], "r+") as dst:
                data = dst.read(1)
                data[100:, :] = -9999
                dst.write(data, 1)
            with rasterio.open(root / hh["fraction_path"], "r+") as dst:
                f = dst.read(1)
                f[100:, :] = 0.0
                dst.write(f, 1)
            west = write_tile(root, "west", 463000, 5979000,
                              "WSV_DGMW_2022_SCHARHOERN", 3.0)
            groups = inspect_tiles(root, [hh, sh, west])
            report = build_region(groups["mainland"], filenames(root / "out", "mainland"))
            self.assertEqual(report["overlapping_footprints"], 1)
            self.assertEqual(report["unique_footprints"], 1)
            self.assertEqual(report["source_cells"], {"LGV_HH_2022": 20000,
                                                       "LVERMGEO_SH_2021": 20000})
            self.assertEqual(report["overlap_resolution"][0]["supplementary_valid_cells_used"], 20000)
            with rasterio.open(root / "out" / "ham_dgm5_mainland_mosaic.tif") as dst:
                array = dst.read(1)
                self.assertTrue(np.all(array[:100, :] == 10.0))
                self.assertTrue(np.all(array[100:, :] == 17.0))
            with rasterio.open(root / "out" / "ham_dgm5_mainland_mosaic_source_id.tif") as dst:
                sources = dst.read(1)
                self.assertTrue(np.all(sources[:100, :] == 1))
                self.assertTrue(np.all(sources[100:, :] == 2))

    def test_overlap_rejects_duplicate_same_source(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            entries = [
                write_tile(root, "a", 555000, 5938000, "LGV_HH_2022"),
                write_tile(root, "b", 555000, 5938000, "LGV_HH_2022"),
            ]
            with self.assertRaisesRegex(ValueError, "Duplicate same-source"):
                inspect_tiles(root, entries)

    def test_overlap_rejects_unapproved_source_combination(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            entries = [
                write_tile(root, "a", 555000, 5938000, "LVERMGEO_SH_2021"),
                write_tile(root, "b", 555000, 5938000, "LGLN_NI_2025"),
            ]
            with self.assertRaisesRegex(ValueError, "Unapproved overlapping"):
                inspect_tiles(root, entries)

    def test_unsupported_source_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            entry = write_tile(root, "a", 555000, 5938000, "LGV_HH_2022")
            entry["source"] = "UNIDENTIFIED"
            with self.assertRaisesRegex(ValueError, "Unknown source"):
                inspect_tiles(root, [entry])

    def test_non_strict_cell_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            entry = write_tile(root, "a", 555000, 5938000, "LGV_HH_2022")
            frac_path = root / entry["fraction_path"]
            with rasterio.open(frac_path, "r+") as dst:
                data = dst.read(1)
                data[0, 0] = 0.96
                dst.write(data, 1)
            entry2 = write_tile(root, "west", 463000, 5979000,
                                "WSV_DGMW_2022_SCHARHOERN")
            groups = inspect_tiles(root, [entry, entry2])
            with self.assertRaisesRegex(ValueError, "Strict aggregation"):
                build_region(groups["mainland"],
                             filenames(root / "out", "mainland"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
