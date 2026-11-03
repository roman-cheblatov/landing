"""Character reference sheet: the hero from several angles in neutral studio light.
python turnaround.py out.png [pose]"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from gl import Renderer
from scene import NIGHT, NIGHT_POST, look_at, dir_from_angles
from hero import Hero

out = sys.argv[1]
pose = sys.argv[2] if len(sys.argv) > 2 else 'stand'
W, H = 480, 720
R = Renderer(W, H, 1.0)
if pose == 'walk':
    hero = Hero([dict(kind='walk', t0=0.0, start=(0.0, -2.0), end=(0.0, 3.0), speed=0.55, hands='pockets')])
    tt = 3.7
else:
    hero = Hero([dict(kind='stand', t0=-100, pos=(0.0, 0.0), yaw=0.0, hands='pockets')], look=[(0, 0, 0)])
    tt = 1.0
st = hero.state(tt)
c = st['uHeroBound'][:3]
views = [('спереди', 0), ('3/4 спереди', 35), ('профиль', 90), ('3/4 со спины', 145), ('со спины', 180)]
tiles = []
for label, az in views:
    U = dict(NIGHT); P = dict(NIGHT_POST)
    U.update(st); U['uHero'] = 1; U['uStudio'] = 1
    a = math.radians(az)
    dist = 7.5
    pos = np.array([c[0] + math.sin(a) * dist, 1.0, c[2] + math.cos(a) * dist])
    tgt = np.array([c[0], 0.93, c[2]])
    U.update(uTime=tt, uCamPos=pos.astype(np.float32), uCamRot=look_at(pos, tgt), uFocal=85.0 * 0.9, uJitter=(0.0, 0.0),
             uMoonDir=dir_from_angles(az + 40.0, 35.0), uMoonCol=np.array([2.2, 2.15, 2.1], np.float32),
             uAmbient=np.array([0.55, 0.57, 0.62], np.float32), uSunCol=np.array([0, 0, 0], np.float32), uCoatWind=0.0)
    P.update(uExposure=1.0, uFocusDist=dist, uFocal=76.5, uMaxCoc=0.0, uVignette=0.0, uGrain=0.0, uBloom=0.0, uHalation=0.0,
             uSat=1.0, uContrast=1.0, uLift=np.zeros(3, np.float32), uGain=np.ones(3, np.float32), uGammaG=np.ones(3, np.float32),
             uShadowTint=np.zeros(3, np.float32), uHighTint=np.zeros(3, np.float32))
    img = Image.fromarray(R.render(U, P, frame=0))
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
    except Exception:
        f = None
    d.text((14, 12), label, fill=(225, 225, 225), font=f)
    tiles.append(np.asarray(img))
sheet = np.concatenate(tiles, 1)
# height ruler (1.82 m reference)
Image.fromarray(sheet).save(out)
print('saved', out)
