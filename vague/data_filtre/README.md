# Découpage après la chute

Depuis `vague/data_filtre`, lancer `python3 crop.py` (NumPy requis).
Régler `DOSSIER` et les paramètres en haut de `crop.py`.
Le script parcourt tous ses sous-dossiers et traite chaque fichier
`*_bar30.jsonl`, avec les mêmes paramètres. Par défaut, il parcourt
`/home/crc/experiment_result/data_exp`. Les fichiers IMU et les métadonnées
ne sont pas concernés.

Le script copie toutes les colonnes des lignes retenues dans
`<nom_original>_apres_chute.jsonl`, à côté du script. Les temps et les mesures
restent inchangés : aucun lissage, aucune interpolation, aucun filtrage.
Le fichier original reste intact. Relancer remplace seulement la copie découpée.
Si aucun intervalle ne convient, rien n'est écrit ; une ancienne copie reste donc
inchangée. Chaque copie écrite est indiquée, puis un bilan donne le nombre
de copies, d'essais sans intervalle calme et de fichiers JSON invalides.
Les fichiers JSON corrompus sont ignorés entièrement et leurs noms sont indiqués
dans le bilan ; les autres essais continuent d'être traités.

## Critères

- Pression quasi constante : `VARIABLE = "pa"`, `MODE = "variation"`,
  `SEUIL = 500` signifie `max(pa) - min(pa) <= 500 Pa` sur l'intervalle entier.
- Vitesse proche de zéro : `VARIABLE = "sink_speed"`, `MODE = "plage"`,
  `PLAGE = (-0.2, 0.2)` signifie que chaque vitesse est dans cette plage, en m/s.
- Faible variation de vitesse : `VARIABLE = "sink_speed"`, `MODE = "variation"`,
  puis `SEUIL` en m/s. Attention : ce critère accepte aussi une chute à vitesse
  constante ; préférer la plage autour de zéro pour détecter l'arrêt.

`DUREE = 5` exige au moins cinq secondes consécutives admissibles. Le découpage
commence au début de cette phase, puis la prolonge tant que le critère reste
respecté sur tout l'intervalle. Un seul point hors critère termine la copie.
Les temps doivent être croissants et l'acquisition continue : les trous sans
mesures ne sont pas évalués. Les valeurs non finies coupent les phases calmes.

Par défaut, la recherche commence après le pic de vitesse absolue pour éviter
le calme avant la chute. C'est une heuristique adaptée à un essai avec une chute :
si un pic parasite ou une autre manœuvre domine, régler `APRES` à un temps situé
pendant la chute. `JUSQU_A_LA_FIN = True` conserve tout après le début détecté,
y compris une éventuelle remontée. Par défaut, seul le premier intervalle calme
est conservé, sans assembler des morceaux séparés.

## Choix du signal

Dans les essais examinés, `sink_speed` est la différence de profondeur divisée
par le pas de temps ; elle amplifie le bruit. La variation de pression est donc
un bon point de départ pour la détection, avec un seuil et une durée à adapter
aux oscillations que l'on veut conserver. Les valeurs par défaut sont des
réglages initiaux, pas une calibration universelle. Une pression quasi constante
ne prouve pas que tout le signal restant est du bruit : les vagues peuvent aussi
y contribuer. Une dérive lente peut écourter l'intervalle puisque le critère
max-min porte sur toute sa durée.
