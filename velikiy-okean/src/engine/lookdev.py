"""Look development: renders a grid of camera setups in one process (shaders JIT once).
python lookdev.py out_prefix W H t '{json overrides for world}' '{json overrides for post}'"""
import sys, os, json, time
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from gl import Renderer
from scene import NIGHT, NIGHT_POST, look_at
from hero import Hero

out, W, H, t = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4])
ow = json.loads(sys.argv[5]) if len(sys.argv) > 5 else {}
op = json.loads(sys.argv[6]) if len(sys.argv) > 6 else {}
cams = json.loads(sys.argv[7]) if len(sys.argv) > 7 else None
R = Renderer(W, H, 1.0)
CAMS = {
    'wide': ((-3.0, 1.55, -14.0), (0.0, 1.2, 10.0), 35.0, 13.0),
    'back': ((0.9, 1.62, -4.6), (0.0, 1.45, 4.0), 50.0, 3.6),
    'sea': ((0.0, 1.8, -2.0), (0.0, 1.0, 60.0), 28.0, 40.0),
    'low': ((2.5, 0.35, -3.0), (0.0, 0.9, 2.0), 32.0, 4.2),
}
hero = Hero([dict(kind='stand', t0=-100, pos=(0.0, -1.2), yaw=-6.0)], look=[(0, 0, 4)])
tiles = []
for name in (cams or list(CAMS)):
    pos, tgt, focal, focus = CAMS[name]
    U = dict(NIGHT); P = dict(NIGHT_POST)
    U.update(hero.state(t)); U['uHero'] = 1
    for k, v in ow.items():
        U[k] = np.array(v, np.float32) if isinstance(v, list) else v
    for k, v in op.items():
        P[k] = np.array(v, np.float32) if isinstance(v, list) else v
    U.update(uTime=t, uCamPos=np.array(pos, np.float32), uCamRot=look_at(pos, tgt), uFocal=focal, uJitter=(0.0, 0.0))
    P.update(uFocusDist=focus, uFocal=focal)
    t1 = time.time()
    img = R.render(U, P, frame=int(t * 24))
    print(name, round(time.time() - t1, 2), flush=True)
    tiles.append(img)
grid = np.concatenate([np.concatenate(tiles[i:i + 2], 1) for i in range(0, len(tiles), 2)], 0) if len(tiles) > 1 else tiles[0]
Image.fromarray(grid).save(out)
