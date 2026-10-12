# Analyse de l'essai « vague »

Données sources : /home/crc/data_exp_2909/vague ; durée 61,5 s.
Contexte indiqué : capteur au fond de l'eau, mouvements résiduels possibles sous l'effet des courants.
Les données originales et le visualiseur existant n'ont pas été modifiés.

## Résultats
Deux composantes communes à la profondeur et aux accélérations : environ 0,21–0,22 Hz
(période 4,5–4,8 s) et 0,28 Hz (3,6 s).
La résolution spectrale est de 0,016 Hz sur tout l'essai et 0,020 Hz sur 8–58 s.
Sur deux sous-intervalles de 25 s, les pics évoluent et leur résolution se dégrade
à 0,040 Hz : il ne s'agit pas d'une sinusoïde stable à une fréquence exacte.

Amplitudes équivalentes des oscillations dans la bande 0,15–0,40 Hz,
mesurées entre 10 et 55 s :

| Signal | Amplitude équivalente A | Crête à crête équivalent 2A |
|---|---:|---:|
| Profondeur apparente | 2,60 mm | 5,21 mm |
| Vitesse sink_speed | 0,00395 m/s | 0,00791 m/s |
| Accélération x robot | 0,0531 m/s² | 0,106 m/s² |
| Accélération y robot | 0,00392 m/s² | 0,00785 m/s² |
| Accélération z robot | 0,0689 m/s² | 0,138 m/s² |

A = sqrt(2) × écart type du signal isolé dans la bande.
Ces valeurs résument l'ensemble de la bande ; ce ne sont ni les maxima observés,
ni les amplitudes de chacun des deux pics. L'amplitude varie au cours de l'essai.
L'écart percentile 95–5 de la profondeur dans cette bande est 6,80 mm.
Le filtre utilisé pour isoler la bande atténue les composantes proches de ses bornes.

La hauteur des vagues en surface ne peut pas être déduite directement de ces
millimètres : le capteur mesure une pression convertie en profondeur, avec de
possibles mouvements du support. L'IMU en repère robot mélange aussi accélérations
de mouvement et projection de la gravité si l'orientation change.

La profondeur brute présente une dérive lente et une excursion totale de 16,7 cm,
bien supérieure à l'oscillation isolée. Cette dérive n'est pas identifiée comme une
vague et sera conservée par un passe-bas. Sa cause reste à déterminer.
sink_speed est exactement la différence de profondeur divisée par le temps
entre échantillons (erreur RMS de vérification : 0). Son bruit rapide, jusqu'à
environ ±0,21 m/s, ne doit donc pas être pris comme amplitude des vagues.

## Réglage initial proposé
Pour estimer une tendance lente de profondeur ou de vitesse : Butterworth
passe-bas d'ordre 2, fréquence de coupure 0,10 Hz. Tester 0,08 Hz si un lissage
plus fort est acceptable. Ce choix reste à valider sur un essai avec les vrais
mouvements à conserver : il atténuera aussi les mouvements utiles dans la même bande.

Pour une passe causale à 0,10 Hz, les amplitudes à 0,21 et 0,28 Hz sont
multipliées respectivement par 0,221 et 0,126 (réductions de 78 % et 87 %).
Il introduit du retard ; son retard de groupe aux très basses fréquences est
d'environ 2,25 s. L'initialisation et les transitions doivent être prises en compte.

Pour un traitement hors ligne aller-retour (sosfiltfilt), les facteurs sont
0,0489 et 0,0160 (réductions de 95 % et 98 %), sans déphasage.
Ce traitement nécessite les données futures, n'est pas utilisable tel quel en
temps réel et sa réponse en amplitude est le carré de celle d'une passe.
Les graphiques de comparaison utilisent cette version hors ligne ; les bords
de l'enregistrement restent sensibles aux conditions de prolongement.

Exemple sur un signal rééchantillonné régulièrement (fs en Hz) :

```python
from scipy.signal import butter, sosfilt, sosfilt_zi, sosfiltfilt
sos = butter(2, 0.10, btype="lowpass", fs=fs, output="sos")
offline = sosfiltfilt(sos, signal_regulier)
temps_reel, etat = sosfilt(
    sos, signal_regulier, zi=sosfilt_zi(sos) * signal_regulier[0]
)
# En traitement par blocs, conserver etat comme zi du bloc suivant.
```

Le visualiseur propose déjà une moyenne glissante de 5 s sur sink_speed.
Elle constitue un essai simple : gain théorique continu d'environ 0,047
à 0,21 Hz mais 0,216 à 0,28 Hz ; retard d'environ 2,5 s en mode non centré.
Elle ne supprime donc pas uniformément toute la bande.
Privilégier window_s=5 plutôt qu'un nombre fixe de points lorsque les temps varient.
Le choix définitif dépend de la rapidité des mouvements utiles et du retard admissible.

## Méthode et reproductibilité
1. Vérification des temps strictement croissants et des valeurs finies.
2. Interpolation linéaire sur grille régulière à l'inverse du pas médian :
   22,64 Hz pour Bar30 ; 189,49 Hz pour IMU.
   Fréquences moyennes réellement acquises : 22,38 et 195,15 Hz.
   Le rééchantillonnage peut modifier le bruit proche de Nyquist ; les
   conclusions recherchées portent sur les basses fréquences.
3. Spectres par périodogramme, fenêtre de Hann, retrait de la tendance linéaire.
4. Comparaison essai complet, 8–58 s et deux segments de 25 s.
5. Isolation 0,15–0,40 Hz par Butterworth d'ordre 3 aller-retour,
   statistiques sur 10–55 s pour limiter transitoires et effets de bord.
   Les amplitudes sont donc dépendantes de cette bande et de cet intervalle.
6. Comparaison de deux passe-bas hors ligne sur la vitesse brute rééchantillonnée.

Exécution sous WSL, avec les bibliothèques système disponibles :
```bash
cd /home/crc/vizualizer_data/vague
python3 -s analyse_vague.py
```

Fichiers : analyse_vague.py, resultats.json, analyse_vague.png,
comparaison_filtres.png ; diagnostic.png et diagnostic.json montrent l'examen initial.

Références API :
- [Butterworth / fréquence de coupure](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.butter.html)
- [Filtrage aller-retour](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.sosfiltfilt.html)
- [Filtrage causal](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.sosfilt.html)
