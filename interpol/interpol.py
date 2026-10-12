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
    points = [(0.577, 16.426), (0.68, 20.125), (0.759, 23.617), (0.838, 27.257), (0.927, 30.684), (0.988, 34.2), (1.076, 37.556), (1.111, 41.317), (1.173, 44.825), (1.269, 47.871), (1.279, 51.936), (1.333, 55.381)]
    points_min = [(0.577, 13.621), (0.68, 16.944), (0.759, 20.06), (0.838, 23.323), (0.927, 26.374), (0.988, 29.514), (1.076, 32.493), (1.111, 35.878), (1.173, 39.01), (1.269, 41.679), (1.279, 45.368), (1.333, 48.437)]
    points_max = [(0.577, 19.231), (0.68, 23.306), (0.759, 27.174), (0.838, 31.191), (0.927, 34.994), (0.988, 38.886), (1.076, 42.618), (1.111, 46.756), (1.173, 50.64), (1.269, 54.062), (1.279, 58.503), (1.333, 62.325)]
    poids = [0.308995, 0.45478, 0.26527, 0.352485, 0.393939, 0.055324, 0.05, 0.05, 0.05, 0.519583, 0.05, 0.185086]
    modele = "quadratique"  # "ax2" (a*x²+b), "quadratique" ou "puissance".
    contraintes = [(0, 0)]  # Tous les modèles : p(0)=0. Mettre [] pour désactiver.
#    contraintes = []  # Tous les modèles : p(0)=0. Mettre [] pour désactiver.

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
