"""Guard plotted evidence, unhidden invalid values, and regeneration state."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("readme_figures", ROOT / "scripts/generate_readme_figures.py")
figures = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(figures)


class TestReadmeFigures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "docs/figures/figure_data.json").read_text())

    def test_pressure_artists_show_nonphysical_values_without_clipping(self):
        with patch.object(figures, "save") as save:
            figures.fig_effectiveness_vs_pressure()
        fig = save.call_args.args[0]
        self.addCleanup(figures.plt.close, fig)
        xs, ys = fig.axes[0].lines[0].get_data()
        self.assertEqual(xs[-1], 0.20)
        self.assertAlmostEqual(ys[-1], 230.3163104927802)
        self.assertGreater(fig.axes[0].get_ylim()[1], max(ys))
        self.assertTrue(any("invalid counter-flow" in t.get_text() for t in fig.texts))

    def test_model_globals_restore_on_failure(self):
        saved = {k: getattr(figures.fsc, k) for k in figures.BASE_PARAMS}
        with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
            with figures.model_parameters(P=0.2, EDS_EFF=0.8):
                raise RuntimeError("synthetic failure")
        self.assertEqual(saved, {k: getattr(figures.fsc, k) for k in saved})

    def test_manifest_source_hashes_match_shipped_files(self):
        for relative, digest in self.manifest["sources_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest, relative)

    def test_manifest_sweeps_replay_live_model(self):
        pressure = self.manifest["pressure"]
        for p, eff, power in zip(pressure["pressure_bar"], pressure["legacy_output_percent"], pressure["legacy_blower_W"]):
            result = figures.evaluate_model(P=p)
            self.assertAlmostEqual(eff, 100 * result["overall_eff"])
            self.assertAlmostEqual(power, result["total_blower_W"])
        for sweep in self.manifest["sensitivity"].values():
            for x, y in zip(sweep["x"], sweep["legacy_output_percent"]):
                result = figures.evaluate_model(**{sweep["parameter"]: x})
                self.assertAlmostEqual(y, 100 * result["overall_eff"])
        self.assertFalse(self.manifest["stages"]["valid_counterflow"])

    def test_dem_manifest_matches_checkpoint_materials_and_steps(self):
        directory = ROOT / "sims/custom_gpu_dem/rung1_highn_checkpoints"
        for kind in ("with_iron", "no_iron"):
            for row in self.manifest["dem_height"][kind]:
                step = row[0]
                with np.load(directory / f"rung1_highn_{kind}_step{step:06d}.npz") as d:
                    self.assertEqual(int(d["step"]), step)
                    for index, mask in enumerate((d["mat"] == 0, d["mat"] != 0), start=1):
                        if index < len(row):
                            expected = d["pos"][mask, 2].astype(float).mean() * 1000
                            self.assertAlmostEqual(row[index], expected, places=4)

    def test_inventory_includes_loose_dumps_and_all_bytes(self):
        base = ROOT / "sims/custom_gpu_dem"
        files = list(base.glob("*checkpoints/*.npz")) + list(base.glob("*.npz"))
        inventory = self.manifest["inventory"]
        self.assertEqual(inventory["total_files"], len(files))
        self.assertEqual(len(files), 1467)
        self.assertAlmostEqual(inventory["total_MB"] * 1e6, sum(p.stat().st_size for p in files))
        self.assertIn("root dumps", [r[0] for r in inventory["rows"]])


if __name__ == "__main__":
    unittest.main()
