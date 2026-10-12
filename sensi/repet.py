import pandas as pd


def summarize(reference):
    """Synthèse par poids : une force par descente, même poids pour chaque essai.

    L'écart type est celui de la population (ddof=0).
    """
    rows = []
    for halteres, group in reference.groupby("halteres", sort=True):
        forces = group["trainee_N"]
        rows.append({
            "halteres": halteres,
            "essais_analyses": group["dossier"].nunique(),
            "essais_avec_mesure": forces.notna().sum(),
            "intervalles": group["intervalles"].sum(),
            "duree_totale_s": group["duree_s"].sum(),
            "trainee_moyenne_N": forces.mean(),
            "trainee_ecart_type_N": forces.std(ddof=0),
        })
    return pd.DataFrame(rows)
