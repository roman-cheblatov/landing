"""Render a single still for look development: python still.py out.png W H t [ss]"""
import sys
import time
import numpy as np
from PIL import Image
sys.path.insert(0, __import__('os').path.dirname(__file__))
from gl import Renderer
from scene import NIGHT, NIGHT_POST, look_at
from hero import Hero

out, W, H, t = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4])
ss = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
cam = sys.argv[6] if len(sys.argv) > 6 else 'wide'

t0 = time.time()
R = Renderer(W, H, ss)
print('compile', round(time.time() - t0, 2), flush=True)
U = dict(NIGHT)
P = dict(NIGHT_POST)
hero = Hero([dict(kind='stand', t0=-100, pos=(0.0, -1.2), yaw=-6.0)], look=[(0, 0, 4)])
U.update(hero.state(t)); U['uHero'] = 1
cams = {
    'wide': ((-3.0, 1.55, -14.0), (0.0, 1.2, 10.0), 35.0, 14.0),
    'back': ((0.9, 1.62, -4.6), (0.0, 1.45, 4.0), 50.0, 3.6),
    'sea': ((0.0, 1.8, -2.0), (0.0, 1.0, 60.0), 28.0, 40.0),
}
pos, tgt, focal, focus = cams[cam]
U.update(uTime=t, uCamPos=np.array(pos, np.float32), uCamRot=look_at(pos, tgt), uFocal=focal, uJitter=(0.0, 0.0))
P.update(uFocusDist=focus, uFocal=focal)
t1 = time.time()
img = R.render(U, P, frame=int(t * 24))
print('render', round(time.time() - t1, 2), flush=True)
Image.fromarray(img).save(out)
