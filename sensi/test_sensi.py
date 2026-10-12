import unittest
from copy import deepcopy
from unittest.mock import patch

import numpy as np
import pandas as pd

from pfs.pfs import calculer_trainee
from sensi import sensi


class SensitivityTests(unittest.TestCase):
    def test_yaw_target_crosses_zero_without_splitting(self):
        criteria = {"yaw_deg": dict(enabled=True, target=0., tolerance=2., period=360.)}
        for values in ([359., 0., 1., 360., -1., 2., 358., 20., 0., 1.],
                       [-1., 0., 1., 0., -1., 2., -2., 20., 0., 1.]):
            imu = pd.DataFrame(dict(time=np.arange(10.), yaw_deg=values))
            signals = sensi.prepare_signals(imu, criteria)
            self.assertEqual(sensi.detect_intervals(signals, 0, 9, criteria, 2), [(0., 6.)])

    def test_missing_angle_cuts_interval_without_poisoning_later_values(self):
        criteria = {"yaw_deg": dict(enabled=True, target=0., tolerance=2., period=360.)}
        imu = pd.DataFrame(dict(time=np.arange(8.), yaw_deg=[359., 0., np.nan, 1., 0., 359., 2., 358.]))
        signals = sensi.prepare_signals(imu, criteria)
        self.assertTrue(signals["yaw_deg"].iloc[3:].notna().all())
        self.assertEqual(sensi.detect_intervals(signals, 0, 7, criteria, 2), [(3., 7.)])

    def test_roll_stability_is_independent_of_orientation_and_angle_wrap(self):
        criteria = {"roll_deg": dict(enabled=True, mode="variation", epsilon=3., period=360.)}
        for values in ([100., 101., 99., 100.], [179., -180., -179., 179.]):
            imu = pd.DataFrame(dict(time=np.arange(4.), roll_deg=values))
            signals = sensi.prepare_signals(imu, criteria)
            self.assertEqual(sensi.detect_intervals(signals, 0, 3, criteria, 2), [(0., 3.)])
        criteria["roll_deg"]["epsilon"] = 2.
        self.assertEqual(sensi.detect_intervals(signals, 0, 3, criteria, 2), [])

    def test_duration_sweep_filters_short_intervals_in_each_context(self):
        time = np.arange(10.)
        speed = pd.Series(0.5, index=time)
        depth = pd.Series(time * 0.5, index=time)
        pitch = pd.Series([-90.] * 3 + [0.] + [-90.] * 6, index=time)
        experiment = (1, "1v1", speed, depth, {"pitch_deg": pitch})
        criteria = {"pitch_deg": dict(enabled=True, target=-90., tolerance=2.)}
        reference = pd.DataFrame([sensi.evaluate(experiment, criteria, 2.)[0]])
        with patch.object(sensi, "Stationary_criteria", criteria), \
             patch.object(sensi, "Sweep_values", {"min_duration_s": [1., 3., 6.]}), \
             patch.object(sensi, "Stationary_min_duration", 2.), \
             patch.object(sensi, "Contexts", {"actuels": 1., "permissifs": 2.}):
            results = sensi.sweep([experiment], reference)
        for _, group in results.groupby("contexte"):
            self.assertEqual(group["valeur"].to_list(), [1., 2., 3., 6.])
            self.assertEqual(group["min_duration_s"].to_list(), [1., 2., 3., 6.])
            self.assertEqual(group["intervalles"].to_list(), [2, 2, 1, 0])
            self.assertEqual(group["duree_s"].to_list(), [7., 7., 5., 0.])
            self.assertTrue(np.isnan(group.iloc[-1].trainee_N))

    def test_union_ignores_gaps_and_fragmentation(self):
        speed = pd.Series([0.5, 0.7, 50., 50., 1., 1.2, 1.4])
        depth = pd.Series([10., 11., 100., 100., 14., 15., 16.])
        combined = sensi.measure_descent("1v1", 1, [(0, 1), (4, 6)], speed, depth)
        split = sensi.measure_descent("1v1", 1, [(0, 1), (4, 5), (5, 6)], speed, depth)
        self.assertEqual(combined["n_mesures"], 5)
        self.assertAlmostEqual(combined["v_r_m_s"], 0.96)
        self.assertAlmostEqual(combined["profondeur_m"], 13.2)
        self.assertAlmostEqual(combined["trainee_N"], calculer_trainee(0.96, 1, 13.2))
        for key in ("n_mesures", "duree_s", "v_r_m_s", "profondeur_m", "trainee_N"):
            self.assertEqual(combined[key], split[key])

    def test_no_detection_is_not_zero_force(self):
        signal = pd.Series([1., 2., 3.])
        result = sensi.measure_descent("1v1", 1, [], signal, signal)
        self.assertEqual(result["n_mesures"], 0)
        self.assertEqual(result["duree_s"], 0)
        for key in ("v_r_m_s", "profondeur_m", "trainee_N"):
            self.assertTrue(np.isnan(result[key]))

    def test_context_comparisons_change_only_the_studied_threshold(self):
        criteria = {
            "xacc_robot": dict(enabled=True, mode="variation", epsilon=1., cutoff_freq=0.1),
            "pitch_deg": dict(enabled=True, target=-90., tolerance=2.),
        }
        original = deepcopy(criteria)
        reference = pd.DataFrame([dict(dossier="1v1", trainee_N=2.)])

        def evaluate(experiment, options, min_duration):
            self.assertEqual(min_duration, sensi.Stationary_min_duration)
            self.assertEqual(options["pitch_deg"]["target"], -90.)
            self.assertEqual(options["xacc_robot"]["cutoff_freq"], 0.1)
            force = options["xacc_robot"]["epsilon"] * options["pitch_deg"]["tolerance"]
            return dict(halteres=1, dossier="1v1", trainee_N=force), []

        with patch.object(sensi, "Stationary_criteria", criteria), \
             patch.object(sensi, "Sweep_values", {"xacc_robot": [0.5, 2.]}), \
             patch.object(sensi, "Contexts", {"actuels": 1., "permissifs": 2.}), \
             patch.object(sensi, "evaluate", side_effect=evaluate):
            results = sensi.sweep([None], reference)
        self.assertEqual(criteria, original)
        self.assertEqual(len(results), 6)  # Le seuil de référence est ajouté automatiquement.
        row = results.loc[(results.contexte == "permissifs") & (results.valeur == 2.)].iloc[0]
        self.assertEqual(row.trainee_N, 8.)
        self.assertEqual(row.delta_contexte_N, 4.)
        self.assertEqual(row.delta_reference_N, 6.)
        self.assertEqual(row.delta_contexte_pct, 100.)

    def test_missing_baseline_preserves_other_measurements(self):
        criteria = {"pitch_deg": dict(enabled=True, target=-90., tolerance=6.)}
        reference = pd.DataFrame([dict(dossier="1v1", trainee_N=np.nan)])

        def evaluate(experiment, options, min_duration):
            value = options["pitch_deg"]["tolerance"]
            return dict(halteres=1, dossier="1v1", trainee_N=20. if value > 6 else np.nan), []

        with patch.object(sensi, "Stationary_criteria", criteria), \
             patch.object(sensi, "Sweep_values", {"pitch_deg": [3., 9.]}), \
             patch.object(sensi, "Contexts", {"actuels": 1.}), \
             patch.object(sensi, "evaluate", side_effect=evaluate):
            results = sensi.sweep([None], reference)
        self.assertEqual(len(results), 3)
        self.assertEqual(results.loc[results.valeur == 9., "trainee_N"].iloc[0], 20.)
        self.assertTrue(results[["delta_reference_N", "delta_contexte_N", "delta_contexte_pct"]].isna().all().all())


if __name__ == "__main__":
    unittest.main()
