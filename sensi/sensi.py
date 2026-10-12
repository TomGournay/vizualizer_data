import json
from pathlib import Path
import re

import numpy as np
import pandas as pd

from data.analysis_tools import get_value, load_folder, moving_average
from data.filtre import filter_series
from data.stationary import sinking_intervals, stationary_intervals
from pfs.pfs import calculer_trainee
from sensi.plots import write_reports
from sensi.repet import summarize


Path_root = Path(__file__).resolve().parents[2] / "experiment_result" / "data_exp"
Output = Path(__file__).resolve().parent / "resultats"
Poids = range(1, 13)          # None = tous les poids disponibles.
Repetitions = range(1, 4)     # None = toutes les répétitions disponibles.

# Référence : tous les critères activés doivent être respectés.
# target : target ± tolerance ; variation : max-min < epsilon.
# Roll/yaw : références permissives pour garder des mesures ; seuils serrés dans Sweep_values.
Stationary_criteria = {
    "xacc_robot": {"enabled": True, "mode": "variation", "epsilon": 0.05, "cutoff_freq": 0.1},
    "yacc_robot": {"enabled": True, "mode": "variation", "epsilon": 0.05, "cutoff_freq": 0.1},
    "zacc_robot": {"enabled": True, "mode": "variation", "epsilon": 0.05, "cutoff_freq": 0.1},
    "pitch_deg": {"enabled": True, "target": -90.0, "tolerance": 6.0},
    "roll_deg": {"enabled": True, "mode": "variation", "epsilon": 180.0, "period": 360.0},
    "yaw_deg": {"enabled": True, "target": 0.0, "tolerance": 180.0, "period": 360.0},
    "xgyro_robot": {"enabled": True, "target": 0, "tolerance": 0.8},
    "ygyro_robot": {"enabled": True, "target": 0, "tolerance": 0.8},
    "zgyro_robot": {"enabled": True, "target": 0, "tolerance": 0.8},
}
Stationary_min_duration = 2.0  # s ; appliquée à chaque étape du découpage existant.
Cutoff_freq = 0.1             # Hz, vitesse BAR30 ; None = vitesse brute du fichier.
Min_sink_speed = 0.05         # m/s
Min_depth_change = 0.20       # m

# Valeurs plus strictes ET plus permissives ; chaque axe est balayé séparément.
Sweep_values = {
    "xacc_robot": [0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 5.00],
    "yacc_robot": [0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 5.00],
    "zacc_robot": [0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 5.00],
    "pitch_deg": [1, 2, 3, 4, 6, 7, 8, 10, 12],
    "roll_deg": [1, 2, 3, 4, 6, 8, 10, 15, 20, 30, 45, 60, 90, 120, 180, 270, 360],
    "yaw_deg": [1, 2, 3, 4, 6, 8, 10, 15, 20, 30, 45, 60, 90, 120, 180],
    "xgyro_robot": [0.1, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.6, 2.0],
    "ygyro_robot": [0.1, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.6, 2.0],
    "zgyro_robot": [0.1, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.6, 2.0],
    "min_duration_s": [0.5, 1, 1.5, 2, 3, 4, 5, 8, 10],
}
# Multiplicateurs des seuils capteurs des AUTRES critères. Cibles et filtres restent fixes.
# La durée reste à sa référence, sauf pendant son propre balayage.
Contexts = {"actuels": 1.0, "intermediaires": 1.5, "permissifs": 2.0}


def experiment_folders(root, poids, repetitions):
    folders = []
    for folder in root.iterdir():
        match = re.fullmatch(r"(\d+)v(\d+)", folder.name)
        if not folder.is_dir() or match is None:
            continue
        nombre, repetition = map(int, match.groups())
        if poids is not None and nombre not in poids:
            continue
        if repetitions is not None and repetition not in repetitions:
            continue
        folders.append((nombre, repetition, folder))
    return sorted(folders)


def prepare_signals(imu, criteria):
    """Déplie les angles périodiques avant tout lissage ; conserve les valeurs manquantes."""
    signals = {}
    for name, options in criteria.items():
        if not options["enabled"]:
            continue
        signal = get_value(imu, name)
        if options.get("period") is not None:
            valid = signal.notna()
            signal.loc[valid] = np.unwrap(signal.loc[valid], period=options["period"])
        if options.get("cutoff_freq") is not None:
            signal = filter_series(signal, options["cutoff_freq"])
        window_s, window_n = options.get("window_s"), options.get("window_n")
        if window_s is not None or window_n is not None:
            signal = moving_average(signal, window_s=window_s, window_n=window_n)
        signals[name] = signal
    return signals


def load_experiments():
    experiments = []
    for nombre, _, folder in experiment_folders(Path_root, Poids, Repetitions):
        data = load_folder(folder)
        bar30 = data[f"{folder.name}_bar30.jsonl"]
        speed = get_value(bar30, "sink_speed")
        if Cutoff_freq is not None:
            speed = filter_series(speed, Cutoff_freq)
        signals = prepare_signals(data[f"{folder.name}_imu.jsonl"], Stationary_criteria)
        experiments.append((nombre, folder.name, speed, get_value(bar30, "depth"), signals))
    return experiments


def threshold_key(options):
    return "epsilon" if options.get("mode", "target") == "variation" else "tolerance"


def detect_intervals(signals, start, end, criteria, min_duration):
    """Cibles, puis variations dans l'ordre fourni ; signaux déjà filtrés."""
    enabled = [(name, options) for name, options in criteria.items() if options["enabled"]]
    enabled.sort(key=lambda item: item[1].get("mode", "target") == "variation")
    intervals = [(start, end)] if enabled else []
    for name, options in enabled:
        mode = options.get("mode", "target")
        keys = ("target", "tolerance") if mode == "target" else ("epsilon",)
        thresholds = {key: options[key] for key in keys}
        signal = signals[name]
        if mode == "target" and options.get("period") is not None:
            period = options["period"]
            signal = (signal - options["target"] + period / 2) % period - period / 2
            thresholds["target"] = 0
        intervals = [interval for lo, hi in intervals
                     for interval in stationary_intervals(signal.loc[lo:hi], mode=mode,
                                                          min_duration=min_duration, **thresholds)]
    return intervals


def measure_descent(folder, nombre, intervals, speed, depth):
    """Moyennes sur l'union des échantillons retenus, sans trous ni doublons aux bornes."""
    selected = np.zeros(len(speed), dtype=bool)
    for start, end in intervals:
        selected |= (speed.index >= start) & (speed.index <= end)
    velocity = float(speed.iloc[selected].mean())
    length = float(depth.iloc[selected].mean())  # Même index BAR30.
    return dict(halteres=nombre, dossier=folder, intervalles=len(intervals),
                duree_s=sum(end - start for start, end in intervals), n_mesures=int(selected.sum()),
                v_r_m_s=velocity, profondeur_m=length,
                trainee_N=calculer_trainee(velocity, nombre, length))


def evaluate(experiment, criteria, min_duration):
    nombre, folder, speed, depth, signals = experiment
    intervals = detect_intervals(signals, max(0, speed.index.min()), speed.index.max(),
                                 criteria, min_duration)
    intervals = sinking_intervals(intervals, speed, depth, Min_sink_speed, Min_depth_change)
    return measure_descent(folder, nombre, intervals, speed, depth), intervals


def build_reference(experiments):
    rows, fragments = [], []
    for experiment in experiments:
        row, intervals = evaluate(experiment, Stationary_criteria, Stationary_min_duration)
        rows.append(row)
        nombre, folder, speed, depth, _ = experiment
        for number, (start, end) in enumerate(intervals, 1):
            fragment = measure_descent(folder, nombre, [(start, end)], speed, depth)
            fragments.append({**fragment, "intervalle": number, "tmin_s": start, "tmax_s": end})
    columns = ["halteres", "dossier", "intervalle", "tmin_s", "tmax_s",
               "duree_s", "v_r_m_s", "profondeur_m", "trainee_N"]
    return pd.DataFrame(rows), pd.DataFrame(fragments, columns=columns)


def sweep(experiments, reference):
    rows = []
    for parameter, values in Sweep_values.items():
        duration_sweep = parameter == "min_duration_s"
        if duration_sweep:
            baseline = Stationary_min_duration
        else:
            options = Stationary_criteria[parameter]
            if not options["enabled"]:
                continue
            key = threshold_key(options)
            baseline = options[key]
        for context, factor in Contexts.items():
            criteria = {
                name: {**option, threshold_key(option): option[threshold_key(option)] * factor}
                for name, option in Stationary_criteria.items()
            }
            for value in sorted(set([*values, baseline])):
                duration = Stationary_min_duration
                if duration_sweep:
                    duration = value
                else:
                    criteria[parameter][key] = value
                for experiment in experiments:
                    row, _ = evaluate(experiment, criteria, duration)
                    rows.append(dict(parametre=parameter, contexte=context, valeur=value,
                                     valeur_reference=baseline, min_duration_s=duration, **row))
    results = pd.DataFrame(rows)
    results["trainee_reference_N"] = results["dossier"].map(reference.set_index("dossier")["trainee_N"])
    # Comparaison appariée : les autres critères restent identiques dans ce contexte.
    keys = ["parametre", "contexte", "dossier"]
    baseline = results.loc[results.valeur == results.valeur_reference].set_index(keys)["trainee_N"]
    results = results.join(baseline.rename("trainee_base_contexte_N"), on=keys)
    results["delta_reference_N"] = results.trainee_N - results.trainee_reference_N
    results["delta_contexte_N"] = results.trainee_N - results.trainee_base_contexte_N
    results["delta_contexte_pct"] = 100 * results.delta_contexte_N / results.trainee_base_contexte_N.replace(0, np.nan)
    return results


def main():
    experiments = load_experiments()
    reference, intervals = build_reference(experiments)
    results = sweep(experiments, reference)
    summary = summarize(reference)
    settings = dict(path_root=str(Path_root), poids=None if Poids is None else list(Poids),
                    repetitions=None if Repetitions is None else list(Repetitions),
                    stationary_criteria=Stationary_criteria, sweep_values=Sweep_values, contexts=Contexts,
                    min_duration_s=Stationary_min_duration, speed_cutoff_hz=Cutoff_freq,
                    min_sink_speed=Min_sink_speed, min_depth_change=Min_depth_change)
    Output.mkdir(parents=True, exist_ok=True)
    for name, frame in (("reference", reference), ("reference_intervalles", intervals),
                        ("par_poids", summary), ("sensibilite", results)):
        frame.to_csv(Output / f"{name}.csv", index=False)
    (Output / "parametres.json").write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    signals = {folder: (speed, depth) for _, folder, speed, depth, _ in experiments}
    write_reports(reference, intervals, summary, results, signals, settings, Output)


if __name__ == "__main__":
    main()
