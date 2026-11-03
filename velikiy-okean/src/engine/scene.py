"""Scene state helpers: camera, looks (palettes per act), interpolation of keyed parameters."""
import math
import numpy as np


def _n(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def look_at(pos, target, roll_deg=0.0):
    f = _n(np.asarray(target, float) - np.asarray(pos, float))
    r = _n(np.cross([0.0, 1.0, 0.0], f))
    u = np.cross(f, r)
    if roll_deg:
        a = math.radians(roll_deg)
        r, u = r * math.cos(a) + u * math.sin(a), -r * math.sin(a) + u * math.cos(a)
    return np.column_stack([r, u, f]).astype(np.float32)


def dir_from_angles(az_deg, el_deg):
    """azimuth measured from +z (sea) toward +x, elevation above horizon."""
    az, el = math.radians(az_deg), math.radians(el_deg)
    return np.array([math.sin(az) * math.cos(el), math.sin(el), math.cos(az) * math.cos(el)], np.float32)


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def ease_io(t, p=2.2):
    t = min(max(t, 0.0), 1.0)
    return t ** p / (t ** p + (1 - t) ** p)


def lerp(a, b, t):
    if isinstance(a, (list, tuple, np.ndarray)):
        return (np.asarray(a, float) + (np.asarray(b, float) - np.asarray(a, float)) * t)
    return a + (b - a) * t


def keyed(keys, t, fn=ease):
    """keys: list of (time, value). Smooth interpolation, clamped outside."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys[:-1], keys[1:]):
        if t0 <= t <= t1:
            return lerp(v0, v1, fn((t - t0) / max(t1 - t0, 1e-9)))
    return keys[-1][1]


def catmull(points, u):
    """Centripetal-ish Catmull-Rom through points for u in [0,1] (uniform parametrisation)."""
    P = [np.asarray(p, float) for p in points]
    if len(P) == 2:
        return P[0] + (P[1] - P[0]) * u
    n = len(P) - 1
    x = min(max(u, 0.0), 1.0) * n
    i = min(int(x), n - 1)
    t = x - i
    p0 = P[max(i - 1, 0)]; p1 = P[i]; p2 = P[i + 1]; p3 = P[min(i + 2, n)]
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def drift(t, seed, amp_pos=0.006, amp_rot=0.0012):
    """Very subtle camera breathing (fluid head / slider), not shaky handheld."""
    s = seed * 13.17
    dp = np.array([math.sin(t * 0.31 + s) + 0.5 * math.sin(t * 0.73 + 2 * s),
                   math.sin(t * 0.27 + 3 * s) + 0.5 * math.sin(t * 0.61 + s),
                   math.sin(t * 0.19 + 5 * s)]) * amp_pos
    dr = np.array([math.sin(t * 0.23 + 7 * s), math.sin(t * 0.29 + 11 * s), 0.0]) * amp_rot
    return dp, dr


# ---------------------------------------------------------------------------
# LOOKS — world + grade presets per act (see docs/STYLE_GUIDE.md)
# ---------------------------------------------------------------------------
NIGHT = dict(
    uMoonDir=dir_from_angles(-14.0, 13.0),
    uMoonCol=np.array([0.62, 0.70, 0.86], np.float32) * 1.0,
    uMoonDisk=260.0,
    uSunDir=dir_from_angles(60.0, -20.0),
    uSunCol=np.array([0.0, 0.0, 0.0], np.float32),
    uSunDisk=0.0,
    uZenith=np.array([0.006, 0.010, 0.022], np.float32),
    uHorizon=np.array([0.042, 0.052, 0.072], np.float32),
    uAmbient=np.array([0.030, 0.040, 0.060], np.float32),
    uStars=0.6,
    uCloudCover=0.62,
    uCloudDens=0.9,
    uCloudOfs=(0.0, 0.0),
    uMoonClear=0.0,
    uMoonVeil=0.0,
    uCloudLit=np.array([0.35, 0.40, 0.50], np.float32),
    uFogDens=0.008,
    uFogH=9.0,
    uGroundMist=0.05,
    uFogCol=np.array([0.80, 0.86, 0.95], np.float32),
    uMist=0.75,
    uWindVel=np.array([0.9, 0.05, -0.35], np.float32),
    uFogG=0.65,
    uFogFar=0.0006,
    uWaveAmp=0.30,
    uSwellAng=math.radians(-90.0 - 4.0),   # waves travel toward -z (the shore)
    uSwashT=6.58,
    uSwashPhase=0.0,
    uSwashReach=1.0,
    uFoamAmt=1.0,
    uRip=np.zeros((4, 4), np.float32),
    uGlow=(0.0, 0.0, 0.0, 0.0),
    uGlowCol=np.array([0.4, 0.6, 0.7], np.float32),
    uDeepCol=np.array([0.020, 0.055, 0.065], np.float32),
    uRocky=0.0,
    uBeachSlope=0.045,
    uHero=0,
    uStudio=0,
    uCoatWind=1.0,
)

NIGHT_POST = dict(
    uExposure=0.5,
    uLift=np.array([0.006, 0.009, 0.016], np.float32),
    uGammaG=np.array([1.0, 1.0, 1.02], np.float32),
    uGain=np.array([0.97, 1.0, 1.04], np.float32),
    uSat=0.72,
    uContrast=1.12,
    uShadowTint=np.array([-0.004, 0.0, 0.010], np.float32),
    uHighTint=np.array([0.006, 0.008, 0.010], np.float32),
    uBloom=0.10,
    uHalation=0.25,
    uVignette=0.42,
    uGrain=0.022,
    uFade=0.0,
    uFadeCol=np.array([0.0, 0.0, 0.0], np.float32),
    uFocusDist=20.0,
    uFStop=2.8,
    uMaxCoc=10.0,
)


# ---- dawn looks (Acts II-III) — first pass, see STYLE_GUIDE.md §3 ----
def _look(base, **kw):
    d = dict(base)
    d.update(kw)
    return d


PEARL = _look(NIGHT,   # D2: sun just below the horizon, mist glowing from within
    uMoonCol=np.array([0.05, 0.055, 0.065], np.float32), uMoonDisk=0.0, uStars=0.0,
    uSunDir=dir_from_angles(-12.0, -1.5), uSunCol=np.array([0.55, 0.40, 0.33], np.float32), uSunDisk=0.0,
    uZenith=np.array([0.075, 0.095, 0.14], np.float32), uHorizon=np.array([0.36, 0.32, 0.30], np.float32),
    uAmbient=np.array([0.16, 0.16, 0.18], np.float32), uCloudLit=np.array([0.55, 0.42, 0.40], np.float32),
    uCloudCover=0.5, uFogCol=np.array([1.0, 0.95, 0.93], np.float32), uFogDens=0.011, uGroundMist=0.07, uFogG=0.6,
    uDeepCol=np.array([0.03, 0.065, 0.075], np.float32))
PEARL_POST = _look(NIGHT_POST, uExposure=0.62, uSat=0.8, uLift=np.array([0.012, 0.010, 0.012], np.float32),
    uGain=np.array([1.02, 1.0, 0.99], np.float32), uShadowTint=np.array([-0.002, 0.002, 0.006], np.float32),
    uHighTint=np.array([0.01, 0.006, 0.002], np.float32), uVignette=0.35)

GOLD = _look(NIGHT,    # D4: sunrise, sparkling ocean
    uMoonCol=np.array([0.0, 0.0, 0.0], np.float32), uMoonDisk=0.0, uStars=0.0,
    uSunDir=dir_from_angles(-10.0, 4.0), uSunCol=np.array([1.45, 1.05, 0.66], np.float32), uSunDisk=55.0,
    uZenith=np.array([0.10, 0.15, 0.25], np.float32), uHorizon=np.array([0.62, 0.48, 0.36], np.float32),
    uAmbient=np.array([0.20, 0.19, 0.20], np.float32), uCloudLit=np.array([0.9, 0.62, 0.42], np.float32),
    uCloudCover=0.45, uFogCol=np.array([1.0, 0.93, 0.85], np.float32), uFogDens=0.006, uGroundMist=0.04, uFogG=0.7,
    uDeepCol=np.array([0.02, 0.075, 0.075], np.float32))
GOLD_POST = _look(NIGHT_POST, uExposure=0.42, uSat=0.9, uLift=np.array([0.014, 0.009, 0.005], np.float32),
    uGain=np.array([1.03, 1.0, 0.95], np.float32), uShadowTint=np.array([-0.004, 0.003, 0.006], np.float32),
    uHighTint=np.array([0.012, 0.006, -0.004], np.float32), uHalation=0.35, uBloom=0.14, uVignette=0.35)
