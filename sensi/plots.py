from html import escape
import json

import plotly.graph_objects as go
from plotly.colors import qualitative
from plotly.offline import get_plotlyjs
from plotly.subplots import make_subplots


def write_page(path, title, parts):
    page = [
        '<!doctype html><html lang="fr"><head><meta charset="utf-8">',
        f'<title>{escape(title)}</title><script src="plotly.min.js"></script>',
        '<style>body{font:15px system-ui;margin:32px;color:#172b3a}'
        'table{border-collapse:collapse;font-size:13px}th,td{padding:6px 10px;'
        'border-bottom:1px solid #ddd;text-align:right}th{background:#eef3f5}'
        'pre{white-space:pre-wrap}.table{overflow-x:auto}a{color:#12609a}</style>',
        f'</head><body><h1>{escape(title)}</h1>', *parts, '</body></html>',
    ]
    path.write_text("\n".join(page), encoding="utf-8")


def table(frame):
    return '<div class="table">' + frame.to_html(
        index=False, float_format=lambda value: f"{value:.3f}", na_rep="—", border=0
    ) + '</div>'


def plot_reference(group, folders, signals):
    titles = [f"{folder} — {label}" for folder in folders for label in ("Vitesse", "Profondeur")]
    fig = make_subplots(rows=len(folders), cols=2, shared_xaxes="rows", subplot_titles=titles)
    for row, folder in enumerate(folders, 1):
        fragments = group.loc[(group["dossier"] == folder) & group["intervalle"].notna()]
        for col, (signal, label) in enumerate(zip(signals[folder], ("Vitesse (m/s)", "Profondeur (m)")), 1):
            fig.add_trace(go.Scatter(x=signal.index, y=signal, mode="lines", name=folder,
                                    line_color=qualitative.Plotly[(row - 1) % 10]), row=row, col=col)
            fig.update_xaxes(title_text="Temps (s)", row=row, col=col)
            fig.update_yaxes(title_text=label, row=row, col=col)
            for fragment in fragments.itertuples():
                fig.add_vrect(x0=fragment.tmin_s, x1=fragment.tmax_s, fillcolor="seagreen",
                              opacity=0.2, line_width=0, row=row, col=col,
                              annotation_text=f"R{int(fragment.intervalle)}" if col == 1 else "",
                              annotation_position="top left")
    fig.update_layout(template="plotly_white", height=320 * len(folders), showlegend=False)
    return fig


def plot_sensitivity(group):
    parameter = group["parametre"].iloc[0]
    xlabel = ("Temps minimum (s)" if parameter == "min_duration_s" else
              "Variation maximale (°)" if parameter == "roll_deg" else
              "Tolérance (°)" if parameter in ("pitch_deg", "yaw_deg") else "Valeur du seuil")
    contexts = group["contexte"].unique()
    folders = group["dossier"].unique()
    colors = dict(zip(folders, (qualitative.Plotly[i % 10] for i in range(len(folders)))))
    fig = make_subplots(rows=2, cols=len(contexts), shared_xaxes="columns", shared_yaxes="rows",
                        subplot_titles=list(contexts), vertical_spacing=0.13)
    for col, context in enumerate(contexts, 1):
        context_rows = group[group["contexte"] == context]
        for folder, values in context_rows.groupby("dossier", sort=False):
            values = values.sort_values("valeur")
            details = values[["trainee_base_contexte_N", "delta_contexte_N",
                              "delta_reference_N", "v_r_m_s", "profondeur_m", "intervalles"]]
            for row, field in enumerate(("trainee_N", "duree_s"), 1):
                hover = (
                    "Force : %{y:.3f} N<br>Base du contexte : %{customdata[0]:.3f} N<br>"
                    "Écart à cette base : %{customdata[1]:+.3f} N<br>"
                    "Écart à la référence : %{customdata[2]:+.3f} N<br>"
                    "Vitesse : %{customdata[3]:.3f} m/s<br>Profondeur : %{customdata[4]:.3f} m"
                    if row == 1 else "Durée : %{y:.2f} s<br>Fragments : %{customdata[5]}"
                )
                fig.add_trace(go.Scatter(
                    x=values["valeur"], y=values[field], mode="lines+markers", connectgaps=False,
                    name=folder, legendgroup=folder, line_color=colors[folder], customdata=details,
                    showlegend=row == 1 and col == 1,
                    hovertemplate="Valeur : %{x}<br>" + hover + "<extra>%{fullData.name}</extra>",
                ), row=row, col=col)
        for row in (1, 2):
            fig.add_vline(x=group["valeur_reference"].iloc[0], line_dash="dot", line_color="gray",
                          row=row, col=col)
            fig.update_xaxes(nticks=6, row=row, col=col)
        fig.update_xaxes(title_text=xlabel, row=2, col=col)
    fig.update_yaxes(title_text="Force de traînée (N)", row=1, col=1)
    fig.update_yaxes(title_text="Durée retenue (s)", rangemode="tozero", row=2, col=1)
    fig.update_layout(template="plotly_white", height=580, margin=dict(t=55, b=65),
                      legend=dict(orientation="h", y=-0.2, groupclick="togglegroup"))
    return fig


def write_reports(reference, intervals, summary, results, signals, settings, output):
    (output / "plotly.min.js").write_text(get_plotlyjs(), encoding="utf-8")
    parts = [
        '<p>Une mesure par descente, calculée sur toutes ses portions stationnaires retenues, '
        'sans inclure les trous. La profondeur moyenne sert de longueur de touret. '
        'Aucune exclusion des vitesses atypiques. Un tiret indique une mesure absente.</p>',
        '<h2>Par poids</h2>', table(summary),
        '<p>Chaque descente mesurée contribue à parts égales à la moyenne par poids.</p>',
    ]
    for weight, group in reference.groupby("halteres", sort=True):
        parts.extend([f'<h2>{weight} haltère(s)</h2>',
                      f'<p><a href="sensibilite_{weight}.html">Sensibilité pour ce poids</a></p>',
                      '<h3>Mesures par descente</h3>', table(group)])
        fragments = intervals[intervals["halteres"] == weight]
        parts.extend(['<details><summary>Détail des fragments de référence</summary>',
                      table(fragments), '</details>',
                      plot_reference(fragments, group["dossier"], signals).to_html(
                          full_html=False, include_plotlyjs=False)])
    parts.extend(['<details><summary>Paramètres</summary><pre>',
                  escape(json.dumps(settings, ensure_ascii=False, indent=2)), '</pre></details>'])
    write_page(output / "reference.html", "Référence de traînée par descente", parts)

    contexts = "; ".join(f"{escape(name)} : ×{factor:g}" for name, factor in settings["contexts"].items())
    for weight, group in results.groupby("halteres", sort=True):
        parts = [
            '<p><a href="reference.html">Retour à la référence</a></p>',
            '<p>Dans chaque colonne, seul le paramètre indiqué varie ; les autres critères restent '
            'fixes aux valeurs du contexte. Le trait vertical indique la valeur de référence. '
            f'Multiplicateurs des seuils des capteurs : {contexts}. '
            f'La durée minimale reste à {settings["min_duration_s"]:g} s pendant les balayages des capteurs ; '
            'elle seule varie pendant le balayage du temps minimum.</p>',
            '<p>Une force absente signifie qu’aucune mesure n’est disponible : elle ne vaut pas zéro. '
            'La durée retenue permet de repérer ces absences. Survoler une mesure affiche ses écarts '
            'à la référence et à la base du contexte (paramètre étudié à sa valeur de référence).</p>',
        ]
        for parameter, values in group.groupby("parametre", sort=False):
            if parameter == "min_duration_s":
                title = "Temps minimum (s)"
            else:
                criterion = settings["stationary_criteria"][parameter]
                threshold = "epsilon (max−min)" if criterion.get("mode") == "variation" else "tolérance autour de la cible"
                title = f"{escape(parameter)} — {threshold}"
            parts.append(f'<h2>{title}</h2>')
            if parameter == "yaw_deg":
                parts.append(f'<p>Écart circulaire autour de {criterion["target"]:g}° : '
                             '359° et −1° représentent le même angle. '
                             f'Tolérance de référence : {criterion["tolerance"]:g}°.</p>')
            if parameter == "roll_deg":
                parts.append('<p>Stabilité du roll : max−min sur les angles dépliés, '
                             'sans cible d’orientation. '
                             f'Amplitude de référence : {criterion["epsilon"]:g}°.</p>')
            parts.append(plot_sensitivity(values).to_html(full_html=False, include_plotlyjs=False))
        write_page(output / f"sensibilite_{weight}.html", f"Sensibilité — {weight} haltère(s)", parts)
