import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit, minimize


def puissance(x, a, b, c):
    return a * np.asarray(x)**b + c


def ajuster_puissance(points, contraintes=(), initial=(1, 2, 0), poids=None):
    """Ajuste a*x**b+c, avec b positif, contraintes exactes et poids positifs."""
    x, y = np.asarray(points, dtype=float).T
    coefficients, _ = curve_fit(
        puissance, x, y, p0=initial,
        sigma=None if poids is None else 1 / np.sqrt(poids),
        bounds=([-np.inf, 1e-8, -np.inf], np.inf), maxfev=10000,
    )
    if not contraintes:
        return coefficients

    xc, yc = np.asarray(contraintes, dtype=float).T
    echelle = max(np.max(np.abs(y)), 1)
    resultat = minimize(
        lambda coefficients: np.average(
            ((puissance(x, *coefficients) - y) / echelle)**2, weights=poids,
        ),
        coefficients,
        method="SLSQP",
        bounds=[(None, None), (1e-8, None), (None, None)],
        constraints={"type": "eq", "fun": lambda coefficients: puissance(xc, *coefficients) - yc},
        options={"ftol": 1e-12, "maxiter": 10000},
    )
    if not resultat.success:
        raise ValueError(resultat.message)
    return resultat.x


def ajuster(points, contraintes=(), lineaire=True, poids=None):
    """Moindres carrés quadratiques ; contraintes (x, y) imposant p(x) = y.

    lineaire=False ajuste a*x²+b, sans terme linéaire.
    Un poids positif par mesure, appliqué à son erreur au carré.
    """
    x, y = zip(*points)
    colonnes = [0, 1, 2] if lineaire else [0, 2]
    A = np.vander(x, 3)[:, colonnes]
    if poids is not None:
        racines = np.sqrt(poids)
        A = A * racines[:, None]
        y = np.asarray(y) * racines
    if contraintes:
        xc, yc = zip(*contraintes)
        C = np.vander(xc, 3)[:, colonnes]
        # Moindres carrés avec égalités exactes (multiplicateurs de Lagrange).
        M = np.block([[A.T @ A, C.T], [C, np.zeros((len(C), len(C)))]])
        coefficients = np.linalg.solve(M, np.r_[A.T @ y, yc])[:len(colonnes)]
    else:
        coefficients = np.linalg.lstsq(A, y, rcond=None)[0]
    return np.poly1d(coefficients if lineaire else [coefficients[0], 0, coefficients[1]])


if __name__ == "__main__":
    points = [(0.583, 16.413), (0.679, 20.119), (0.765, 23.612), (0.84, 27.228), (0.921, 30.753), (0.981, 34.251), (1.076, 37.552), (1.116, 41.249), (1.165, 44.888), (1.221, 48.48), (1.275, 51.962), (1.323, 55.536)]
    points_min = [(0.583, 13.609), (0.679, 16.938), (0.765, 20.055), (0.84, 23.294), (0.921, 26.443), (0.981, 29.564), (1.076, 32.49), (1.116, 35.81), (1.165, 39.073), (1.221, 42.288), (1.275, 45.394), (1.323, 48.592)]
    points_max = [(0.583, 19.218), (0.679, 23.3), (0.765, 27.17), (0.84, 31.162), (0.921, 35.063), (0.981, 38.937), (1.076, 42.615), (1.116, 46.688), (1.165, 50.703), (1.221, 54.671), (1.275, 58.53), (1.323, 62.48)]
    poids = [1, 1, 1, 1, 1, 1, 5, 5, 5, 5, 5, 5]  # Un poids positif par mesure, dans le même ordre.
    modele = "quadratique"  # "ax2" (a*x²+b), "quadratique" ou "puissance".
    contraintes = [(0, 0)]  # Tous les modèles : p(0)=0. Mettre [] pour désactiver.

    for nom, mesures, couleur in [
        ("p", points, "C0"),
        ("p_min", points_min, "C1"),
        ("p_max", points_max, "C2"),
    ]:
        if modele == "puissance":
            a, b, c = ajuster_puissance(mesures, contraintes, poids=poids)
            p = lambda x: puissance(x, a, b, c)
            print(f"{nom}(x) = {a:.6g} x^{b:.6g} {c:+.6g}")
        else:
            p = ajuster(mesures, contraintes, lineaire=(modele == "quadratique"), poids=poids)
            if modele == "ax2":
                print(f"{nom}(x) = {p[2]:.6g} x² {p[0]:+.6g}")
            else:
                print(f"{nom}(x) = {p[2]:.6g} x² {p[1]:+.6g} x {p[0]:+.6g}")

        x, y = np.asarray(mesures).T
        xx = np.linspace(0, 2, 300)
        plt.scatter(x, y, color=couleur)
        plt.plot(xx, p(xx), color=couleur, label=f"{nom} ({modele})")
    if contraintes:
        plt.scatter(*zip(*contraintes), marker="x", s=80, label="Contraintes")
    plt.xlabel("v (m/s)")
    plt.ylabel("f_drag (N)")
    plt.xlim(0, 2)
    plt.grid()
    plt.legend()
    plt.tight_layout()
    plt.show()
