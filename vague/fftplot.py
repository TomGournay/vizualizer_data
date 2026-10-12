import json
import re
from textwrap import fill
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks


DOSSIER = Path(__file__).resolve().parent / "data_filtre"
SOURCES = Path("/home/crc/experiment_result/data_exp")
VARIABLE = "pa"
FREQUENCE_MIN = 0  # Hz : inclure les très basses fréquences, sauf la moyenne à 0 Hz.
FREQUENCE_MAX = 2  # Hz
HAUTEUR_MIN = 0.25  # Amplitude du pic >= 25 % du maximum de son essai dans la bande.
PROMINENCE = 0.03  # Relief du pic >= 3 % du même maximum.
ANNOTER_PICS = True  # Fréquences sur le graphique ; valeurs aussi dans pics_fft.json.
AFFICHER_LEGENDES = True  # État initial ; Ctrl+L pour basculer dans la fenêtre.
COLONNES = 2  # Nombre de poids par ligne ; deux graphiques par poids.
MARGE = 10  # Secondes de contexte avant et après les portions conservées.


def lire_signal(fichier):
    with fichier.open(encoding="utf-8") as f:
        data = [json.loads(line) for line in f if line.strip()]
    t = np.array([d["time"] for d in data])
    x = np.array([d[VARIABLE] for d in data])
    return t, x


def detecter_pics(freq, fft):
    """Maxima assez hauts et proéminents, sans limite de nombre.

    Exclure 0 Hz avant la détection évite de transformer une simple décroissance
    en pic artificiel au premier point. Un pic au bord de la bande choisie est
    accepté si ses voisins dans le spectre complet confirment un maximum.
    """
    bande = np.flatnonzero((freq > 0) & (freq >= FREQUENCE_MIN) & (freq <= FREQUENCE_MAX))
    if len(bande) == 0:
        return np.array([], dtype=int)
    maximum = fft[bande].max()
    pics, _ = find_peaks(
        fft[1:], height=HAUTEUR_MIN * maximum, prominence=PROMINENCE * maximum,
    )
    pics += 1
    return pics[(freq[pics] >= FREQUENCE_MIN) & (freq[pics] <= FREQUENCE_MAX)]


groupes = {}
for fichier in sorted(DOSSIER.glob("*_bar30_apres_chute.jsonl")):
    nom = fichier.name.removesuffix("_bar30_apres_chute.jsonl")
    essai = re.fullmatch(r"(\d+)v(\d+)", nom)
    poids = int(essai[1]) if essai else None
    groupes.setdefault(poids, []).append((nom, fichier))

poids = sorted(p for p in groupes if p is not None)
if None in groupes:
    poids.append(None)

lignes = (len(poids) + COLONNES - 1) // COLONNES
fig, axes = plt.subplots(
    lignes, 2 * COLONNES, figsize=(20, 3.5 * lignes),
    squeeze=False, layout="constrained",
)

resultats = {}
for (ax_temps, ax_fft), p in zip(axes.reshape(-1, 2), poids):
    debut, fin = np.inf, -np.inf
    etiquette_y = 0.70
    for i, (nom, fichier) in enumerate(groupes[p]):
        t, x = lire_signal(fichier)
        t_source, x_source = lire_signal(SOURCES / nom / f"{nom}_bar30.jsonl")
        contexte = (t_source >= t[0] - MARGE) & (t_source <= t[-1] + MARGE)
        ax_temps.plot(
            t_source[contexte], x_source[contexte], color="0.7", linewidth=0.8,
            label="Original" if i == 0 else None,
        )
        courbe, = ax_temps.plot(
            t, x, label=f"{nom} : {t[0]:.1f}–{t[-1]:.1f} s", zorder=3,
        )
        couleur = courbe.get_color()
        ax_temps.scatter(t[[0, -1]], x[[0, -1]], color=couleur, s=15, zorder=4)
        debut, fin = min(debut, t[0]), max(fin, t[-1])

        duree = t[-1] - t[0]
        dt = duree / (len(t) - 1)
        freq = np.fft.rfftfreq(len(x), d=dt)
        # Retirer la moyenne et normaliser pour comparer des longueurs différentes.
        fft = np.abs(np.fft.rfft(x - x.mean())) / len(x)

        ax_fft.plot(
            freq[1:], fft[1:], color=couleur,
            label=f"{nom} ({duree:.1f} s, Δf={freq[1]:.3f} Hz)",
        )
        pics = detecter_pics(freq, fft)
        ax_fft.scatter(freq[pics], fft[pics], color=couleur, marker="v", s=30, zorder=4)
        # Un maximum dès le premier point positif est dominant, mais non résolu.
        bande = (freq > 0) & (freq >= FREQUENCE_MIN) & (freq <= FREQUENCE_MAX)
        bord = (
            len(fft) > 2 and bande[1] and fft[1] > fft[2]
            and fft[1] == fft[bande].max()
        )
        resultats[nom] = {
            "espacement_hz": float(freq[1]),
            "pics": [
                {"frequence_hz": float(freq[pic]), "module_fft_normalise": float(fft[pic])}
                for pic in pics
            ],
            "bord_basse_frequence_non_resolu": (
                {"frequence_hz": float(freq[1]), "module_fft_normalise": float(fft[1])}
                if bord else None
            ),
        }
        if bord:
            ax_fft.scatter(freq[1], fft[1], edgecolors=couleur, facecolors="none", s=45, zorder=4)
        if ANNOTER_PICS:
            valeurs = [f"{freq[pic]:.3f}" for pic in pics]
            if bord:
                valeurs.insert(0, f"{freq[1]:.3f} (bord)")
            if valeurs:
                texte = fill(f"{nom} : {', '.join(valeurs)} Hz", width=36)
                ax_fft.text(
                    0.97, etiquette_y, texte, transform=ax_fft.transAxes,
                    ha="right", va="top", color=couleur, fontsize=8,
                    bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85},
                )
                etiquette_y -= 0.055 * (texte.count("\n") + 1) + 0.035

    titre = f"Poids {p}" if p is not None else "Autres essais"
    ax_temps.set(
        title=f"{titre} — découpage", xlabel="Temps original (s)",
        ylabel=VARIABLE, xlim=(debut - MARGE, fin + MARGE),
    )
    ax_fft.set(
        title=f"{titre} — FFT", xlabel="Fréquence (Hz, pas moyen)",
        ylabel=f"Module FFT / N — {VARIABLE}", xlim=(0, FREQUENCE_MAX),
    )
    ax_fft.margins(y=0.25)
    ax_fft.set_ylim(bottom=0)
    for ax in (ax_temps, ax_fft):
        ax.grid(alpha=0.3)
        legende = ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.25))
        legende.set_visible(AFFICHER_LEGENDES)

for ax in list(axes.flat)[2 * len(poids):]:
    ax.set_visible(False)


def basculer_legendes(event):
    if event.key == "ctrl+l":
        for ax in axes.flat:
            legende = ax.get_legend()
            if legende is not None:
                legende.set_visible(not legende.get_visible())
        fig.canvas.draw_idle()


fig.canvas.mpl_connect("key_press_event", basculer_legendes)

fig.suptitle(
    "Découpage et FFT — pics dominants en triangles ; cercles : maximum basse fréquence au bord, non résolu"
)
fig.savefig(DOSSIER.parent / "fft_crops.png", dpi=150)
(DOSSIER.parent / "pics_fft.json").write_text(
    json.dumps(resultats, indent=2, ensure_ascii=False), encoding="utf-8",
)
plt.show()
