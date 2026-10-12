"""Analyse reproductible de l'essai vague. Executer : python3 -s analyse_vague.py."""
import json
from pathlib import Path
import numpy as np
from scipy import signal
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC = Path("/home/crc/data_exp_2909/vague")
OUT = Path(__file__).resolve().parent
BAND = (0.15, 0.40)
results = {}
series = {}
for typ, keys in [("bar30", ["depth", "sink_speed"]), ("imu", ["xacc_robot", "yacc_robot", "zacc_robot"])]:
    data = [json.loads(l) for l in (SRC / f"vague_{typ}.jsonl").read_text().splitlines()]
    t = np.array([r["time"] for r in data])
    assert np.all(np.diff(t)>0)
    fs = 1 / np.median(np.diff(t))
    tu = np.arange(t[0], t[-1], 1/fs)
    for key in keys:
        x = np.array([r[key] for r in data])
        assert np.all(np.isfinite(x))
        xu = np.interp(tu, t, x)
        band = signal.sosfiltfilt(signal.butter(3, BAND, btype="bandpass", fs=fs, output="sos"), signal.detrend(xu))
        mask = (tu>=10)&(tu<=55)
        central = band[mask]
        # Equivalent sinusoidal amplitude, not an individual measured wave height.
        amp = np.sqrt(2)*np.std(central)
        segments = {}
        for a,b in [(0,61.5),(8,58),(8,33),(33,58)]:
            m=(tu>=a)&(tu<=b)
            f,p=signal.periodogram(signal.detrend(xu[m]),fs,window="hann")
            peaks,_=signal.find_peaks(p)
            inds=sorted([k for k in peaks if .15<=f[k]<=.4],key=lambda k:p[k],reverse=True)[:2]
            segments[f"{a}-{b}"]={"resolution_hz":float(f[1]-f[0]),"peaks_hz":[float(f[k]) for k in inds]}
        f,p=signal.periodogram(signal.detrend(xu[(tu>=8)&(tu<=58)]),fs,window="hann")
        results[key]={"unit": "m" if key=="depth" else "m/s" if key=="sink_speed" else "m/s²",
            "amplitude_equivalente":float(amp),"crete_a_crete_equivalente":float(2*amp),
            "rms_bande":float(np.std(central)),"p95_p05_bande":float(np.percentile(central,95)-np.percentile(central,5)),
            "segments":segments,"fs_grille_hz":float(fs),"fs_moyen_hz":float((len(t)-1)/(t[-1]-t[0]))}
        series[key]=(tu,xu,band,f,p,fs)
# Check speed construction on original timestamps.
d=[json.loads(l) for l in (SRC/"vague_bar30.jsonl").read_text().splitlines()]
t=np.array([r["time"] for r in d]); dep=np.array([r["depth"] for r in d]); vel=np.array([r["sink_speed"] for r in d])
results["verification_vitesse"]={"rmse_difference_finie":float(np.sqrt(np.mean((np.diff(dep)/np.diff(t)-vel[1:])**2)))}
fig,axs=plt.subplots(3,2,figsize=(13,10))
for i,key in enumerate(["depth","sink_speed","xacc_robot"]):
    tu,xu,band,f,p,fs=series[key]
    scale=1000 if key=="depth" else 1
    unit="mm" if key=="depth" else results[key]["unit"]
    axs[i,0].plot(tu,band*scale,lw=1)
    axs[i,0].axvspan(0,10,color="gray",alpha=.15); axs[i,0].axvspan(55,tu[-1],color="gray",alpha=.15)
    axs[i,0].set(xlabel="Temps (s)",ylabel=f"{key} ({unit})",title="Composante 0,15–0,40 Hz (bords exclus des amplitudes)")
    axs[i,1].plot(f,p*scale**2)
    axs[i,1].set_ylim(0, 1.12*np.max(p[(f>=.1)&(f<=.65)])*scale**2)
    axs[i,1].set(xlim=(.1,.65),xlabel="Fréquence (Hz)",ylabel=f"DSP ({unit}²/Hz)",title="Spectre du signal brut detrendé, 8–58 s")
    for a in axs[i]: a.grid(alpha=.3)
fig.tight_layout(); fig.savefig(OUT/"analyse_vague.png",dpi=160); plt.close(fig)
tu,xu,band,f,p,fs=series["sink_speed"]
fig,axs=plt.subplots(2,1,figsize=(12,7))
axs[0].plot(tu,xu,color=".65",lw=.6,label="Vitesse brute")
for fc in [.08,.1]:
    sos=signal.butter(2,fc,fs=fs,output="sos")
    y=signal.sosfiltfilt(sos,xu)
    axs[0].plot(tu,y,label=f"Butterworth ordre 2, {fc} Hz, aller-retour")
    axs[1].plot(tu,y,label=f"{fc} Hz, aller-retour")
    _,h=signal.sosfreqz(sos,worN=[.21,.28],fs=fs)
    results[f"filtre_{fc}"]={"gain_causal_021_028":np.abs(h).tolist(),"gain_aller_retour_021_028":(np.abs(h)**2).tolist()}
for a in axs:
    a.set(xlabel="Temps (s)",ylabel="Vitesse (m/s)")
    a.grid(alpha=.3); a.legend()
axs[1].set_ylim(-.015,.015)
fig.tight_layout(); fig.savefig(OUT/"comparaison_filtres.png",dpi=150)
(OUT/"resultats.json").write_text(json.dumps(results,indent=2,ensure_ascii=False))
print(json.dumps(results,indent=2,ensure_ascii=False))
