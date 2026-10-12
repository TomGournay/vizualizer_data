"""Copie la première phase calme après la chute, sans modifier les mesures."""

import json
from pathlib import Path

import numpy as np


DOSSIER = Path("/home/crc/experiment_result/data_exp")
VARIABLE = "pa"  # "pa", "mbar", "depth" ou "sink_speed"
MODE = "variation"  # "variation" : max-min <= SEUIL ; "plage" : dans PLAGE
SEUIL = 500  # Dans l'unité de VARIABLE : ici, Pa.
PLAGE = (-0.2, 0.2)  # Pour VARIABLE = "sink_speed" et MODE = "plage", en m/s.
DUREE = 5  # Durée minimale de calme, en secondes.
APRES = None  # Temps minimal de recherche ; None : après le pic de |sink_speed|.
JUSQU_A_LA_FIN = False  # True : conserver aussi les éventuels mouvements suivants.


def intervalle_calme(t, x, apres, mode, seuil, plage, duree):
    """Indices [début, fin[ du premier intervalle calme assez long, ou None.

    Le critère porte sur tout l'intervalle, pas sur deux points successifs.
    """
    if mode not in ("variation", "plage"):
        raise ValueError("MODE doit être 'variation' ou 'plage'.")
    if duree <= 0 or seuil < 0 or plage[0] > plage[1]:
        raise ValueError("Vérifier DUREE, SEUIL et PLAGE.")
    if not np.all(np.isfinite(t)) or not np.all(np.diff(t) > 0):
        raise ValueError("Les temps doivent être finis et strictement croissants.")

    def calme(bas, haut):
        if mode == "variation":
            return haut - bas <= seuil
        return plage[0] <= bas and haut <= plage[1]

    for debut in range(np.searchsorted(t, apres, side="right"), len(t)):
        dernier = np.searchsorted(t, t[debut] + duree)
        if dernier == len(t):
            break
        fenetre = x[debut:dernier + 1]
        if not np.all(np.isfinite(fenetre)):
            continue
        bas, haut = np.min(fenetre), np.max(fenetre)
        if not calme(bas, haut):
            continue

        fin = dernier + 1
        while fin < len(t) and np.isfinite(x[fin]):
            bas, haut = min(bas, x[fin]), max(haut, x[fin])
            if not calme(bas, haut):
                break
            fin += 1
        return debut, fin
    return None


def decouper(source):
    with source.open(encoding="utf-8") as fichier:
        lignes = [ligne for ligne in fichier if ligne.strip()]
    donnees = [json.loads(ligne) for ligne in lignes]
    t = np.array([d["time"] for d in donnees])
    x = np.array([d[VARIABLE] for d in donnees])
    vitesse = np.array([d["sink_speed"] for d in donnees])
    apres = t[np.nanargmax(np.abs(vitesse))] if APRES is None else APRES
    intervalle = intervalle_calme(t, x, apres, MODE, SEUIL, PLAGE, DUREE)
    if intervalle is None:
        return False  # Aucun fichier créé si aucun intervalle ne convient.

    debut, fin = intervalle
    if JUSQU_A_LA_FIN:
        fin = len(t)
    sortie = Path(__file__).resolve().parent / f"{source.stem}_apres_chute.jsonl"
    with sortie.open("w", encoding="utf-8") as fichier:
        fichier.writelines(lignes[debut:fin])
    print(f"{sortie.name} : {t[debut]:.2f} à {t[fin - 1]:.2f} s ({fin - debut} mesures)")
    return True


def main():
    sources = sorted(DOSSIER.rglob("*_bar30.jsonl"))
    copies = 0
    invalides = []
    for source in sources:
        try:
            copies += decouper(source)
        except json.JSONDecodeError:
            invalides.append(source.name)
    sans_intervalle = len(sources) - copies - len(invalides)
    print(f"{copies} copies ; {sans_intervalle} sans intervalle calme ; {len(invalides)} fichiers JSON invalides.")
    if invalides:
        print("Fichiers ignorés : " + ", ".join(invalides))


if __name__ == "__main__":
    main()
