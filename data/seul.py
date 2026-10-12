from pathlib import Path

from analysis_tools import (
    load_folder, get_value, moving_average, processed_series, plot_subplots,
)
from plot_display import open_plot
from stationary import sinking_intervals, stationary_intervals
from filtre import filter_series

Path_root = Path("/home/crc/experiment_result/data_exp")



# variable : un nom ou une liste de noms, superposes sur le meme axe Y.
# Un dictionnaire par graphique. Pour un seul graphique, garder une seule entrée.
# None = borne automatique. window_s/window_n surchargent la fenêtre globale.
# stats=True : moyenne, médiane et écart type de CHAQUE traitement activé.
# stats_tmin/stats_tmax : intervalle indépendant du tracé ; None = début/fin du fichier.
# stationary=True : détection avec Stationary_criteria sur l'IMU du même dossier.

# Activer/désactiver chaque courbe ET ses calculs, indépendamment des autres.
Treatments = {
    "raw": False,             # Données brutes du fichier
    "moving_average": False,  # Moyenne glissante des données brutes
    "moving_median": False,   # Médiane glissante des données brutes
    "lowpass": True,         # Filtre passe-bas des données brutes
}
Rolling_window_s = 5.0       # Fenêtre commune aux deux traitements glissants
Rolling_window_n = None      # OU nombre de points ; mettre Rolling_window_s à None
Rolling_center = False       # False : fenêtre passée ; True : fenêtre centrée
Cutoff_freq = 0.1            # Hz ; None désactive la courbe passe-bas
gyro_tol = 0.2
# Tous les critères activés doivent être respectés ; aucun activé = aucun intervalle.
# mode="target" (par défaut) : target ± tolerance ; mode="variation" : max-min < epsilon.
# Seuils dans l'unité de la variable. Filtrage indépendant des courbes :
# cutoff_freq en Hz ; window_s OU window_n pour une moyenne glissante ; absents/None = brut.
Stationary_criteria = {
    "xacc_robot": {"enabled": True, "mode": "variation", "epsilon": 0.05, "cutoff_freq": Cutoff_freq},
    "yacc_robot": {"enabled": True, "mode": "variation", "epsilon": 0.05, "cutoff_freq": Cutoff_freq},
    "zacc_robot": {"enabled": True, "mode": "variation", "epsilon": 0.05, "cutoff_freq": Cutoff_freq},
    "pitch_deg": {"enabled": True, "target": -90.0, "tolerance": 6.0},
    "roll_deg": {"enabled": True, "mode": "variation", "epsilon": 180.0, "period": 360.0},
    "yaw_deg": {"enabled": True, "target": 0.0, "tolerance": 180.0, "period": 360.0},
    "xgyro_robot": {"enabled": True, "target": 0, "tolerance": gyro_tol},
    "ygyro_robot": {"enabled": True, "target": 0, "tolerance": gyro_tol},
    "zgyro_robot": {"enabled": True, "target": 0, "tolerance": gyro_tol},
}
Stationary_min_duration = 1.0  # secondes, après combinaison des critères

# Garder uniquement les coulées (descente positive), pour le tracé et l'export.
Min_sink_speed = 0.05        # m/s, vitesse moyenne minimale
Min_depth_change = 0.20      # m, augmentation minimale de profondeur
Export_file = Path(__file__).resolve().parent / "coulees.txt"

# Template 1 : plusieurs fichiers du même dossier.
folder_name = "1v2"
Show_plot = True

Subplots_meme_dossier = [

    {"file": "bar30", "variable": "sink_speed",
     "tmin": 0, "tmax": None, "ymin": 0.7, "ymax": 1.4, "window_s": 5,
     "stats": True, "stats_tmin": 0, "stats_tmax": 70,
     "stationary": True},

    {"file": "bar30", "variable": "depth",
     "tmin": 0, "tmax": None, "ymin": 0.7, "ymax": 1.4, "window_s": 5,
     "stats": True, "stats_tmin": 0, "stats_tmax": 70,
     "stationary": True},

    {"file": "imu", "variable": ["xacc_robot", "yacc_robot", "zacc_robot"],
     "tmin": 0, "tmax": None, "ymin": None, "ymax": None, "window_n": 40,
     "stats": False, "stats_tmin": None, "stats_tmax": None,
     "stationary": False},

    {"file": "imu", "variable": ["xgyro_robot", "ygyro_robot", "zgyro_robot"],
     "tmin": 0, "tmax": None, "ymin": None, "ymax": None, "window_n": 40,
     "stats": False, "stats_tmin": None, "stats_tmax": None,
     "stationary": False},

    {"file": "imu", "variable": ["roll_deg", "pitch_deg", "yaw_deg"],
     "treatments": {"raw": True, "lowpass": False},
     "tmin": 0, "tmax": None, "ymin": None, "ymax": None, "window_n": 40,
     "stats": False, "stats_tmin": None, "stats_tmax": None,
     "stationary": False},
]


# Template 2 : dossiers sous Path_root.
poids = 10  # Nombre d'haltères (1 à 12), clé du bloc exporté.

# None : utiliser la fenêtre globale ; nombre : fenêtre en secondes pour ce template.
window_s = None

# Exemple : folder="8v1", file="bar30" -> 8v1/8v1_bar30.jsonl
Subplots_dossiers_differents = [

    {"folder": f"{poids}v1",
     "file": "bar30", "variable": "sink_speed",
     "tmin": 0, "tmax": None, "ymin": 0.0, "ymax": 1.5, "window_s": window_s,
     "stats": True, "stats_tmin": 40, "stats_tmax": 50,
     "stationary": True},

    {"folder": f"{poids}v2",
     "file": "bar30", "variable": "sink_speed",
     "tmin": 0, "tmax": None, "ymin": 0, "ymax": 1.5, "window_s": window_s,
     "stats": True, "stats_tmin": 40, "stats_tmax": 50,
     "stationary": True},

    {"folder": f"{poids}v3",
     "file": "bar30", "variable": "sink_speed",
     "tmin": 0, "tmax": None, "ymin": 0, "ymax": 1.5, "window_s": window_s,
     "stats": True, "stats_tmin": 40, "stats_tmax": 50,
     "stationary": True},

#   {"folder": f"{poids}v4",
#    "file": "bar30", "variable": "sink_speed",
#    "tmin": 0, "tmax": None, "ymin": 0, "ymax": 1.5, "window_s": window_s,
#    "stats": True, "stats_tmin": 40, "stats_tmax": 50,
#    "stationary": True},

#   {"folder": f"{poids}v5",
#    "file": "bar30", "variable": "sink_speed",
#    "tmin": 0, "tmax": None, "ymin": 0, "ymax": 1.5, "window_s": window_s,
#    "stats": True, "stats_tmin": 40, "stats_tmax": 50,
#    "stationary": True},

#   {"folder": f"{poids}v6",
#    "file": "bar30", "variable": "sink_speed",
#    "tmin": 0, "tmax": None, "ymin": 0, "ymax": 1.5, "window_s": window_s,
#    "stats": True, "stats_tmin": 40, "stats_tmax": 50,
#    "stationary": True},
]

# Choisir le template à utiliser :
Subplots = Subplots_meme_dossier
#Subplots = Subplots_dossiers_differents

def studied_values(value, config=None):
    """Traitements indépendants avec options globales et surcharges par subplot."""
    config = config or {}
    treatments = {**Treatments, **config.get("treatments", {})}
    window_s, window_n = config.get("window_s"), config.get("window_n")
    if window_s is None and window_n is None:
        window_s, window_n = Rolling_window_s, Rolling_window_n
    cutoff = config.get("cutoff_freq", Cutoff_freq)
    if cutoff is None:
        treatments["lowpass"] = False
    return processed_series(value, treatments, window_s=window_s, window_n=window_n,
                            center=config.get("center", Rolling_center), cutoff_freq=cutoff)


def detect_intervals(imu, start, end):
    """Combine les critères IMU activés dans la plage étudiée."""
    criteria = [(name, options) for name, options in Stationary_criteria.items()
                if options["enabled"]]
    # Couper aux sorties de cible avant de chercher les plages de faible variation.
    criteria.sort(key=lambda item: item[1].get("mode", "target") == "variation")
    intervals = [(start, end)] if criteria else []
    labels = []
    for name, options in criteria:
        signal = get_value(imu, name)
        cutoff = options.get("cutoff_freq")
        label = f"{name} brut"
        if cutoff is not None:
            signal = filter_series(signal, cutoff)
            label = f"{name} passe-bas ({cutoff:g} Hz)"
        window_s, window_n = options.get("window_s"), options.get("window_n")
        if window_s is not None or window_n is not None:
            signal = moving_average(signal, window_s=window_s, window_n=window_n)
            window = f"{window_n} valeurs" if window_n is not None else f"{window_s:g} s"
            label += f" — moyenne glissante ({window})"
        mode = options.get("mode", "target")
        thresholds = {key: options[key] for key in
                      (("target", "tolerance") if mode == "target" else ("epsilon",))}
        intervals = [interval for lo, hi in intervals
                     for interval in stationary_intervals(signal.loc[lo:hi], mode=mode,
                                                          min_duration=Stationary_min_duration,
                                                          **thresholds)]
        if mode == "target":
            label += f" : {options['target']:g} ± {options['tolerance']:g}"
        else:
            label += f" : max − min &lt; {options['epsilon']:g}"
        labels.append(label)
    return intervals, "<br>".join(labels) or "Aucun critère activé"


def build_panels(datasets):
    """Construit les courbes et les intervalles à partir des fichiers bruts."""
    panels = []
    for config in Subplots:
        folder = Path_root / config.get("folder", folder_name)
        file_name = f"{folder.name}_{config['file']}.jsonl"
        variables = config["variable"]
        if isinstance(variables, str):
            variables = [variables]
        raw_values = [get_value(datasets[folder][file_name], name) for name in variables]
        value = raw_values[0]  # Les colonnes du même fichier ont les mêmes temps.
        values = [series for raw_value in raw_values for series in studied_values(raw_value, config)]
        intervals = None
        depth = None
        sink_speed = None
        detection_label = ""
        if config.get("stationary", False):
            bar30 = datasets[folder][f"{folder.name}_bar30.jsonl"]
            depth = get_value(bar30, "depth")
            sink_speed = get_value(bar30, "sink_speed")
            cutoff = config.get("cutoff_freq", Cutoff_freq)
            if cutoff is not None:
                sink_speed = filter_series(sink_speed, cutoff)
            imu = datasets[folder][f"{Path(folder).name}_imu.jsonl"]
            # Recherche dans la plage affichée et couverte par le signal tracé.
            start = config.get("tmin")
            end = config.get("tmax")
            start = max(value.index.min(), start) if start is not None else value.index.min()
            end = min(value.index.max(), end) if end is not None else value.index.max()
            intervals, detection_label = detect_intervals(imu, start, end)
            intervals = sinking_intervals(intervals, sink_speed, depth,
                                          Min_sink_speed, Min_depth_change)
        variable_names = ", ".join(variables)
        panels.append(dict(value=values, intervals=intervals,
                           detection_label=detection_label, depth=depth, sink_speed=sink_speed,
                           tmin=config.get("tmin"), tmax=config.get("tmax"),
                           ymin=config.get("ymin"), ymax=config.get("ymax"),
                           stats=config.get("stats", False),
                           stats_tmin=config.get("stats_tmin"),
                           stats_tmax=config.get("stats_tmax"),
                           ylabel=variable_names,
                           title=f"{file_name} — {variable_names}"))
    return panels


def export_intervals(panels, destination):
    """Exporte un bloc à copier dans le dictionnaire essais de repet.py."""
    speeds, depths = [], []
    for panel in panels:
        for start, end in panel["intervals"] or []:
            speeds.append(round(float(panel["sink_speed"].loc[start:end].mean()), 3))
            depths.append(round(float(panel["depth"].loc[start:end].mean()), 3))
    destination.write_text(
        f"    {poids}: {{\n"
        f'        "v_r": {speeds},\n'
        f'        "L_touret": {depths},\n'
        "    },\n",
        encoding="utf-8",
    )


def main():
    folders = {Path_root / c.get("folder", folder_name) for c in Subplots}
    datasets = {folder: load_folder(folder) for folder in folders}
    panels = build_panels(datasets)
    export_intervals(panels, Export_file)
    fig = plot_subplots(panels)

    output = Path(__file__).resolve().parent / "plots"
    output.mkdir(exist_ok=True)
    destination = output / f"{folder_name}_subplots.html"
    fig.write_html(destination)
    if Show_plot:
        open_plot(destination)


if __name__ == "__main__":
    main()
