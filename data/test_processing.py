import unittest
from ast import literal_eval
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import numpy as np
import pandas as pd
from pandas.testing import assert_series_equal

import main
from analysis_tools import (
    interval_statistics, moving_average, moving_median, plot_subplots, processed_series,
)
from filtre import filter_series
from stationary import sinking_intervals


class ProcessingTests(unittest.TestCase):
    def setUp(self):
        self.times = np.arange(401) / 10
        self.value = pd.Series(0.8 + 0.2 * np.sin(2 * np.pi * self.times),
                               index=self.times, name="sink_speed")
        self.all_treatments = dict(raw=True, moving_average=True, moving_median=True, lowpass=True)

    def test_rolling_statistics_and_interval_boundaries(self):
        value = pd.Series([0., 10., 2., 4.], index=[0., 1., 2., 3.], name="speed")
        average = moving_average(value, window_n=3)
        median = moving_median(value, window_n=3)
        np.testing.assert_allclose(average, [0, 5, 4, 16 / 3])
        np.testing.assert_allclose(median, [0, 5, 2, 4])
        stats = interval_statistics(median, 1, 2)
        self.assertEqual(stats, dict(count=2, mean=3.5, median=3.5, std=1.5))
        timed = moving_median(value, window_s=2)
        np.testing.assert_allclose(timed, median)
        centered = moving_median(value, window_n=3, center=True)
        np.testing.assert_allclose(centered, [5, 2, 4, 3])

    def test_treatments_are_independent_and_do_not_change_source(self):
        original = self.value.copy()
        variants = processed_series(self.value, self.all_treatments, window_n=5, cutoff_freq=0.2)
        assert_series_equal(variants[0], self.value.rename(variants[0].name))
        assert_series_equal(variants[1], moving_average(self.value, window_n=5))
        assert_series_equal(variants[2], moving_median(self.value, window_n=5))
        assert_series_equal(variants[3], filter_series(self.value, 0.2))
        assert_series_equal(self.value, original)
        interior = variants[3].loc[10:30]
        self.assertAlmostEqual(interior.mean(), 0.8, delta=0.005)
        self.assertLess(interior.std(), 0.01)

    def test_individual_switches_and_disabled_filter(self):
        for key in self.all_treatments:
            with self.subTest(key=key):
                variants = processed_series(self.value, {key: True}, window_n=5, cutoff_freq=0.2)
                self.assertEqual(len(variants), 1)
        with patch("analysis_tools.filter_series", side_effect=AssertionError("must not filter")):
            variants = processed_series(self.value, {"raw": True}, cutoff_freq=-1)
            self.assertEqual(len(variants), 1)

    def test_missing_values_in_rolling_statistics(self):
        value = self.value.copy()
        value.iloc[5] = np.nan
        self.assertTrue(pd.isna(moving_median(value, window_n=3).iloc[5]))
        self.assertEqual(interval_statistics(value, 0.5, 0.5)["count"], 0)

    def test_main_shared_intervals_and_plotted_statistics(self):
        folder = main.Path_root / "test"
        bar = pd.DataFrame(dict(time=self.times, sink_speed=self.value.to_numpy(), depth=2 + self.times))
        imu = pd.DataFrame(dict(time=self.times, xacc_robot=np.full(len(self.times), -9.81)))
        datasets = {folder: {"test_bar30.jsonl": bar, "test_imu.jsonl": imu}}
        config = dict(folder="test", file="bar30", variable="sink_speed", window_n=5,
                      stats=True, stats_tmin=10, stats_tmax=20, stationary=True)
        criteria = {"xacc_robot": dict(enabled=True, target=-9.81, tolerance=0.05)}
        with patch.object(main, "Subplots", [config]), \
             patch.object(main, "Treatments", self.all_treatments), \
             patch.object(main, "Stationary_criteria", criteria), \
             patch.object(main, "Stationary_min_duration", 5):
            panels = main.build_panels(datasets)
            self.assertEqual(panels[0]["intervals"], [(0., 40.)])
            self.assertEqual(len(panels[0]["value"]), 4)
            figure = plot_subplots(panels)
            self.assertEqual(len(figure.data), 8)  # Four curves + four interval means.
            notes = figure.layout.annotations[-1].text
            self.assertEqual(notes.count("Médiane :"), 8)  # Manual and detected interval.
            self.assertIn("N : 101", notes)
            for variant in panels[0]["value"]:
                self.assertIn(f"Moyenne : {variant.loc[10:20].mean():.6g}", notes)
            # Only lowpass, with another curve cutoff: detection must remain identical.
            config["treatments"] = dict(raw=False, moving_average=False, moving_median=False)
            config["cutoff_freq"] = 0.4
            lowpass_panels = main.build_panels(datasets)
            self.assertEqual(lowpass_panels[0]["intervals"], panels[0]["intervals"])
            self.assertEqual(len(lowpass_panels[0]["value"]), 1)
            # Multi-variable panel, no stationary detection, empty manual interval.
            config.update(variable=["sink_speed", "depth"], stationary=False, stats_tmin=100)
            multiple = main.build_panels(datasets)
            self.assertEqual(len(multiple[0]["value"]), 2)
            self.assertEqual(plot_subplots(multiple).layout.annotations[-1].text.count("Aucune donnée"), 2)
        pd.testing.assert_frame_equal(datasets[folder]["test_bar30.jsonl"], bar)

    def test_stationary_criteria_combine_and_toggle_independently(self):
        imu = pd.DataFrame(dict(time=np.arange(16, dtype=float), xacc_robot=[-9.81] * 16,
                                pitch_deg=[-95, -90, -85, -90, -90, -80, -90, -90,
                                           np.nan, -90, -90, -90, -90, -90, -90, -90],
                                xgyro_robot=[0] * 12 + [20] * 4))
        criteria = {
            "xacc_robot": dict(enabled=True, target=-9.81, tolerance=0.03, epsilon=0.03),
            "pitch_deg": dict(enabled=False, target=-90, tolerance=5),
            "xgyro_robot": dict(enabled=False, target=0, tolerance=1),
        }
        with patch.object(main, "Stationary_criteria", criteria), \
             patch.object(main, "Stationary_min_duration", 3):
            self.assertEqual(main.detect_intervals(imu, 0, 15)[0], [(0., 15.)])
            criteria["pitch_deg"]["enabled"] = True
            for mode in ("target", "variation"):
                criteria["xacc_robot"]["mode"] = mode
                self.assertEqual(main.detect_intervals(imu, 0, 15)[0], [(0., 4.), (9., 15.)])
            criteria["xgyro_robot"]["enabled"] = True
            self.assertEqual(main.detect_intervals(imu, 0, 15)[0], [(0., 4.)])
            criteria["xgyro_robot"]["enabled"] = False
            imu.loc[12, "xacc_robot"] = 0
            self.assertEqual(main.detect_intervals(imu, 0, 15)[0], [(0., 4.)])
            criteria["xacc_robot"]["enabled"] = False
            imu = imu.drop(columns="xacc_robot")
            self.assertEqual(main.detect_intervals(imu, 0, 15)[0], [(0., 4.), (9., 15.)])
            self.assertEqual(main.detect_intervals(imu, 10, 14)[0], [(10., 14.)])
            criteria["pitch_deg"]["enabled"] = False
            self.assertEqual(main.detect_intervals(imu, 0, 15)[0], [])

    def test_main_defaults_and_overrides(self):
        with patch.object(main, "Treatments", self.all_treatments), patch.object(main, "Rolling_window_s", 5):
            values = main.studied_values(self.value, {"window_n": 3, "cutoff_freq": None})
            self.assertEqual(len(values), 3)
            assert_series_equal(values[1], moving_average(self.value, window_n=3))
            values = main.studied_values(self.value, {"window_s": None})
            assert_series_equal(values[2], moving_median(self.value, window_s=5))

    def test_sinking_intervals_reject_stops_ascent_and_small_depth_change(self):
        intervals = [(0, 2), (3, 5), (6, 8), (9, 11), (12, 14)]
        speed = pd.Series([0.] * 3 + [0.6] * 3 + [-0.6] * 3 + [0.01] * 3 + [0.6] * 3)
        depth = pd.Series([2., 2., 2., 2., 2.05, 2.1, 3., 2., 1., 1., 2., 3., 3., 3.5, 4.])
        self.assertEqual(sinking_intervals(intervals, speed, depth, 0.05, 0.2), [(12, 14)])
        self.assertEqual(sinking_intervals([(20, 22)], speed, depth, 0.05, 0.2), [])

    def test_export_uses_filtered_speed_and_mean_depth_in_interval_order(self):
        speed = filter_series(self.value, 0.2)
        depth = pd.Series(self.times ** 2, index=self.times)
        intervals = [(10., 10.7), (20., 21.)]
        panels = [dict(intervals=intervals, sink_speed=speed, depth=depth), dict(intervals=None)]
        with TemporaryDirectory() as folder:
            destination = Path(folder) / "coulees.txt"
            main.export_intervals(panels, destination)
            exported = literal_eval("{" + destination.read_text(encoding="utf-8") + "}")[main.poids]
            self.assertEqual(exported["v_r"], [round(float(speed.loc[a:b].mean()), 3) for a, b in intervals])
            self.assertEqual(exported["L_touret"], [round(float(depth.loc[a:b].mean()), 3) for a, b in intervals])
            self.assertNotEqual(exported["v_r"][0], round(float(self.value.loc[10:10.7].mean()), 3))
            main.export_intervals([dict(intervals=[])], destination)
            self.assertEqual(destination.read_text(encoding="utf-8"),
                             f'    {main.poids}: {{\n        "v_r": [],\n        "L_touret": [],\n    }},\n')

    def test_outliers_across_trials_keep_exported_speeds_and_depths_aligned(self):
        speeds = [1.198, 1.20, 1.202, 1.24, 0.9]
        panels = [dict(intervals=[(0, 1)], sink_speed=pd.Series([speed, speed]),
                       depth=pd.Series([i, i + 1])) for i, speed in enumerate(speeds)]
        panels.append(dict(intervals=None))
        main.filter_stationary_outliers(panels, None)
        self.assertEqual(sum(len(p["intervals"] or []) for p in panels), 5)
        main.filter_stationary_outliers(panels, 1.5)
        self.assertEqual([p["intervals"] for p in panels],
                         [[(0, 1)], [(0, 1)], [(0, 1)], [], [], None])
        with TemporaryDirectory() as folder:
            destination = Path(folder) / "coulees.txt"
            main.export_intervals(panels, destination)
            exported = literal_eval("{" + destination.read_text(encoding="utf-8") + "}")[main.poids]
            self.assertEqual(exported, dict(v_r=[1.198, 1.2, 1.202], L_touret=[0.5, 1.5, 2.5]))

    def test_outlier_filter_preserves_at_least_three_intervals(self):
        for speeds in ([], [1.2], [1.2, 1.8], [1.2, 1.2, 1.8]):
            panels = [dict(intervals=[(0, 1)], sink_speed=pd.Series([speed, speed]))
                      for speed in speeds]
            main.filter_stationary_outliers(panels, 1.5)
            self.assertEqual([p["intervals"] for p in panels], [[(0, 1)]] * len(speeds))

    def test_std_inflation_filter_handles_zero_spread_and_relative_scale(self):
        cases = [([1.2] * 4, 4), ([1.2] * 3 + [1.8], 3),
                 ([1.18, 1.20, 1.22, 1.24], 4),
                 ([1.198, 1.20, 1.202, 1.24, 0.9], 3)]
        for speeds, count in cases:
            for scale in (1, 1000):
                with self.subTest(speeds=speeds, scale=scale):
                    panels = [dict(intervals=[(0, 1)],
                                   sink_speed=pd.Series([speed * scale] * 2))
                              for speed in speeds]
                    main.filter_stationary_outliers(panels, 1.5)
                    self.assertEqual(sum(len(p["intervals"]) for p in panels), count)


if __name__ == "__main__":
    unittest.main()
