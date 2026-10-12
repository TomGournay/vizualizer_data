from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.colors import qualitative
from plotly.subplots import make_subplots

if __package__:
    from .filtre import filter_series
else:
    from filtre import filter_series


def load_folder(path):
    return {
        file.name: pd.read_json(file, lines=True, encoding="utf-8-sig")
        .sort_values("time", kind="stable")
        for file in sorted(Path(path).expanduser().glob("*.jsonl"))
    }


def get_value(data, column):
    return data.set_index("time")[column].astype(float)


def select_interval(value, tmin=None, tmax=None):
    return value.loc[tmin:tmax]


def mean(value, tmin=None, tmax=None):
    return select_interval(value, tmin, tmax).mean()


def median(value, tmin=None, tmax=None):
    return select_interval(value, tmin, tmax).median()


def std(value, tmin=None, tmax=None, ddof=0):
    return select_interval(value, tmin, tmax).std(ddof=ddof)


def _moving_statistic(value, window_s, center, window_n, statistic, label):
    if window_n is not None:
        rolling = value.rolling(window_n, center=center, min_periods=1)
        smooth = getattr(rolling, statistic)()
        window = f"{window_n} points"
    else:
        timed = value.copy()
        timed.index = pd.to_timedelta(value.index, unit="s")
        rolling = timed.rolling(pd.Timedelta(seconds=window_s), center=center,
                                min_periods=1, closed="both")
        smooth = getattr(rolling, statistic)()
        smooth.index = value.index
        window = f"{window_s:g} s"
    alignment = "centrée" if center else "non centrée"
    return smooth.where(value.notna()).rename(f"{value.name} — {label} ({window}, {alignment})")


def moving_average(value, window_s=None, center=False, *, window_n=None):
    """Moyenne glissante ; choisir window_s OU window_n."""
    return _moving_statistic(value, window_s, center, window_n, "mean", "moyenne glissante")


def moving_median(value, window_s=None, center=False, *, window_n=None):
    """Médiane glissante ; choisir window_s OU window_n."""
    return _moving_statistic(value, window_s, center, window_n, "median", "médiane glissante")


def processed_series(value, treatments, window_s=None, window_n=None,
                     center=False, cutoff_freq=None):
    """Chaque traitement part de la série brute complète, avant sélection temporelle."""
    values = []
    if treatments.get("raw", False):
        values.append(value.copy().rename(f"{value.name} — brut"))
    for key, operation in (("moving_average", moving_average), ("moving_median", moving_median)):
        if treatments.get(key, False):
            values.append(operation(value, window_s=window_s, window_n=window_n, center=center))
    if treatments.get("lowpass", False):
        values.append(filter_series(value, cutoff_freq))
    return values


def interval_statistics(value, tmin=None, tmax=None):
    selected = select_interval(value, tmin, tmax).dropna()
    return dict(count=len(selected), mean=selected.mean(), median=selected.median(),
                std=selected.std(ddof=0))


def statistics_text(value, tmin=None, tmax=None):
    stats = interval_statistics(value, tmin, tmax)
    if not stats["count"]:
        return f"<b>{value.name}</b><br>Aucune donnée dans l’intervalle"
    return (f"<b>{value.name}</b><br>Moyenne : {stats['mean']:.6g} · "
            f"Médiane : {stats['median']:.6g}<br>"
            f"Écart type : {stats['std']:.6g} · N : {stats['count']}")


def plot_subplots(panels, tmin=None, tmax=None, title="Données"):
    """Un panneau contient une série ou une liste de séries superposées."""
    panels = [dict(p) for p in panels]
    for panel in panels:
        if isinstance(panel["value"], pd.Series):
            panel["value"] = [panel["value"]]
        smooth = panel.get("smoothed")
        panel["smoothed"] = [smooth] if isinstance(smooth, pd.Series) else (smooth or [])
    heights = [max(300, 220 + (155 + 80 * len(p["value"])) * len(p.get("intervals") or [])
                   + (70 + 80 * len(p["value"])) * bool(p.get("stats"))) for p in panels]
    fig = make_subplots(
        rows=len(panels), cols=1, row_heights=heights,
        subplot_titles=[p.get("title", ", ".join(v.name for v in p["value"])) for p in panels],
        vertical_spacing=min(0.08, 0.2 / len(panels)),
    )
    for row, panel in enumerate(panels, 1):
        values = panel["value"]
        start = panel.get("tmin", tmin)
        end = panel.get("tmax", tmax)
        first = min(v.index.min() for v in values)
        last = max(v.index.max() for v in values)
        for series_index, series in enumerate(values + panel["smoothed"]):
            selected = select_interval(series, start, end)
            fig.add_trace(go.Scatter(x=selected.index, y=selected, mode="lines",
                                    line=dict(color=qualitative.Plotly[series_index % len(qualitative.Plotly)]),
                                    legendgroup=f"{row}-{series_index}",
                                    name=f"{row}. {series.name}"), row=row, col=1)
        fig.update_xaxes(title_text="Temps (s)", row=row, col=1,
                         range=[first if start is None else start, last if end is None else end])
        fig.update_yaxes(title_text=panel.get("ylabel", ", ".join(v.name for v in values)),
                         row=row, col=1, range=[panel.get("ymin"), panel.get("ymax")])
        notes = []
        if panel.get("stats", False):
            lo = panel.get("stats_tmin")
            hi = panel.get("stats_tmax")
            notes.append(f"<b>Statistiques</b><br>"
                         f"Intervalle : {first if lo is None else lo:g} à {last if hi is None else hi:g} s")
            for value in values:
                notes.append(statistics_text(value, lo, hi))
        intervals = panel.get("intervals")
        if intervals is not None:
            notes.append(f"<b>Régimes stationnaires</b><br>{panel.get('detection_label', 'xacc_robot brut')}")
            if not intervals:
                notes.append("Aucun intervalle détecté")
            for number, (lo, hi) in enumerate(intervals, 1):
                fig.add_vrect(x0=lo, x1=hi, fillcolor="seagreen", opacity=0.15,
                              line_width=1, row=row, col=1,
                              annotation_text=f"R{number}", annotation_position="top left")
                notes.append(f"<b>R{number} : {lo:.3f} à {hi:.3f} s</b><br>Durée : {hi - lo:.3f} s")
                depth = panel.get("depth")
                if depth is not None:
                    selected_depth = select_interval(depth, lo, hi).dropna()
                    if selected_depth.empty:
                        notes.append("Profondeur : aucune mesure dans l’intervalle")
                    else:
                        dmin, dmax = selected_depth.iloc[[0, -1]]
                        depth_start, depth_end = selected_depth.index[[0, -1]]
                        notes.append(f"Profondeur tmin : {dmin:.6g} m (t = {depth_start:.3f} s)<br>"
                                     f"Profondeur tmax : {dmax:.6g} m (t = {depth_end:.3f} s)<br>"
                                     f"Profondeur moyenne : {selected_depth.mean():.6g} m")
                for series_index, value in enumerate(values):
                    average = mean(value, lo, hi)
                    if pd.notna(average):
                        fig.add_trace(go.Scatter(x=[lo, hi], y=[average, average], mode="lines",
                                                line=dict(dash="dash", color=qualitative.Plotly[series_index % len(qualitative.Plotly)]),
                                                legendgroup=f"{row}-{series_index}", showlegend=False,
                                                name=f"{row}. {value.name} R{number} moyenne"), row=row, col=1)
                    notes.append(statistics_text(value, lo, hi))
        if notes:
            axis = str(row) if row > 1 else ""
            fig.add_annotation(x=1.03, y=1, xref=f"x{axis} domain", yref=f"y{axis} domain",
                               xanchor="left", yanchor="top", showarrow=False,
                               align="left", font=dict(size=12), text="<br><br>".join(notes))
    fig.update_layout(title=title, template="plotly_white", height=sum(heights) + 120,
                      margin=dict(r=560 if any(p.get("stats") or p.get("intervals") is not None
                                               for p in panels) else 40),
                      legend=dict(orientation="h", y=-0.12, x=0))
    return fig

def plot(value, tmin=None, tmax=None, ymin=None, ymax=None,
         smoothed=None, title=None, ylabel=None):
    return plot_subplots([dict(value=value, tmin=tmin, tmax=tmax, ymin=ymin,
                               ymax=ymax, smoothed=smoothed,
                               title=title or value.name, ylabel=ylabel or value.name)])
