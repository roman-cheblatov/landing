"""Shot list of the film as code. Each shot maps film time -> (world uniforms, post uniforms).
Times are seconds of the original audio (docs/TIMELINE.json); frames at 24 fps: f = round(t*24).
This file currently contains ACT I opening (shots 01-04 = the approved-test candidate)."""
import math
import numpy as np
from scene import NIGHT, NIGHT_POST, look_at, keyed, ease, ease_io, catmull, drift, dir_from_angles, lerp
from hero import Hero

FPS = 24

# One hero timeline for the whole opening (continuity across cuts)
HERO_OPENING = Hero([
    dict(kind='walk', t0=6.4, start=(-3.0, -5.4), end=(0.0, -1.05), speed=0.58, step=0.41, hands='pockets', lean=3.0),
    dict(kind='stand', t0=14.55, pos=(0.0, -1.05), yaw=-7.0, hands='pockets', lean=1.5),
], look=[(0.0, 0, 6), (13.5, 0, 6), (15.6, 0, 3), (17.6, -4, -6), (21.5, -6, -5), (24.0, -2, 2), (29.2, -3, 1)], seed=1)

# Swash cycle phase: an up-rush begins at t=24.3 s (peaks ~26.4 s on the hero's boots in shot 04)
SWASH_PHASE = 1.0 - (24.3 / 6.58) % 1.0


def base_night(t):
    U = dict(NIGHT)
    P = dict(NIGHT_POST)
    U['uTime'] = t
    U['uSwashPhase'] = SWASH_PHASE
    U['uCloudOfs'] = (0.0016 * t, 0.0009 * t)          # slow cloud drift, continuous across cuts
    # clouds part from the moon with the full entrance of the female voice (16.00 s)
    U['uMoonVeil'] = 1.0 - ease_io((t - 15.2) / 3.4)
    U['uMoonClear'] = 0.0
    return U, P


def cam(U, P, pos, tgt, focal, focus, fstop=2.8, roll=0.0, t=0.0, seed=0, breath=1.0):
    dp, dr = drift(t, seed)
    pos = np.asarray(pos, float) + dp * breath
    tgt = np.asarray(tgt, float) + np.array([dr[0], dr[1], 0.0]) * np.linalg.norm(np.asarray(tgt, float) - pos) * breath
    U['uCamPos'] = pos.astype(np.float32)
    U['uCamRot'] = look_at(pos, tgt, roll)
    U['uFocal'] = float(focal)
    P['uFocal'] = float(focal)
    P['uFocusDist'] = float(focus)
    P['uFStop'] = float(fstop)
    U['uJitter'] = (0.0, 0.0)


def hero_on(U, hero, t):
    U.update(hero.state(t))
    U['uHero'] = 1


# ---------------------------------------------------------------- shots
def shot01(t, u):
    """EWS at sea: the Ocean breathes. Fade in from black on the first piano notes; glide toward the veiled moon."""
    U, P = base_night(t)
    pos = catmull([(7.0, 2.7, 26.0), (6.2, 2.5, 29.0), (5.4, 2.35, 31.6)], ease_io(u, 1.4))
    tgt = pos + np.array([-0.30, -0.035, 1.0]) * 50.0
    cam(U, P, pos, tgt, 26.0, 60.0, fstop=4.0, t=t, seed=1, roll=-0.4)
    P['uFade'] = 1.0 - ease_io(t / 4.2, 1.6)
    P['uExposure'] = NIGHT_POST['uExposure'] * 0.92
    U['uHero'] = 0
    return U, P


def shot02(t, u):
    """WS on the beach: a lone figure walks to the water's edge; lateral track with foreground parallax."""
    U, P = base_night(t)
    pos = lerp((6.6, 1.22, -13.2), (4.7, 1.3, -12.4), ease_io(u, 1.3))
    tgt = lerp((-1.6, 0.95, 4.0), (-1.2, 1.0, 4.5), ease_io(u, 1.3))
    hp = HERO_OPENING.state(t)['uJ'][0]
    focus = float(np.linalg.norm(np.asarray(hp) - np.asarray(pos)))
    cam(U, P, pos, tgt, 35.0, focus, fstop=2.8, t=t, seed=2)
    hero_on(U, HERO_OPENING, t)
    return U, P


def shot03(t, u):
    """MS from behind: the voice of the Ocean enters, the clouds part, the moon path lights up; slow push-in."""
    U, P = base_night(t)
    pos = lerp((1.75, 1.58, -8.1), (1.05, 1.5, -5.7), ease_io(u, 1.15))
    tgt = lerp((-0.9, 1.32, 8.0), (-1.1, 1.36, 8.0), ease_io(u, 1.2))
    hp = HERO_OPENING.state(t)['uJ'][3]
    focus = float(np.linalg.norm(np.asarray(hp) - np.asarray(pos)))
    cam(U, P, pos, tgt, 50.0, focus, fstop=2.2, t=t, seed=3)
    hero_on(U, HERO_OPENING, t)
    return U, P


def shot04(t, u):
    """High wide from behind: crane up reveals the long misty shoreline; the swash runs up around his boots and slides back."""
    U, P = base_night(t)
    e = ease_io(u, 1.25)
    pos = catmull([(3.2, 2.0, -10.2), (2.9, 3.9, -11.1), (2.5, 5.8, -12.0)], e)
    tgt = catmull([(0.0, 0.7, 0.0), (-0.3, 0.35, 2.5), (-0.7, 0.0, 6.5)], e)
    hp = HERO_OPENING.state(t)['uJ'][0]
    focus = float(np.linalg.norm(np.asarray(hp) - pos))
    cam(U, P, pos, tgt, 32.0, focus, fstop=4.0, t=t, seed=4, breath=0.7)
    U['uSwashReach'] = 0.36
    hero_on(U, HERO_OPENING, t)
    return U, P


SHOTS = [
    # id, start_frame, end_frame (inclusive), fn, description
    ('01', 0, 173, shot01, 'EWS море, проявление из черноты'),
    ('02', 174, 354, shot02, 'WS берег, герой идёт к кромке воды'),
    ('03', 355, 551, shot03, 'MS со спины, голос Океана, луна выходит из облаков'),
    ('04', 552, 698, shot04, 'HWS кран вверх: длинная береговая линия, накат вокруг ботинок'),
]


def frame_state(f):
    for sid, f0, f1, fn, _ in SHOTS:
        if f0 <= f <= f1:
            t = f / FPS
            u = (f - f0) / max(f1 - f0, 1)
            U, P = fn(t, u)
            return sid, U, P
    raise ValueError(f'frame {f} outside defined shots')
