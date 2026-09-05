"""Regression checks for DEM figure evidence and center/sphere distinctions."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("audit_dem_figures", ROOT / "scripts/audit_dem_figures.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class TestDEMFigureAudit(unittest.TestCase):
    def test_center_containment_does_not_imply_whole_particle_containment(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "test_step000002.npz"
            np.savez(path, pos=[[0, 0.009, 0.01], [0.009, 0.009, 0.03]],
                     vel=np.zeros((2, 3)), radius=[0.0001, 0.00075], mat=[0, 1], step=2)
            result = audit.checkpoint_stats(path)
            self.assertEqual(result["center_inside_count"], 2)
            self.assertEqual(result["whole_sphere_inside_count"], 1)
            self.assertEqual(result["regolith"]["mean_center_z_mm"], 10)
            self.assertEqual(result["iron"]["diameter_range_mm"], [1.5, 1.5])

    def test_rejects_wrong_internal_step_and_nonfinite_positions(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "test_step000002.npz"
            arrays = dict(pos=np.ones((2, 3)), vel=np.zeros((2, 3)), radius=[0.001, 0.001], mat=[0, 1], step=3)
            np.savez(path, **arrays)
            with self.assertRaisesRegex(ValueError, "filename/internal step mismatch"):
                audit.checkpoint_stats(path)
            arrays["step"] = 2
            arrays["pos"][0, 0] = np.nan
            np.savez(path, **arrays)
            with self.assertRaisesRegex(ValueError, "nonfinite"):
                audit.checkpoint_stats(path)

    def test_committed_evidence_matches_archive_and_current_runner_sources(self):
        stored = json.loads((ROOT / "docs/figures/dem_validation.json").read_text())
        self.assertEqual(stored, audit.build_report(), "Regenerate with python3 scripts/audit_dem_figures.py")

    def test_cited_ratios_use_explicit_earlier_baseline_and_sampled_peak(self):
        report = audit.build_report()
        ratios = report["reference_ratios"]
        self.assertEqual(ratios["denominator_step"], 400)
        self.assertEqual(ratios["sampled_highn_peak_step"], 1300)
        self.assertAlmostEqual(ratios["goodvar_to_baseline"], 3.5784267679, places=8)
        self.assertEqual(max(r["step"] for r in report["series"]["highn_no_iron"]), 400)
        good = report["series"]["real_drag_filename_u3_5_iron1_5mm"][-1]
        self.assertEqual(good["center_inside_count"], 6500)
        self.assertEqual(good["whole_sphere_inside_count"], 6331)
        self.assertEqual(good["iron"]["count"], 455)


if __name__ == "__main__":
    unittest.main()
