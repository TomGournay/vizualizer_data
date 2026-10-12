from statistics import mean, pstdev

from pfs import calculer_trainee


# Par nombre d'haltères : vitesses en m/s et longueurs de touret en m.
# Les valeurs de même indice correspondent au même essai.
essais = {
    1: {
        "v_r": [0.576, 0.57, 0.591, 0.572, 0.579, 0.568],
        "L_touret": [26.355, 37.615, 23.069, 32.922, 26.258, 36.699],
    },
    2: {
        "v_r": [0.675, 0.658, 0.681, 0.665, 0.676, 0.663],
        "L_touret": [24.031, 34.928, 20.355, 33.42, 21.805, 29.484],
    },
    3: {
        "v_r": [0.753, 0.758, 0.768],
        "L_touret": [30.217, 21.082, 13.745],
    },
    4: {
        "v_r": [0.842, 0.851, 0.83, 0.86],
        "L_touret": [13.051, 9.245, 25.218, 12.094],
    },
    5: {
        "v_r": [0.915, 0.872, 0.927, 0.91],
        "L_touret": [8.865, 26.767, 13.114, 16.915],
    },
    6: {
        "v_r": [0.973, 0.984, 0.972, 1.0, 0.989, 0.978, 0.993, 0.995, 0.972, 0.973],
        "L_touret": [11.57, 24.191, 34.118, 7.781, 23.418, 34.215, 7.391, 23.843, 32.817, 36.095],
    },
    7: {
        "v_r": [1.07, 1.054, 1.026, 1.069, 1.075, 1.068, 1.064, 1.03],
        "L_touret": [7.592, 21.285, 31.472, 8.007, 20.345, 7.12, 21.544, 31.275],
    },
    8: {
        "v_r": [1.117, 1.119, 1.092, 1.104, 1.123, 1.093, 1.132, 1.096],
        "L_touret": [9.761, 19.712, 26.876, 13.84, 22.43, 29.616, 14.854, 26.456],
    },
    9: {
        "v_r": [1.166, 1.16, 1.193, 1.184, 1.155, 1.182, 1.175, 1.172],
        "L_touret": [14.403, 27.173, 8.601, 20.431, 29.006, 14.982, 29.078, 33.359],
    },
    10: {
        "v_r": [1.196, 1.216, 1.206, 1.232, 1.239, 1.239],
        "L_touret": [19.734, 15.423, 28.916, 9.229, 16.088, 24.546],
    },
    11: {
        "v_r": [1.274, 1.279, 1.286, 1.269, 1.281, 1.271],
        "L_touret": [14.416, 27.291, 15.036, 27.678, 14.858, 27.141],
    },
    12: {
        "v_r": [1.327, 1.314, 1.336, 1.328, 1.323, 1.325],
        "L_touret": [14.589, 27.279, 13.827, 25.615, 14.178, 26.463],
    },
}


if __name__ == "__main__":
    entete = (
        f"{'Essai':>5} | {'v_r (m/s)':>10} | {'L_touret (m)':>12} | "
        f"{'Traînée (N)':>12} | {'C_d (kg/m)':>10}"
    )

    points = []
    for nombre, mesures in essais.items():
        vitesses = mesures["v_r"]
        longueurs = mesures["L_touret"]
        if not vitesses or not longueurs:
            continue
        forces = [
            calculer_trainee(vitesse, nombre, longueur)
            for vitesse, longueur in zip(vitesses, longueurs, strict=True)
        ]
        # Coefficient global : F_d = C_d * v_r**2 (C_d en kg/m).
        coefficients = [
            force / vitesse**2
            for force, vitesse in zip(forces, vitesses)
        ]
        points.append((round(mean(vitesses), 3), round(mean(forces), 3)))

        print(f"\n{nombre} haltère(s) — masse nominale : {nombre * 0.5:.1f} kg")
        print(entete)
        print("-" * len(entete))
        for numero, (vitesse, longueur, force, coefficient) in enumerate(
            zip(vitesses, longueurs, forces, coefficients), start=1
        ):
            print(
                f"{numero:5d} | {vitesse:10.3f} | {longueur:12.3f} | "
                f"{force:12.3f} | {coefficient:10.3f}"
            )
        print(
            f"Moyennes : v_r = {mean(vitesses):.3f} m/s | "
            f"Traînée = {mean(forces):.3f} N | C_d = {mean(coefficients):.3f} kg/m"
        )
        print(
            f"Écarts types (population) : Traînée = {pstdev(forces):.3f} N | "
            f"C_d = {pstdev(coefficients):.3f} kg/m"
        )

    print(f"\npoints = {points}")
