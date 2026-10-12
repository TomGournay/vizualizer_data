from collections import deque
import math


def sinking_intervals(intervals, speed, depth, min_speed, min_depth_change):
    """Garde les coulées : vitesse moyenne positive et profondeur croissante."""
    selected = []
    for start, end in intervals:
        interval_depth = depth.loc[start:end].dropna()
        if len(interval_depth) < 2:
            continue
        depth_change = interval_depth.iloc[-1] - interval_depth.iloc[0]
        if speed.loc[start:end].mean() > min_speed and depth_change > min_depth_change:
            selected.append((start, end))
    return selected


def stationary_intervals(acceleration, epsilon=0.5, min_duration=5,
                         mode="variation", target=9.81, tolerance=0.2):
    """Intervalles disjoints de durée >= min_duration.
    variation : max-min < epsilon ; target : valeurs dans target ± tolerance.

    Parcours chronologique : on prolonge le premier intervalle admissible
    jusqu'à rupture du critère, puis on recommence au point suivant.
    Une valeur manquante coupe l'intervalle.
    """
    if mode == "target":
        return target_intervals(acceleration, target, tolerance, min_duration)
    if mode != "variation":
        raise ValueError("mode doit être 'variation' ou 'target'")
    times = acceleration.index.to_numpy()
    values = acceleration.to_numpy()
    intervals = []
    low, high = deque(), deque()
    start = 0

    for end, value in enumerate(values):
        # Fermer l'intervalle précédent avant d'ajouter un point incompatible.
        invalid = not math.isfinite(value)
        breaks_range = low and max(values[high[0]], value) - min(values[low[0]], value) >= epsilon
        if invalid or breaks_range:
            if end > start and times[end - 1] - times[start] >= min_duration:
                intervals.append((float(times[start]), float(times[end - 1])))
                start = end
                low.clear()
                high.clear()
        if invalid:
            start = end + 1
            low.clear()
            high.clear()
            continue

        while low and values[low[-1]] >= value:
            low.pop()
        while high and values[high[-1]] <= value:
            high.pop()
        low.append(end)
        high.append(end)
        # Si la fenêtre est trop courte, avancer son début pour chercher la suivante.
        while low and high and values[high[0]] - values[low[0]] >= epsilon:
            if low[0] == start:
                low.popleft()
            if high[0] == start:
                high.popleft()
            start += 1

    if len(times) > start and times[-1] - times[start] >= min_duration:
        intervals.append((float(times[start]), float(times[-1])))
    return intervals


def target_intervals(acceleration, target=9.81, tolerance=0.2, min_duration=5):
    """Plages consécutives dans [target-tolerance, target+tolerance], bornes incluses."""
    intervals = []
    start = None
    end = None
    for time, value in acceleration.items():
        if math.isfinite(value) and target - tolerance <= value <= target + tolerance:
            if start is None:
                start = time
            end = time
        else:
            if start is not None and end - start >= min_duration:
                intervals.append((float(start), float(end)))
            start = None
    if start is not None and end - start >= min_duration:
        intervals.append((float(start), float(end)))
    return intervals
