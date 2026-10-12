# Utilisation

```bash
python -m pip install -r requirements.txt
python main.py
```

Dans `main.py` :
- `Path_root` : chemin général des essais, par exemple `/home/crc/data_exp_2909`.
- `folder_name` : essai du template 1, par exemple `6v3`.
- `Subplots` : une entrée par graphique, avec fichier, variable, tmin/tmax, ymin/ymax.
- `None` : borne automatique pour le fichier concerné. Axes et zooms indépendants.
- `Treatments` : active séparément les données brutes, la moyenne glissante,
  la médiane glissante et le passe-bas (courbes et calculs).
- `Rolling_window_s` OU `Rolling_window_n` : fenêtre globale des deux traitements
  glissants. `Rolling_center` choisit une fenêtre centrée ou passée.
- `window_s` OU `window_n` dans un subplot : surcharge de cette fenêtre.
  Si les deux sont absents ou `None`, la fenêtre globale s'applique.
- `Show_plot = False` : enregistrer le HTML sans ouvrir le navigateur.

Un seul graphique = une seule entrée dans `Subplots`.
Pour des calculs libres :

```python
from analysis_tools import load_folder, get_value, mean, std, moving_average

files = load_folder("/home/crc/experiment_result/data_exp/6v2")
value = get_value(files["6v2_bar30.jsonl"], "depth")
Mean = mean(value, 10, 40)
Std = std(value, 10, 40)
smooth = moving_average(value, window_n=20)
```

`main()` affiche les graphiques et exporte les coulées dans `data/coulees.txt`.
Il charge seulement les dossiers sélectionnés. Les erreurs des bibliothèques remontent directement.

## Export des coulées

À chaque exécution, `Export_file` est réécrit avec trois listes Python :

```python
v_r = [0.575, 0.569]  # m/s sinking speed
L_touret = [26.3, 37.6]  # m, profondeur
essai_haltere = [1, 1]
```

Chaque paire correspond à un intervalle retenu, dans l'ordre des panneaux puis
dans l'ordre chronologique. Les valeurs sont arrondies à trois décimales.
`v_r` est la moyenne de `sink_speed` filtré sur le signal complet avec
`Cutoff_freq` (ou `cutoff_freq` du panneau), indépendamment des courbes activées.
Une coupure `None` utilise la vitesse brute. `L_touret` est la moyenne de toutes
les mesures de profondeur brutes dans l'intervalle, bornes incluses.
`essai_haltere` répète la valeur de `poids` renseignée dans `main.py` (1 à 12),
une fois par intervalle : les trois listes ont la même longueur.

Après la détection IMU, seuls les intervalles vérifiant **les deux** critères
suivants sont conservés sur le graphique et dans l'export :

- vitesse moyenne > `Min_sink_speed = 0.05` m/s ;
- profondeur finale − profondeur initiale > `Min_depth_change = 0.20` m.

Ces seuils sont réglables dans `main.py`. La descente est positive ; les remontées
sont donc exclues. Seuls les panneaux avec `stationary=True` fournissent des
intervalles. Sans coulée retenue, les trois listes sont vides.

## Comparaison des traitements

Dans `main.py`, les quatre traitements sont activés par défaut :

```python
Treatments = {
    "raw": True,
    "moving_average": True,
    "moving_median": True,
    "lowpass": True,
}
Rolling_window_s = 5.0
Rolling_window_n = None
Rolling_center = False
Cutoff_freq = 0.2  # Hz ; None désactive le passe-bas de comparaison
```

Chaque traitement part **directement des données brutes du fichier**, sur le
signal complet avant sélection de l'intervalle. La moyenne et la médiane
glissantes ne sont donc pas appliquées au passe-bas. `sink_speed` est utilisé
tel qu'il est enregistré : sa dérivation depuis la pression n'est pas recalculée.
Les mêmes options s'appliquent aux autres variables (`depth`, accélération…).

Une surcharge partielle est possible pour chaque subplot :

```python
{"folder": "6v1", "file": "bar30", "variable": "sink_speed",
 "treatments": {"moving_median": False, "lowpass": False},
 "window_n": 40, "center": True,
 "stats": True, "stats_tmin": 10, "stats_tmax": 20}
```

Une option `False` supprime la courbe et ses calculs. Garder au moins un
traitement actif par subplot. Désactiver les deux traitements glissants dans
`treatments` pour ne pas les calculer ; `window_s=None` seul ne les désactive pas.
`cutoff_freq` permet de surcharger la coupure pour un subplot.

Pour chaque traitement et chaque variable, les statistiques affichent la
**moyenne, la médiane, l'écart type population et le nombre de valeurs** sur les
mêmes bornes. Elles sont disponibles sur l'intervalle manuel (`stats`) et sur
chaque régime stationnaire. Un intervalle vide affiche « Aucune donnée ».
L'écart type décrit la dispersion du signal traité, pas l'incertitude de sa moyenne.

Intervalles inclusifs ; moyenne des échantillons et écart type population
(`ddof=1` pour l'écart type échantillon). Les statistiques sont indépendantes
des intervalles de tracé. Le lissage est calculé avant le découpage, avec des
fenêtres partielles aux bords ; `center=True` permet une fenêtre centrée.
Les valeurs manquantes sont ignorées dans les calculs et restent des trous
sur les courbes. Les temps d'origine sont conservés sans synchronisation.

Les graphiques sont enregistrés dans `plots/` et ouverts via Windows sous WSL.
Les erreurs Python/pandas/Plotly remontent directement.

Pour afficher les statistiques à droite d'un graphique, ajoutez dans son entrée :
`"stats": True, "stats_tmin": 10, "stats_tmax": 40`.
`"stats": False` (ou absent) désactive cet affichage. `None` utilise le début/la fin
du fichier. Le calcul porte séparément sur chaque traitement activé,
indépendamment de l'intervalle affiché ; l'écart type est celui de la population (`ddof=0`).

Détection de régime stationnaire : mettre `"stationary": True` dans les subplots
concernés. Tous les réglages de détection sont communs, dans `main.py` :

```python
Stationary_criteria = {
    "xacc_robot": {"enabled": True, "mode": "target", "target": 9.81,
                   "tolerance": 0.2, "epsilon": 0.5, "cutoff_freq": 0.1},
    "pitch_deg": {"enabled": False, "target": -90.0, "tolerance": 5.0},
    "xgyro_robot": {"enabled": False, "target": 0, "tolerance": 1},
}
Stationary_min_duration = 5.0  # secondes
```

Chaque critère possède son interrupteur `enabled`. Ajouter une variable IMU
revient à ajouter une entrée au dictionnaire. Tous les critères actifs doivent
être respectés ; aucun critère actif ne produit aucun intervalle.

- `mode="target"` (par défaut) : valeurs dans `target ± tolerance`, bornes incluses.
- `mode="variation"` : `max − min < epsilon` ; `target` et `tolerance` sont ignorés.
- Les seuils sont dans l'unité de la variable ; la cible est signée.
- `cutoff_freq` : passe-bas en Hz ; absent ou `None` utilise les données brutes.
- `window_s` OU `window_n` : moyenne glissante en secondes ou en points,
  appliquée après le passe-bas ; absents ou `None` désactivent ce lissage.

Le filtrage de chaque critère part du signal complet, indépendamment des courbes.
La recherche se limite ensuite à tmin/tmax et à la période couverte par le tracé.
Les critères de cible découpent d'abord les plages admissibles, puis les critères
de variation les découpent à leur tour, dans l'ordre du dictionnaire.
Chaque intervalle final dure au moins `Stationary_min_duration`.
Une valeur manquante coupe l'intervalle ; les trous sans échantillon ne sont pas évalués.
La sélection des coulées par vitesse et profondeur s'applique ensuite.

Les deux templates utilisent ces mêmes réglages. Pour retrouver les anciens
réglages du template 2 : cible `-9.81`, tolérance `0.03`, durée minimale `1.0`.

Chaque intervalle est surligné et numéroté R1, R2… Ses statistiques sont calculées
sur chaque courbe activée, avec ses propres horodatages. Les critères et leurs
traitements sont indiqués à droite. Les statistiques manuelles restent indépendantes.

Dans le template 2, préciser le dossier et le type de fichier :
```python
{"folder": "8v1", "file": "bar30", "variable": "sink_speed", "stationary": True}
```
Le fichier lu est `Path_root/8v1/8v1_bar30.jsonl`. Dans le template 1,
ommettre `folder` utilise `folder_name`.

Plusieurs variables sur le même subplot :
```python
{"file": "imu", "variable": ["xacc_robot", "yacc_robot", "zacc_robot"],
 "tmin": 0, "tmax": None, "window_n": 40}
```
Les variables partagent les axes et les intervalles détectés. Leurs traitements
et statistiques sont calculés séparément.

`filtre.py` utilise un Butterworth d'ordre 4 avec `sosfiltfilt`.
La fréquence d'échantillonnage est estimée pour chaque fichier par
`1 / médiane(diff(time))` : les temps doivent être en secondes et presque réguliers.
La coupure doit être positive et inférieure à `fs / 2` pour chaque fichier.
Les signaux doivent être sans valeurs manquantes et avoir plus de 15 échantillons.

Pour filtrer directement un tableau (temps sur l'axe 0) :
```python
from filtre import apply_filter
filtered = apply_filter(data, fs=100, cutoff_freq=2)
```

Pour chaque régime, les profondeurs de `<nom_du_dossier>_bar30.jsonl` sont
également affichées à droite : première mesure à partir de tmin et dernière
mesure jusqu'à tmax, en restant dans l'intervalle (bornes incluses). Leurs temps
exacts sont indiqués, ainsi que la moyenne de toutes les profondeurs de l'intervalle.
Sans profondeur disponible dans l'intervalle, une mention le signale.
Ces profondeurs sont celles du fichier brut, indépendamment des traitements.

Vérification des calculs et des options : `python -m unittest discover -s data -p "test_processing.py"`
depuis la racine du projet.
