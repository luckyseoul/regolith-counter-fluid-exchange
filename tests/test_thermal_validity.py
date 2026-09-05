"""Physical-consistency diagnostics for the unrepaired legacy recurrence."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "models/five_stage_counterflow.py"
SPEC = importlib.util.spec_from_file_location("thermal_validity_model", MODEL)
model = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(model)


class TestThermalValidity(unittest.TestCase):
    def test_default_replay_preserves_arithmetic_but_rejects_interpretation(self):
        result = model.run_5stage()
        self.assertAlmostEqual(result["overall_eff"], 0.755922660639789)
        self.assertFalse(result["valid_counterflow"])
        self.assertEqual(result["validity"]["negative_heat_stages"], [2, 4])
        self.assertEqual(result["validity"]["reversed_inlet_stages"], [2, 4])
        self.assertEqual(result["validity"]["stage_effectiveness_out_of_bounds"], [])

    def test_trace_exposes_energy_balance_and_same_direction_propagation(self):
        result = model.run_5stage()
        trace = result["stage_trace"]
        self.assertEqual(len(trace), 5)
        capacity = 100 / 3600 * model.CP_REG
        for row in trace:
            self.assertAlmostEqual(row["cold_in_K"] + row["hot_in_K"], 1100)
            self.assertAlmostEqual(row["cold_out_K"] + row["hot_out_K"], 1100)
            self.assertAlmostEqual(capacity * (row["cold_out_K"] - row["cold_in_K"]), row["heat_W"])
        for previous, current in zip(trace, trace[1:]):
            self.assertEqual(previous["cold_out_K"], current["cold_in_K"])
            self.assertEqual(previous["hot_out_K"], current["hot_in_K"])
        self.assertAlmostEqual(sum(row["heat_W"] for row in trace) / 1000, result["recovered_kW"])

    def test_pressure_sweep_exposes_unbounded_coefficients_without_clipping(self):
        with patch.object(model, "P", 0.20):
            result = model.run_5stage()
        self.assertEqual(result["validity"]["stage_effectiveness_out_of_bounds"], [1, 2, 3, 4, 5])
        self.assertTrue(result["validity"]["overall_effectiveness_out_of_bounds"])
        self.assertAlmostEqual(result["overall_eff"], 2.303163104927802)
        self.assertGreater(result["stage_trace"][-1]["cold_out_K"], 900)

    def test_bounded_stage_coefficients_do_not_validate_counterflow_topology(self):
        with patch.object(model, "stage", return_value=(0.1, 0.1, 10.0, 0.015)):
            result = model.run_5stage()
        self.assertFalse(result["valid_counterflow"])
        self.assertEqual(result["validity"]["negative_heat_stages"], [])
        self.assertEqual(result["validity"]["stage_effectiveness_out_of_bounds"], [])

    def test_cli_discloses_invalidity_and_signed_heat(self):
        output = subprocess.check_output([sys.executable, str(MODEL)], text=True)
        self.assertIn("WARNING: invalid counterflow interpretation", output)
        self.assertIn("unvalidated arithmetic outputs", output)
        self.assertIn("Q=-", output)
        self.assertIn("Overall effectiveness: 75.6%", output)


if __name__ == "__main__":
    unittest.main()
