"""Temporal QA: per-frame luma and frame-to-frame change; flags jumps that are not at planned cuts.
python temporal_check.py video.mp4 f0 cut1 cut2 ...   (cut = first frame of a new shot)"""
import sys, subprocess, json
import numpy as np
video, f0 = sys.argv[1], int(sys.argv[2])
cuts = set(int(c) for c in sys.argv[3:])
w, h = 192, 108
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', video, '-vf', f'scale={w}:{h}', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
mean = fr.mean((1, 2))
diff = np.abs(np.diff(fr, axis=0)).mean((1, 2))
med = np.median(diff)
flags = []
for i, d in enumerate(diff):
    f = f0 + i + 1
    if f in cuts:
        continue
    if d > max(4.0 * med, 3.0):
        flags.append(dict(frame=f, diff=round(float(d), 2)))
rep = dict(frames=int(len(fr)), luma_min=round(float(mean.min()), 1), luma_max=round(float(mean.max()), 1),
           median_change=round(float(med), 2), max_change_noncut=round(float(max([d for i, d in enumerate(diff) if f0 + i + 1 not in cuts] or [0])), 2),
           change_at_cuts={c: round(float(diff[c - f0 - 1]), 2) for c in sorted(cuts) if 0 < c - f0 <= len(diff)},
           suspicious_jumps=flags[:20])
print(json.dumps(rep, ensure_ascii=False, indent=1))
