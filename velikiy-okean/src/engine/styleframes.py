"""First-pass style frames for later acts (not final shots): python styleframes.py outdir"""
import sys, os, math
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from gl import Renderer
from scene import PEARL, PEARL_POST, GOLD, GOLD_POST, look_at
from hero import Hero
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
R = Renderer(1920, 1080, 1.0)
hero_stand = Hero([dict(kind='stand', t0=-100, pos=(0.0, 3.5), yaw=-8.0, hands='pockets')], look=[(0, -3, -2)])
frames = [
    ('D2_pearl_shot29', PEARL, PEARL_POST, (1.6, 1.45, -3.2), (-0.5, 1.2, 12.0), 50.0, 3.0, hero_stand, 200.0),
    ('D4_gold_shot35', GOLD, GOLD_POST, (4.0, 3.4, 42.0), (-3.5, 0.3, 100.0), 26.0, 60.0, None, 245.0),
    ('D4_gold_shot38', GOLD, GOLD_POST, (1.3, 1.25, -1.5), (-0.6, 1.0, 14.0), 50.0, 5.2, hero_stand, 266.0),
]
for name, W, P0, pos, tgt, focal, focus, hero, t in frames:
    U = dict(W); P = dict(P0)
    U.update(uTime=t, uCamPos=np.array(pos, np.float32), uCamRot=look_at(pos, tgt), uFocal=focal, uJitter=(0.0, 0.0), uSwashPhase=0.3)
    if hero:
        U.update(hero.state(t)); U['uHero'] = 1
    else:
        U['uHero'] = 0
    P.update(uFocusDist=focus, uFocal=focal)
    Image.fromarray(R.render(U, P, frame=int(t * 24))).save(f'{out}/{name}.png')
    print(name, flush=True)
