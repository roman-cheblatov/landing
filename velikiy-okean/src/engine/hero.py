"""The hero: procedural skeleton, gait and poses -> 20 joint positions for the SDF figure.

Joint order (must match world.frag):
 0 pelvis  1 chest  2 neck base  3 head centre
 4 L shoulder 5 L elbow 6 L wrist 7 L fingertips
 8 R shoulder 9 R elbow 10 R wrist 11 R fingertips
12 L hip 13 L knee 14 L ankle 15 L toe
16 R hip 17 R knee 18 R ankle 19 R toe
Body frame: x = hero's right, y = up, z = forward (facing). Units: metres. Height ~1.82 m.
"""
import math
import numpy as np

UP = np.array([0.0, 1.0, 0.0])

DIM = dict(pelvis=0.985, chest=1.30, neck=1.515, head=1.672, sh_w=0.181, sh_y=1.432,
           upper_arm=0.295, forearm=0.265, hand=0.17, hip_w=0.093, thigh=0.445, shin=0.435,
           ankle_h=0.085, foot=0.19)


def _n(v):
    l = np.linalg.norm(v)
    return v / l if l > 1e-9 else v


def smoothstep(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def two_bone_ik(root, target, l1, l2, pole):
    """Returns the middle joint position for a two-bone chain root->mid->end reaching target."""
    d = target - root
    dist = np.linalg.norm(d)
    dist_c = min(max(dist, abs(l1 - l2) + 1e-4), l1 + l2 - 1e-4)
    dirv = d / max(dist, 1e-9)
    a = (l1 * l1 - l2 * l2 + dist_c * dist_c) / (2 * dist_c)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    pole_dir = _n(pole - dirv * np.dot(pole, dirv))
    mid = root + dirv * a + pole_dir * h
    end = root + dirv * dist_c
    return mid, end


class Hero:
    """Evaluates the hero at time t from a list of actions.
    actions: list of dicts, evaluated in order, each with 't0','t1'. Kinds:
      stand: pos (x,z), yaw (deg)
      walk:  start (x,z), end (x,z), speed (m/s)  — footstep planned, ends standing at 'end'
    Overlays (any action): head_yaw / head_pitch keyframes, hands='pockets'|'free', breathe.
    """

    def __init__(self, actions, look=None, seed=0):
        self.actions = sorted(actions, key=lambda a: a['t0'])
        self.look = look or []   # list of (t, yaw_deg, pitch_deg) relative to body
        self.rng = np.random.default_rng(seed)
        self._plans = {}

    # ---------------- footstep planning ----------------
    def _plan(self, a):
        key = id(a)
        if key in self._plans:
            return self._plans[key]
        s = np.array(a['start'], float)
        e = np.array(a['end'], float)
        L = np.linalg.norm(e - s)
        fwd = (e - s) / max(L, 1e-6)
        right = np.array([fwd[1], -fwd[0]])  # in xz: right of forward (x,z)->(z,-x)
        v = a.get('speed', 0.55)
        step = a.get('step', 0.40)
        n = max(int(math.ceil(L / step)), 1)
        step = L / n
        dur = L / v
        tstep = dur / n
        steps = []  # (t_land, foot(0=L,1=R), pos xz)
        for k in range(1, n + 1):
            foot = (k + (0 if a.get('lead', 'L') == 'L' else 1)) % 2
            pos = s + fwd * (k * step) + right * (DIM['hip_w'] * 1.15) * (1 if foot == 1 else -1)
            steps.append((a['t0'] + k * tstep, foot, pos))
        # final closing step: trailing foot comes alongside
        last_foot = steps[-1][1]
        other = 1 - last_foot
        pos = e + right * (DIM['hip_w'] * 1.15) * (1 if other == 1 else -1)
        steps.append((a['t0'] + dur + tstep * 0.85, other, pos))
        plan = dict(fwd=fwd, right=right, dur=dur, tstep=tstep, steps=steps, s=s, e=e, t_end=a['t0'] + dur + tstep * 0.85)
        self._plans[key] = plan
        return plan

    def _feet_walk(self, a, t):
        p = self._plan(a)
        fwd, right, tstep = p['fwd'], p['right'], p['tstep']
        start_feet = [p['s'] - right * DIM['hip_w'] * 1.15, p['s'] + right * DIM['hip_w'] * 1.15]
        feet = []
        lifts = []
        for foot in (0, 1):
            prev_t, prev_pos = a['t0'] - 10.0, start_feet[foot]
            nxt = None
            for (tl, f, pos) in p['steps']:
                if f != foot:
                    continue
                if tl <= t:
                    prev_t, prev_pos = tl, pos
                else:
                    nxt = (tl, pos)
                    break
            if nxt is None:
                feet.append(prev_pos); lifts.append(0.0)
                continue
            swing_dur = tstep * 1.15
            t_lift = nxt[0] - swing_dur
            if t < t_lift:
                feet.append(prev_pos); lifts.append(0.0)
            else:
                u = (t - t_lift) / swing_dur
                ue = ease(u)
                feet.append(prev_pos + (nxt[1] - prev_pos) * ue)
                lifts.append(math.sin(math.pi * u))
        # pelvis follows the centre of support with a smooth lead
        tt = min(max((t - a['t0']) / p['dur'], 0.0), 1.0)
        prog = tt
        base = p['s'] + (p['e'] - p['s']) * prog
        return feet, lifts, base, fwd

    # ---------------- evaluation ----------------
    def state(self, t):
        act = None
        for a in self.actions:
            if a['t0'] <= t:
                act = a
        if act is None:
            act = self.actions[0]
        yaw = None
        if act['kind'] == 'stand':
            pos = np.array(act['pos'], float)
            yaw = math.radians(act.get('yaw', 0.0))
            fwd = np.array([math.sin(yaw), math.cos(yaw)])
            right = np.array([fwd[1], -fwd[0]])
            stance = act.get('stance', 1.0)
            feet = [pos - right * DIM['hip_w'] * 1.45 * stance + fwd * 0.07 * stance,
                    pos + right * DIM['hip_w'] * 0.95 * stance - fwd * 0.02 * stance]
            lifts = [0.0, 0.0]
            base = pos
            gait = 0.0
        else:
            plan = self._plan(act)
            if t > plan['t_end']:
                pos = plan['e']; fwd = plan['fwd']; right = plan['right']
                feet = [pos - right * DIM['hip_w'] * 1.15, pos + right * DIM['hip_w'] * 1.15]
                lifts = [0.0, 0.0]; base = pos; gait = 0.0
            else:
                feet, lifts, base, fwd = self._feet_walk(act, t)
                gait = 1.0
            yaw = math.atan2(fwd[0], fwd[1])
        return self._build(t, base, yaw, feet, lifts, gait, act)

    def _look(self, t):
        if not self.look:
            return 0.0, 0.0
        ks = self.look
        if t <= ks[0][0]:
            return ks[0][1], ks[0][2]
        for (t0, y0, p0), (t1, y1, p1) in zip(ks[:-1], ks[1:]):
            if t0 <= t <= t1:
                u = ease((t - t0) / max(t1 - t0, 1e-6))
                return y0 + (y1 - y0) * u, p0 + (p1 - p0) * u
        return ks[-1][1], ks[-1][2]

    def _build(self, t, base, yaw, feet, lifts, gait, act):
        fwd3 = np.array([math.sin(yaw), 0.0, math.cos(yaw)])
        right3 = np.array([math.cos(yaw), 0.0, -math.sin(yaw)])
        b3 = np.array([base[0], 0.0, base[1]])
        breath = math.sin(t * 2 * math.pi / 4.6)
        sway = (0.006 * math.sin(t * 2 * math.pi / 7.3) + 0.022) * (1 - gait)   # weight on the right leg
        # pelvis height: bob while walking (lowest at double support)
        bob = 0.0
        if gait > 0:
            phase = (lifts[0] - lifts[1])
            bob = 0.012 * (abs(phase) - 0.5)
        pelvis = b3 + UP * (DIM['pelvis'] - 0.006 * (1 - gait) - 0.024 * gait + bob) + right3 * sway
        if gait > 0:
            # shift over stance foot
            stance = 0 if lifts[0] < lifts[1] else 1
            sf = np.array([feet[stance][0], 0, feet[stance][1]])
            lat = np.dot(sf - pelvis, right3)
            pelvis = pelvis + right3 * lat * 0.12
        lean = math.radians(act.get('lean', 2.0) + 2.5 * gait)
        spine_up = _n(UP * math.cos(lean) + fwd3 * math.sin(lean))
        chest = pelvis + spine_up * (DIM['chest'] - DIM['pelvis']) + UP * 0.003 * breath
        neck = pelvis + spine_up * (DIM['neck'] - DIM['pelvis']) + UP * 0.004 * breath
        hy, hp = self._look(t)
        hy += 2.0 * math.sin(t * 0.37) * (1 - gait)
        hyaw = yaw + math.radians(hy)
        hpitch = math.radians(hp + act.get('head_pitch', 0.0))
        head_fwd = np.array([math.sin(hyaw) * math.cos(hpitch), -math.sin(hpitch), math.cos(hyaw) * math.cos(hpitch)])
        head = neck + UP * (DIM['head'] - DIM['neck']) * 0.98 + head_fwd * 0.012 + spine_up * 0.0
        shL = neck - spine_up * (DIM['neck'] - DIM['sh_y']) - right3 * DIM['sh_w'] + UP * 0.003 * breath
        shR = neck - spine_up * (DIM['neck'] - DIM['sh_y']) + right3 * DIM['sh_w'] + UP * 0.003 * breath
        J = [pelvis, chest, neck, head]
        hands = act.get('hands', 'pockets')
        for side, sh in ((-1, shL), (1, shR)):
            if hands == 'pockets':
                target = pelvis + right3 * side * 0.124 + fwd3 * 0.088 - UP * 0.07
                pole = right3 * side * 0.95 - fwd3 * 0.55 - UP * 0.1
                elbow, wrist = two_bone_ik(sh, target, DIM['upper_arm'], DIM['forearm'], pole)
                tip = wrist + _n(-UP * 0.85 - fwd3 * 0.15 - right3 * side * 0.25) * 0.075   # hand inside the pocket
            else:
                swing = 0.0
                if gait > 0:
                    swing = 0.25 * ((lifts[0] if side > 0 else lifts[1]) - 0.5)
                arm_dir = _n(-UP + fwd3 * (0.08 + swing) + right3 * side * 0.08)
                elbow = sh + arm_dir * DIM['upper_arm']
                fdir = _n(arm_dir + fwd3 * 0.25)
                wrist = elbow + fdir * DIM['forearm']
                tip = wrist + _n(fdir + fwd3 * 0.05) * DIM['hand']
            J += [sh, elbow, wrist, tip]
        for side, ft, lift in ((-1, feet[0], lifts[0]), (1, feet[1], lifts[1])):
            hip = pelvis + right3 * side * DIM['hip_w'] - UP * 0.012
            f3 = np.array([ft[0], 0.0, ft[1]])
            ankle_t = f3 + UP * (DIM['ankle_h'] + 0.07 * lift) - fwd3 * 0.02
            knee, ankle = two_bone_ik(hip, ankle_t, DIM['thigh'], DIM['shin'], fwd3 + right3 * side * 0.08)
            pitch = -0.25 * lift
            toe = ankle + _n(fwd3 * math.cos(pitch) + UP * math.sin(pitch) + right3 * side * 0.08) * DIM['foot'] - UP * (DIM['ankle_h'] - 0.03) * (1 - lift * 0.5)
            J += [hip, knee, ankle, toe]
        J = np.array(J, dtype=np.float32)
        hem = 0.47 + (pelvis[1] - DIM['pelvis'])
        lo = J.min(0) - 0.35
        hi = J.max(0) + 0.35
        c = (lo + hi) * 0.5
        r = float(np.linalg.norm(hi - lo) * 0.5)
        return dict(uJ=J, uBodyFwd=fwd3.astype(np.float32), uHeadFwd=head_fwd.astype(np.float32),
                    uHemY=float(hem), uHeroBound=np.array([c[0], c[1], c[2], r], np.float32))
