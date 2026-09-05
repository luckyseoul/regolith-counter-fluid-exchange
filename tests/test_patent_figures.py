"""Regression gates for the discovered unit and material-label errors."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "patent_drawings" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


snapshots = load("audited_patent", "generate_audited_figures.py")
progression = load("patent_progression", "generate_fig07_rung5_progression.py")
overview = load("system_overview", "generate_fig01_system_overview.py")


class TestPatentFigures(unittest.TestCase):
    def test_rung5_metres_are_not_labelled_millimetres(self):
        with patch.object(snapshots, "save") as save:
            snapshots.snapshot(5, 500000, "unused", 3)
        fig = save.call_args.args[0]
        self.addCleanup(snapshots.plt.close, fig)
        ax = fig.axes[0]
        self.assertEqual(ax.get_ylabel(), "Particle center z (m)")
        with np.load(ROOT / "sims/custom_gpu_dem/rung5_checkpoints/rung5_step500000.npz") as data:
            for collection, material in zip(ax.collections, [0, 1]):
                np.testing.assert_allclose(collection.get_offsets()[:, 1], data["pos"][data["mat"] == material, 2])
        self.assertGreater(max(c.get_offsets()[:, 1].max() for c in ax.collections), 22)

    def test_progression_legend_matches_checkpoint_materials(self):
        captured = []
        def capture(fig, *args, **kwargs):
            captured.append(fig)
        with patch("matplotlib.figure.Figure.savefig", new=capture):
            progression.main()
        ax = captured[0].axes[0]
        lines = {line.get_label(): line for line in ax.lines}
        with np.load(ROOT / "sims/custom_gpu_dem/rung5_checkpoints/rung5_step500000.npz") as data:
            for label, material in [("Regolith mean z", 0), ("Iron mean z", 1)]:
                expected = data["pos"][data["mat"] == material, 2].astype(float).mean() * 1000
                self.assertAlmostEqual(lines[label].get_ydata()[-1], expected, places=2)
                self.assertEqual(lines[label].get_xdata()[-1], 500)
        self.assertGreater(lines["Iron mean z"].get_ydata()[-1], lines["Regolith mean z"].get_ydata()[-1])


class TestSystemOverview(unittest.TestCase):
    def setUp(self):
        self.fig = overview.build_figure()
        self.addCleanup(overview.plt.close, self.fig)
        self.ax = self.fig.axes[0]

    def test_regolith_streams_have_opposite_correct_directions(self):
        for prefix, sign in [("cold-transfer-", 1), ("hot-transfer-", -1)]:
            arrows = [p for p in self.ax.patches if (p.get_gid() or "").startswith(prefix)]
            self.assertEqual(len(arrows), 6)  # inlet, four interstage transfers, outlet
            for arrow in arrows:
                vertices = arrow.get_path().vertices
                self.assertGreater(sign * (vertices[2, 0] - vertices[0, 0]), 0)
                self.assertAlmostEqual(vertices[2, 1], vertices[0, 1])
        text = " ".join(t.get_text() for t in self.ax.texts)
        self.assertIn("HOT SPENT", text)
        self.assertIn("COLD FEED", text)
        self.assertNotIn("Iron/heat", text)

    def test_gas_branches_share_manifolds_in_parallel(self):
        for prefix in ("gas-supply-stage-", "gas-return-stage-"):
            arrows = [p for p in self.ax.patches if (p.get_gid() or "").startswith(prefix)]
            self.assertEqual(len(arrows), 5)
            starts = [p.get_path().vertices[0] for p in arrows]
            ends = [p.get_path().vertices[2] for p in arrows]
            self.assertEqual(len({round(float(p[0]), 6) for p in starts}), 5)
            self.assertEqual(len({round(float(p[1]), 6) for p in starts}), 1)
            self.assertEqual(len({round(float(p[1]), 6) for p in ends}), 1)
            for start, end in zip(starts, ends):
                self.assertAlmostEqual(start[0], end[0])
                self.assertGreater(end[1], start[1])
        text = " ".join(t.get_text() for t in self.ax.texts)
        self.assertIn("The same five stages, connected in parallel", text)
        self.assertIn("+ standby backup", text)

    def test_current_and_bundle_fig1_artifacts_are_identical(self):
        for extension in ("svg", "pdf"):
            name = f"FIG_01_system_overview.{extension}"
            self.assertEqual((ROOT / "patent_drawings" / name).read_bytes(),
                             (ROOT / "patent_application/2026-06-05/patent_drawings" / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
