"""Render specific film frames to PNG at full resolution: python stills_at.py outdir f1 f2 ... [--ss 1.0]"""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image
from gl import Renderer
import film
args = sys.argv[1:]
ss = 1.0
if '--ss' in args:
    i = args.index('--ss'); ss = float(args[i + 1]); del args[i:i + 2]
out = args[0]; frames = [int(x) for x in args[1:]]
os.makedirs(out, exist_ok=True)
R = Renderer(1920, 1080, ss)
for f in frames:
    t0 = time.time()
    sid, U, P = film.frame_state(f)
    Image.fromarray(R.render(U, P, frame=f)).save(f'{out}/f{f:05d}.png')
    print(f, sid, round(time.time() - t0, 2), flush=True)
