"""Vocal activity + pitch analysis on Demucs stems. Outputs per-frame arrays (npz) and region list."""
import sys, json, numpy as np, soundfile as sf, librosa
voc_path, acc_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
SR, HOP = 16000, 160  # 10 ms
v, sr = librosa.load(voc_path, sr=SR, mono=True)
a, _ = librosa.load(acc_path, sr=SR, mono=True)
def rms_db(x):
    r = librosa.feature.rms(y=x, frame_length=1024, hop_length=HOP, center=True)[0]
    return 20*np.log10(r + 1e-9)
vdb, adb = rms_db(v), rms_db(a)
n = min(len(vdb), len(adb)); vdb, adb = vdb[:n], adb[:n]
t = np.arange(n) * HOP / SR
f0, vflag, vprob = librosa.pyin(v, fmin=65, fmax=1000, sr=SR, frame_length=1024, hop_length=HOP, center=True)
f0, vflag, vprob = f0[:n], vflag[:n], vprob[:n]
# spectral centroid of vocals (timbre cue)
cent = librosa.feature.spectral_centroid(y=v, sr=SR, n_fft=1024, hop_length=HOP)[0][:n]
np.savez_compressed(out + '.npz', t=t, vdb=vdb, adb=adb, f0=f0, vflag=vflag, vprob=vprob, cent=cent)
peak = np.percentile(vdb, 99.5)
thr = peak - 38
act = vdb > thr
# hysteresis smoothing: close gaps < 250 ms, drop blips < 120 ms
def runs(mask):
    idx = np.flatnonzero(np.diff(np.r_[0, mask.astype(int), 0]))
    return list(zip(idx[::2], idx[1::2]))
m = act.copy()
for s, e in runs(~m):
    if s > 0 and e < n and (e - s) < 25: m[s:e] = True
for s, e in runs(m):
    if (e - s) < 12: m[s:e] = False
regions = []
for s, e in runs(m):
    seg_f0 = f0[s:e][vflag[s:e]]
    semis = 12*np.log2(seg_f0/55.0) if len(seg_f0) else np.array([])
    stab = float(np.median(np.abs(np.diff(semis)))) if len(semis) > 2 else None
    regions.append(dict(start=round(float(t[s]), 3), end=round(float(t[min(e, n-1)]), 3),
                        dur=round(float(t[min(e, n-1)] - t[s]), 3),
                        voiced_frac=round(float(vflag[s:e].mean()), 2),
                        f0_med=None if len(seg_f0) == 0 else round(float(np.median(seg_f0)), 1),
                        f0_p10=None if len(seg_f0) == 0 else round(float(np.percentile(seg_f0, 10)), 1),
                        f0_p90=None if len(seg_f0) == 0 else round(float(np.percentile(seg_f0, 90)), 1),
                        f0_step_med=None if stab is None else round(stab, 3),
                        vdb=round(float(vdb[s:e].mean()), 1), adb=round(float(adb[s:e].mean()), 1)))
json.dump(dict(peak_db=float(peak), thr_db=float(thr), regions=regions), open(out + '_regions.json', 'w'), indent=1)
for r in regions:
    print(f"{r['start']:7.2f}-{r['end']:7.2f} ({r['dur']:5.2f}s) voiced={r['voiced_frac']:.2f} f0med={r['f0_med']} [{r['f0_p10']}-{r['f0_p90']}] step={r['f0_step_med']} v={r['vdb']} acc={r['adb']}")
