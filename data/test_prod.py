import ast
from importlib import import_module
from pathlib import Path
from statistics import StatisticsError
import sys
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

import prod

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pfs"))
repet = import_module("2repet")


class AttitudeTests(unittest.TestCase):
    def test_circular_angles_and_export_from_raw_imu(self):
        times = np.arange(7, dtype=float)
        folder = prod.Path_root / "test"
        imu = pd.DataFrame(dict(time=times, yaw_deg=[359, 1, 359, 1, 0, 0, 0],
                                pitch_deg=[270] * 7, roll_deg=[80, -80, 50, -50, 0, 120, -120]))
        bar = pd.DataFrame(dict(time=times, sink_speed=[0.8] * 7, depth=1 + 0.8 * times))
        datasets = {folder: {"test_imu.jsonl": imu, "test_bar30.jsonl": bar}}
        criteria = {
            "yaw_deg": dict(enabled=True, target=0, tolerance=2, period=360),
            "pitch_deg": dict(enabled=True, target=-90, tolerance=2, period=360),
        }
        config = dict(folder="test", file="bar30", variable="sink_speed", stationary=True)
        with patch.object(prod, "Stationary_criteria", criteria), \
             patch.object(prod, "Cutoff_freq", None), \
             patch.object(prod, "Treatments", {"raw": True}), \
             patch.object(prod, "Max_std_inflation", None):
            panels = prod.build_panels(datasets, [config])
        self.assertEqual(panels[0]["intervals"], [(0., 6.)])
        result = ast.literal_eval("{" + prod.export_intervals(panels, 10) + "}")[10]
        self.assertEqual(result, {"v_r": [0.8], "L_touret": [3.4], "d": [0.756]})
        self.assertEqual(prod.angular_deviation(1, 359), 2)
        self.assertEqual(prod.angular_deviation(270, -90), 0)

    def test_export_alignment_after_outlier_removal(self):
        panels = [dict(intervals=[(0, 2)], sink_speed=pd.Series([speed] * 3),
                       depth=pd.Series([depth] * 3), attitude_squared=pd.Series([d**2] * 3))
                  for speed, depth, d in [(0.8, 10, 1), (0.82, 20, 2), (0.81, 30, 3), (1.5, 40, 4)]]
        prod.filter_stationary_outliers(panels, 1.5)
        result = ast.literal_eval("{" + prod.export_intervals(panels, 1) + "}")[1]
        self.assertEqual(result, {"v_r": [0.8, 0.82, 0.81], "L_touret": [10., 20., 30.], "d": [1., 2., 3.]})

    def test_missing_attitude_is_not_treated_as_perfect(self):
        panel = dict(intervals=[(0, 2)], sink_speed=pd.Series([0.8] * 3),
                     depth=pd.Series([10.] * 3), attitude_squared=pd.Series([1., np.nan, 9.]))
        result = ast.literal_eval("{" + prod.export_intervals([panel], 1) + "}")[1]
        self.assertEqual(result["d"], [round(np.sqrt(5), 3)])
        panel["attitude_squared"][:] = np.nan
        with self.assertRaises(StatisticsError):
            prod.export_intervals([panel], 1)

    def test_weights_and_weighted_population_statistics(self):
        self.assertEqual(repet.poids_attitude(0), 1)
        self.assertAlmostEqual(repet.poids_attitude(5), np.exp(-0.5))
        self.assertEqual(repet.poids_attitude(15), 0.05)
        weights = [0.9, 0.1]
        self.assertAlmostEqual(repet.moyenne_ponderee([10, 20], weights), 11)
        self.assertAlmostEqual(repet.ecart_type_pondere([10, 20], weights), 3)
        self.assertAlmostEqual(repet.moyenne_ponderee(weights, weights), 0.82)
        with self.assertRaises(ValueError):
            repet.moyenne_ponderee([10], weights)


if __name__ == "__main__":
    unittest.main()
