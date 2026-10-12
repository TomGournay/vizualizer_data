from importlib import import_module
from statistics import mean, pstdev

calculer_trainee = import_module("2pfs").calculer_trainee


#ICI JE FAIS LA MEME CHOSE QUE REPET.PY MAIS parcontre mes critères de selections d'intervales stationnaires sont plus restrictif et assure une "Bonne orientation etc"

# Par nombre d'haltères : vitesses en m/s et longueurs de touret en m.
# Les valeurs de même indice correspondent au même essai.
essais = {
    1: {
        "v_r": [0.589, 0.579, 0.573, 0.592],
        "L_touret": [23.73, 31.473, 32.745, 23.241],
    },
    2: {
        "v_r": [0.681, 0.68, 0.676],
        "L_touret": [10.008, 15.33, 17.232],
    },
    3: {
        "v_r": [0.768, 0.774, 0.754],
        "L_touret": [22.479, 13.205, 33.188],
    },
    4: {
        "v_r": [0.84, 0.843, 0.836],
        "L_touret": [15.629, 26.437, 20.881],
    },
    5: {
        "v_r": [0.91, 0.906, 0.946, 0.913, 0.92, 0.932, 0.934, 0.905],
        "L_touret": [8.743, 16.515, 4.947, 8.548, 11.897, 14.617, 17.146, 29.992],
    },
    6: {
        "v_r": [0.964, 0.957, 1.013, 1.013, 0.963, 0.976],
        "L_touret": [31.757, 39.395, 16.731, 18.876, 30.814, 35.255],
    },
    7: {
        "v_r": [1.08, 1.072, 1.075],
        "L_touret": [6.253, 16.159, 21.159],
    },
    8: {
        "v_r": [1.096, 1.13, 1.092, 1.119, 1.145],
        "L_touret": [25.847, 19.851, 32.261, 14.067, 20.01],
    },
    9: {
        "v_r": [1.17, 1.16],
        "L_touret": [17.858, 29.056],
    },
    10: {
        "v_r": [1.282, 1.223, 1.216, 1.195, 1.159, 1.26, 1.225, 1.206],
        "L_touret": [7.125, 12.614, 16.6, 20.966, 25.669, 7.154, 10.153, 15.157],
    },
    11: {
        "v_r": [1.271, 1.274, 1.28],
        "L_touret": [10.614, 18.041, 26.263],
    },
    12: {
        "v_r": [1.344, 1.314, 1.333, 1.322, 1.322, 1.339, 1.312, 1.303, 1.307, 1.336, 1.317],
        "L_touret": [7.979, 14.613, 18.496, 12.799, 16.937, 21.864, 28.938, 12.354, 16.086, 20.552, 29.273],
    },
}


if __name__ == "__main__":
    entete = (
        f"{'Essai':>5} | {'v_r (m/s)':>10} | {'L_touret (m)':>12} | "
        f"{'Traînée (N)':>12} | {'Min (N)':>10} | {'Max (N)':>10} | {'C_d (kg/m)':>10}"
    )

    points = []
    points_min = []
    points_max = []
    for nombre, mesures in essais.items():
        vitesses = mesures["v_r"]
        longueurs = mesures["L_touret"]
        if not vitesses or not longueurs:
            continue
        resultats = [
            calculer_trainee(vitesse, nombre, longueur, incertitudes=True)
            for vitesse, longueur in zip(vitesses, longueurs, strict=True)
        ]
        forces, forces_min, forces_max = zip(*resultats)
        # Coefficient global : F_d = C_d * v_r**2 (C_d en kg/m).
        coefficients = [
            force / vitesse**2
            for force, vitesse in zip(forces, vitesses)
        ]
        points.append((round(mean(vitesses), 3), round(mean(forces), 3)))
        points_min.append((round(mean(vitesses), 3), round(mean(forces_min), 3)))
        points_max.append((round(mean(vitesses), 3), round(mean(forces_max), 3)))

        print(f"\n{nombre} haltère(s) — masse nominale : {nombre * 0.5:.1f} kg")
        print(entete)
        print("-" * len(entete))
        for numero, (vitesse, longueur, force, force_min, force_max, coefficient) in enumerate(
            zip(vitesses, longueurs, forces, forces_min, forces_max, coefficients), start=1
        ):
            print(
                f"{numero:5d} | {vitesse:10.3f} | {longueur:12.3f} | "
                f"{force:12.3f} | {force_min:10.3f} | {force_max:10.3f} | {coefficient:10.3f}"
            )
        print(
            f"Moyennes : v_r = {mean(vitesses):.3f} m/s | "
            f"Traînée = {mean(forces):.3f} N | C_d = {mean(coefficients):.3f} kg/m"
        )
        print(
            f"Bornes de la traînée moyenne : min = {mean(forces_min):.3f} N | "
            f"max = {mean(forces_max):.3f} N"
        )
        print(
            f"Écarts types (population) : Traînée = {pstdev(forces):.3f} N | "
            f"C_d = {pstdev(coefficients):.3f} kg/m"
        )

    print(f"\npoints = {points}")
    print(f"points_min = {points_min}")
    print(f"points_max = {points_max}")
