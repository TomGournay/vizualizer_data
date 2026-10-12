from importlib import import_module
from math import exp, sqrt

calculer_trainee = import_module("2pfs").calculer_trainee


Theta0_deg = 15.0
Poids_min = 0.05

# Blocs exportés par prod.py : vitesses en m/s, longueurs en m et d en degrés.
# Les valeurs de même indice correspondent au même essai.
essais = {
    1: {
        "v_r": [0.589, 0.579, 0.573, 0.592],
        "L_touret": [23.73, 31.473, 32.745, 23.241],
        "d": [36.75, 27.97, 19.622, 102.717],
    },
    2: {
        "v_r": [0.681, 0.68, 0.676],
        "L_touret": [10.008, 15.33, 17.232],
        "d": [16.048, 22.386, 74.407],
    },
    3: {
        "v_r": [0.768, 0.774, 0.754],
        "L_touret": [22.479, 13.205, 33.188],
        "d": [33.325, 100.64, 21.986],
    },
    4: {
        "v_r": [0.84, 0.843, 0.836],
        "L_touret": [15.629, 26.437, 20.881],
        "d": [27.446, 143.168, 18.852],
    },
    5: {
        "v_r": [0.91, 0.906, 0.946, 0.913, 0.92, 0.932, 0.934, 0.905],
        "L_touret": [8.743, 16.515, 4.947, 8.548, 11.897, 14.617, 17.146, 29.992],
        "d": [128.571, 140.92, 101.901, 80.007, 60.833, 15.262, 47.28, 89.771],
    },
    6: {
        "v_r": [0.964, 1.013, 1.013, 0.963, 0.976],
        "L_touret": [31.649, 16.731, 18.876, 30.814, 35.255],
        "d": [135.918, 34.552, 55.734, 82.282, 51.085],
    },
    7: {
        "v_r": [1.08, 1.072, 1.075],
        "L_touret": [6.253, 16.159, 20.03],
        "d": [55.468, 77.711, 71.409],
    },
    8: {
        "v_r": [1.096, 1.13, 1.092, 1.124],
        "L_touret": [25.847, 19.851, 32.261, 14.726],
        "d": [47.828, 71.617, 63.279, 38.307],
    },
    9: {
        "v_r": [1.173],
        "L_touret": [18.584],
        "d": [168.158],
    },
    10: {
        "v_r": [1.282, 1.217, 1.26, 1.225, 1.205],
        "L_touret": [7.125, 16.22, 7.154, 10.153, 15.163],
        "d": [12.6, 47.163, 28.538, 38.549, 56.227],
    },
    11: {
        "v_r": [1.271, 1.278, 1.286, 1.273, 1.287],
        "L_touret": [10.614, 18.646, 11.146, 15.124, 17.855],
        "d": [148.967, 123.694, 111.154, 56.786, 118.668],
    },
    12: {
        "v_r": [1.344, 1.314, 1.333, 1.322, 1.322, 1.339, 1.336],
        "L_touret": [7.979, 14.613, 18.496, 12.799, 16.937, 21.864, 20.552],
        "d": [41.199, 68.407, 47.422, 32.495, 48.729, 22.702, 105.654],
    },
}


def poids_attitude(d):
    return max(Poids_min, exp(-0.5 * (d / Theta0_deg)**2))


def moyenne_ponderee(valeurs, poids):
    return sum(valeur * poids_i for valeur, poids_i in zip(valeurs, poids, strict=True)) / sum(poids)


def ecart_type_pondere(valeurs, poids):
    moyenne = moyenne_ponderee(valeurs, poids)
    return sqrt(moyenne_ponderee([(valeur - moyenne)**2 for valeur in valeurs], poids))


if __name__ == "__main__":
    entete = (
        f"{'Essai':>5} | {'v_r (m/s)':>10} | {'L_touret (m)':>12} | "
        f"{'d (°)':>8} | {'w_i':>8} | "
        f"{'Traînée (N)':>12} | {'Min (N)':>10} | {'Max (N)':>10} | {'C_d (kg/m)':>10}"
    )

    points = []
    points_min = []
    points_max = []
    poids = []
    for nombre, mesures in essais.items():
        vitesses = mesures["v_r"]
        longueurs = mesures["L_touret"]
        deviations = mesures["d"]
        print(f"\n{nombre} haltère(s) — masse nominale : {nombre * 0.5:.1f} kg")
        print(entete)
        print("-" * len(entete))
        if not vitesses and not longueurs and not deviations:
            print()
            continue
        poids_intervalles = [poids_attitude(d) for d in deviations]
        resultats = [
            calculer_trainee(vitesse, nombre, longueur, incertitudes=True)
            for vitesse, longueur, d in zip(vitesses, longueurs, deviations, strict=True)
        ]
        forces, forces_min, forces_max = zip(*resultats)
        # Coefficient global : F_d = C_d * v_r**2 (C_d en kg/m).
        coefficients = [
            force / vitesse**2
            for force, vitesse in zip(forces, vitesses)
        ]
        vitesse_moyenne = moyenne_ponderee(vitesses, poids_intervalles)
        force_moyenne = moyenne_ponderee(forces, poids_intervalles)
        force_min_moyenne = moyenne_ponderee(forces_min, poids_intervalles)
        force_max_moyenne = moyenne_ponderee(forces_max, poids_intervalles)
        coefficient_moyen = moyenne_ponderee(coefficients, poids_intervalles)
        poids_moyen = moyenne_ponderee(poids_intervalles, poids_intervalles)
        points.append((round(vitesse_moyenne, 3), round(force_moyenne, 3)))
        points_min.append((round(vitesse_moyenne, 3), round(force_min_moyenne, 3)))
        points_max.append((round(vitesse_moyenne, 3), round(force_max_moyenne, 3)))
        poids.append(round(poids_moyen, 6))

        for numero, (vitesse, longueur, d, poids_i, force, force_min, force_max, coefficient) in enumerate(
            zip(vitesses, longueurs, deviations, poids_intervalles,
                forces, forces_min, forces_max, coefficients, strict=True), start=1
        ):
            print(
                f"{numero:5d} | {vitesse:10.3f} | {longueur:12.3f} | "
                f"{d:8.3f} | {poids_i:8.4f} | "
                f"{force:12.3f} | {force_min:10.3f} | {force_max:10.3f} | {coefficient:10.3f}"
            )
        print(
            f"Moyennes pondérées : v_r = {vitesse_moyenne:.3f} m/s | "
            f"Traînée = {force_moyenne:.3f} N | C_d = {coefficient_moyen:.3f} kg/m | "
            f"Poids moyen = {poids_moyen:.4f}"
        )
        print(
            f"Bornes de la traînée moyenne pondérée : min = {force_min_moyenne:.3f} N | "
            f"max = {force_max_moyenne:.3f} N"
        )
        print(
            f"Écarts types pondérés (population) : "
            f"Traînée = {ecart_type_pondere(forces, poids_intervalles):.3f} N | "
            f"C_d = {ecart_type_pondere(coefficients, poids_intervalles):.3f} kg/m"
        )

    print(f"\npoints = {points}")
    print(f"points_min = {points_min}")
    print(f"points_max = {points_max}")
    print(f"poids = {poids}")
