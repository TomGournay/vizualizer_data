# Sensibilité des seuils de stationnarité

Depuis la racine du projet, dans WSL :

```bash
python3 -B -m sensi.sensi
```

Les réglages sont en tête de `sensi.py` :
- `Path_root` : dossier des données, par défaut `experiment_result/data_exp` à côté du projet.
- `Poids` et `Repetitions` : sélection des dossiers disponibles ; `None` sélectionne tout.
- `Stationary_criteria` : référence, cibles, seuils et filtres IMU.
- `Sweep_values` : valeurs plus strictes et plus permissives, axe par axe, et durée `min_duration_s`.
- `Contexts` : multiplicateurs des seuils des **autres capteurs** (1, 1.5 et 2).

Le paramètre étudié prend les valeurs de sa liste ; il n'est pas multiplié par le contexte.
Sa valeur de référence est toujours incluse. La durée minimale reste à `Stationary_min_duration`
(2 s) pendant les balayages des capteurs. Pendant son propre balayage, seule cette durée
varie et les seuils des capteurs restent fixes dans chaque contexte ; aucun multiplicateur
ne s'applique à la durée. Les cibles, le filtrage et les conditions de descente restent fixes.

Le roll mesure la stabilité par `max−min` sur les angles dépliés, sans cible d'orientation.
Le yaw mesure l'écart circulaire autour de 0° : 359° équivaut à −1° ; sa tolérance
de référence est 180°. Le roll a aussi une référence permissive de 180° :
les petits seuils suppriment presque toutes les mesures dans ces données.
Les deux seuils sont balayés sur
`[1, 2, 3, 4, 6, 8, 10, 15, 20, 30, 45, 60, 90, 120, 180]` degrés,
avec en plus `270` et `360` degrés pour le roll. Une variation sur un angle déplié
peut dépasser 180°, tandis que l'écart circulaire du yaw reste entre −180° et 180°.
La durée minimale est balayée sur `[0.5, 1, 1.5, 2, 3, 4, 5, 8, 10]` secondes.
Un seuil angulaire plus petit est plus restrictif ; une durée minimale plus grande l'est aussi.

Les signaux sont chargés et filtrés une seule fois. L'ordre de découpage existant reste
inchangé : cibles, puis variations. Aucune exclusion des vitesses atypiques n'est appliquée.

## Une mesure par descente

Chaque dossier (`9v1`, `9v2`…) identifie une descente. Pour chaque réglage, on sélectionne
l'union des échantillons BAR30 dans les intervalles stationnaires descendants.
La vitesse et la profondeur sont moyennées sur ces échantillons, puis transmises à
`pfs.pfs.calculer_trainee`. Les trous entre intervalles sont exclus et les bornes communes
ne sont pas comptées deux fois. Les moyennes sont par échantillon, pas par fragment.
La profondeur moyenne est assimilée à la longueur de touret, comme précédemment.

Sans détection : durée et nombre d'échantillons à zéro, vitesse/profondeur/force absentes.
La référence peut donc être absente pour un dossier qui devient mesurable
avec d'autres seuils. Les calculs précèdent tout arrondi d'affichage.

## Comparaisons

Chaque ligne du balayage contient :
- `trainee_N` : force de cette descente avec ce seuil et ce contexte ;
- `delta_reference_N` : différence avec tous les réglages initiaux ;
- `delta_contexte_N` et `delta_contexte_pct` : différence avec le seuil étudié remis à sa
  référence, **les autres critères restant dans le même contexte**.

Les différences restent absentes si la mesure ou sa référence manque. Le pourcentage
est aussi absent si la force de comparaison est nulle. Trois contextes explorent des
interactions, sans couvrir toutes les combinaisons. Les plages sont exploratoires :
une force stable ne garantit pas à elle seule la validité physique du régime stationnaire.

## Résultats dans `resultats/`

- `reference.html` : référence par descente, fragments repérés sur vitesse/profondeur,
  et liens vers les graphiques de sensibilité par poids.
- `sensibilite_{poids}.html` : pour chaque paramètre, force et durée selon le seuil ;
  une colonne par contexte et une courbe par descente. Les forces absentes coupent les courbes.
- `reference.csv` : une ligne par descente, y compris sans détection.
- `reference_intervalles.csv` : détails des fragments de la référence.
- `par_poids.csv` : moyenne et écart type population des forces par descente ;
  chaque descente mesurée a le même poids dans la synthèse.
- `sensibilite.csv` : tous les résultats et différences, sans arrondi imposé.
- `parametres.json` : paramètres de l'exécution.
- `plotly.min.js` : bibliothèque partagée pour consulter les rapports hors connexion.

`sensi.py` calcule, `plots.py` trace, `repet.py` résume les forces par poids.
Cette version remplace la référence précédente par intervalle : les synthèses sont
maintenant calculées par descente complète.

Vérification ciblée : `python3 -B -m unittest sensi.test_sensi`.
