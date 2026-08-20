#!/usr/bin/env python3
"""Gating test: current RCFX claims must match the shipped model and cited .npz.

Drives models/five_stage_counterflow.py (import + CLI) and np.load of the
primary physical-lid checkpoints. Fails if documented current numbers drift.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
HIGHN = ROOT / "sims" / "custom_gpu_dem" / "rung1_highn_checkpoints"
BOX_M = 0.018  # documented current containment domain

GOODVAR = HIGHN / "physical_drag_real_u3.5_iron1.5mm_step002000.npz"
NOIRON_400 = HIGHN / "rung1_highn_no_iron_step000400.npz"
IRON_1000 = HIGHN / "rung1_highn_with_iron_step001000.npz"
IRON_1300 = HIGHN / "rung1_highn_with_iron_step001300.npz"

MODEL_PATH = ROOT / "models" / "five_stage_counterflow.py"


def load_shipped_lumped():
    spec = importlib.util.spec_from_file_location("five_stage_counterflow", MODEL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load shipped model {MODEL_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_ckpt(path: Path):
    if not path.is_file():
        raise FileNotFoundError(path)
    return np.load(path)


def stats(path: Path) -> dict:
    d = load_ckpt(path)
    pos, mat = d["pos"], d["mat"]
    inside = (
        (pos[:, 0] >= 0)
        & (pos[:, 1] >= 0)
        & (pos[:, 2] >= 0)
        & (pos[:, 0] <= BOX_M)
        & (pos[:, 1] <= BOX_M)
    )
    reg = mat == 0
    iron = mat != 0
    return {
        "n": int(pos.shape[0]),
        "inside_frac": float(inside.mean()),
        "reg_z_mm": float(pos[reg, 2].mean() * 1e3),
        "iron_z_mm": float(pos[iron, 2].mean() * 1e3) if iron.any() else None,
        "zmax_mm": float(pos[:, 2].max() * 1e3),
    }


class TestCurrentClaims(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_shipped_lumped()
        cls.res = cls.model.run_5stage()
        cls.baseline_z = stats(NOIRON_400)["reg_z_mm"]

    def test_lumped_cli_prints_75p6_and_221w(self):
        out = subprocess.check_output(
            [sys.executable, str(MODEL_PATH)],
            cwd=str(ROOT),
            text=True,
        )
        self.assertIn("Overall effectiveness: 75.6%", out)
        self.assertIn("Estimated blower power: 221 W", out)
        self.assertNotIn("68 W", out)

    def test_lumped_run_5stage_matches_documented_plant(self):
        self.assertAlmostEqual(self.res["P_bar"], 0.14, places=2)
        self.assertAlmostEqual(self.res["overall_eff"] * 100.0, 75.6, places=1)
        self.assertEqual(round(self.res["total_blower_W"]), 221)
        self.assertAlmostEqual(self.res["recovered_kW"], 11.8, places=1)

    def test_cited_checkpoints_exist(self):
        for p in (GOODVAR, NOIRON_400, IRON_1000, IRON_1300):
            self.assertTrue(p.is_file(), f"missing cited checkpoint {p}")

    def test_containment_box_018(self):
        for p in (GOODVAR, NOIRON_400, IRON_1000, IRON_1300):
            s = stats(p)
            self.assertEqual(s["n"], 6500, p.name)
            self.assertAlmostEqual(s["inside_frac"], 1.0, places=6, msg=p.name)
            self.assertLess(s["zmax_mm"], 60.0, msg=p.name)

    def test_noiron_baseline_z(self):
        self.assertAlmostEqual(self.baseline_z, 3.23, places=2)

    def test_goodvar_emi_and_heights(self):
        s = stats(GOODVAR)
        emi = s["reg_z_mm"] / self.baseline_z
        self.assertAlmostEqual(s["reg_z_mm"], 11.56, places=2)
        self.assertAlmostEqual(s["iron_z_mm"], 34.47, places=2)
        self.assertAlmostEqual(emi, 3.58, places=2)

    def test_highn_emi_1000_and_1300(self):
        s1000 = stats(IRON_1000)
        s1300 = stats(IRON_1300)
        emi1000 = s1000["reg_z_mm"] / self.baseline_z
        emi1300 = s1300["reg_z_mm"] / self.baseline_z
        self.assertAlmostEqual(emi1000, 8.04, places=2)
        self.assertAlmostEqual(emi1300, 8.53, places=2)
        self.assertAlmostEqual(s1000["reg_z_mm"], 25.99, places=2)
        self.assertAlmostEqual(s1300["reg_z_mm"], 27.57, places=2)

    def test_exhibits_do_not_sell_stale_812_emi(self):
        files = (
            ROOT / "patent_evidence/2026-06-04/Exhibit_B_GPU_DEM_Iron_Agitation.md",
            ROOT / "patent_evidence/2026-06-04/COLD_CLAIMS_AND_MATH_REVIEW.md",
        )
        for path in files:
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"8\.12\s*[×xX]", msg=str(path))


if __name__ == "__main__":
    unittest.main()
