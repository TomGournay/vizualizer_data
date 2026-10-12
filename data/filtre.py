from scipy.signal import butter, sosfiltfilt


def apply_filter(data, fs, cutoff_freq):
    sos = butter(4, cutoff_freq, btype="lowpass", fs=fs, output="sos")
    return sosfiltfilt(sos, data, axis=0)


def filter_series(value, cutoff_freq):
    """Filtre une seule série, indexée par un temps en secondes."""
    fs = 1 / value.index.to_series().diff().median()
    filtered = value.copy()
    filtered.iloc[:] = apply_filter(value.to_numpy(), fs, cutoff_freq)
    return filtered.rename(f"{value.name} — passe-bas ({cutoff_freq:g} Hz)")


def filter_data(data, cutoff_freq):
    """Filtre les colonnes numériques ; time est en secondes, presque régulier."""
    filtered = data.copy()
    columns = data.select_dtypes(include="number").columns.drop("time")
    fs = 1 / data["time"].diff().median()
    filtered[columns] = apply_filter(data[columns], fs, cutoff_freq)
    return filtered
