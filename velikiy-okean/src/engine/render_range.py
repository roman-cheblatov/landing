"""Render a frame range of the film to an MP4 segment (video only) or PNG frames.
python render_range.py f0 f1 out.mp4 [W H ss] [--png dir] [--every N]"""
import sys, os, time, subprocess, argparse
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from gl import Renderer
import film

ap = argparse.ArgumentParser()
ap.add_argument('f0', type=int); ap.add_argument('f1', type=int); ap.add_argument('out')
ap.add_argument('--w', type=int, default=1920); ap.add_argument('--h', type=int, default=1080)
ap.add_argument('--ss', type=float, default=1.0)
ap.add_argument('--png', default=None)
ap.add_argument('--every', type=int, default=1)
ap.add_argument('--crf', type=int, default=14)
a = ap.parse_args()

R = Renderer(a.w, a.h, a.ss)
frames = list(range(a.f0, a.f1 + 1, a.every))
enc = None
if a.out != '-':
    fps = 24 / a.every
    enc = subprocess.Popen(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                            '-s', f'{a.w}x{a.h}', '-r', f'{fps}', '-i', '-', '-c:v', 'libx264', '-preset', 'slow',
                            '-crf', str(a.crf), '-tune', 'grain', '-pix_fmt', 'yuv420p', '-g', '48', '-bf', '2', a.out],
                           stdin=subprocess.PIPE)
if a.png:
    os.makedirs(a.png, exist_ok=True)
t0 = time.time()
for i, f in enumerate(frames):
    sid, U, P = film.frame_state(f)
    img = R.render(U, P, frame=f)
    if enc:
        enc.stdin.write(img.tobytes())
    if a.png:
        from PIL import Image
        Image.fromarray(img).save(os.path.join(a.png, f'f{f:05d}.png'))
    if i % 24 == 0 or i == len(frames) - 1:
        el = time.time() - t0
        print(f'frame {f} shot {sid} [{i + 1}/{len(frames)}] {el / (i + 1):.2f}s/frame, elapsed {el:.0f}s', flush=True)
if enc:
    enc.stdin.close(); enc.wait()
print('done', a.out, round(time.time() - t0, 1))
