"""Mux rendered video with the ORIGINAL audio (bit-exact stream copy) and run technical checks; build a contact sheet.

python assemble.py video.mp4 out.mp4 --f0 0 --f1 698 [--sheet sheet.png]

Audio: the MP3 stream is copied, never re-encoded. ffmpeg carries the encoder delay (1105 samples) into the MP4 edit
list, so the first decoded sample coincides with video frame 0 — the same t=0 used for TIMELINE.json. (Do NOT add
-itsoffset: that double-skips the delay and drops 23 ms of real audio; the check below measures the lag.)
"""
import argparse, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
SRC_MP3 = os.path.join(ROOT, 'media', 'source.mp3')
FPS = 24


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    r = run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', path])
    return json.loads(r.stdout)


def mp3_start(path):
    for s in probe(path)['streams']:
        if s['codec_type'] == 'audio':
            return float(s.get('start_time', 0.0))
    return 0.0


def mux(video, out, f0, f1):
    t0 = f0 / FPS
    dur = (f1 - f0 + 1) / FPS
    cmd = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', video]
    cmd += (['-ss', f'{t0:.6f}'] if t0 > 0 else []) + ['-i', SRC_MP3]
    cmd += ['-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'copy', '-t', f'{dur:.6f}',
            '-movflags', '+faststart', '-metadata', 'title=Великий Океан — Тихое возвращение', out]
    r = run(cmd)
    if r.returncode:
        sys.exit(r.stderr)


def checks(out, f0, f1, video):
    rep = {}
    p = probe(out)
    v = [s for s in p['streams'] if s['codec_type'] == 'video'][0]
    a = [s for s in p['streams'] if s['codec_type'] == 'audio'][0]
    rep['video'] = dict(codec=v['codec_name'], w=v['width'], h=v['height'], fps=v['r_frame_rate'], pix_fmt=v['pix_fmt'],
                        start=float(v.get('start_time', 0)), duration=float(v.get('duration', 0)))
    rep['audio'] = dict(codec=a['codec_name'], sr=int(a['sample_rate']), ch=a['channels'], start=float(a.get('start_time', 0)),
                        duration=float(a.get('duration', 0)), bit_rate=a.get('bit_rate'))
    r = run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', out])
    rep['video']['frames'] = int(r.stdout.strip() or 0)
    rep['expected_frames'] = f1 - f0 + 1
    # black frames
    r = run(['ffmpeg', '-hide_banner', '-i', out, '-vf', 'blackdetect=d=0.04:pic_th=0.985:pix_th=0.02', '-an', '-f', 'null', '-'])
    rep['black_segments'] = [l.split('blackdetect')[1].strip() for l in r.stderr.splitlines() if 'black_start' in l]
    # audio identity: decoded audio of the mux == decoded original for the same span (bit-exact samples)
    def pcm(path, ss=None, t=None, extra=()):
        cmd = ['ffmpeg', '-v', 'error']
        if ss is not None:
            cmd += ['-ss', f'{ss:.6f}']
        cmd += ['-i', path] + list(extra)
        if t is not None:
            cmd += ['-t', f'{t:.6f}']
        cmd += ['-map', '0:a:0', '-f', 's16le', '-ac', '2', '-ar', '48000', '-']
        return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.int16)
    dur = (f1 - f0 + 1) / FPS
    A = pcm(out).astype(np.int32)
    B = pcm(SRC_MP3).astype(np.int32)[int(round(f0 / FPS * 48000)) * 2:]
    n = min(len(A), len(B), int(dur * 48000) * 2)
    A, B = A[:n], B[:n]
    # find best lag within ±50 ms (should be 0)
    a1 = A[0::2][:48000 * 20].astype(np.float64); b1 = B[0::2][:48000 * 20].astype(np.float64)
    best = (0, -1)
    for lag in range(-2400, 2401, 1):
        if lag >= 0:
            c = np.dot(a1[lag:lag + 200000], b1[:200000])
        else:
            c = np.dot(a1[:200000], b1[-lag:-lag + 200000])
        if c > best[1]:
            best = (lag, c)
    rep['audio_lag_samples'] = best[0]
    rep['audio_lag_ms'] = round(best[0] / 48.0, 3)
    rep['audio_identical_samples'] = bool(np.array_equal(A, B)) if best[0] == 0 else False
    rep['audio_max_abs_diff'] = int(np.abs(A - B).max()) if best[0] == 0 else None
    return rep


def contact_sheet(video, out_png, f0, f1, shots, per_shot=4, tile=(480, 270)):
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 15)
        bold = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 17)
    except Exception:
        font = bold = None
    rows = []
    for sid, a, b, desc in shots:
        a, b = max(a, f0), min(b, f1)
        if a > b:
            continue
        idx = np.linspace(a, b, per_shot + 2)[1:-1].round().astype(int)
        tiles = []
        for f in idx:
            t = (f - f0) / FPS
            r = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t + 0.5 / FPS:.4f}', '-i', video, '-frames:v', '1',
                                '-vf', f'scale={tile[0]}:{tile[1]}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True)
            im = Image.frombuffer('RGB', tile, r.stdout[:tile[0] * tile[1] * 3])
            d = ImageDraw.Draw(im)
            tc = f / FPS
            lab = f'{int(tc // 60)}:{tc % 60:05.2f}  f{f}'
            d.rectangle([0, tile[1] - 24, 190, tile[1]], fill=(0, 0, 0))
            d.text((6, tile[1] - 21), lab, fill=(230, 230, 230), font=font)
            tiles.append(np.asarray(im))
        row = np.concatenate([np.pad(t_, ((0, 0), (0, 6), (0, 0))) for t_ in tiles], 1)
        head = Image.new('RGB', (row.shape[1], 30), (12, 14, 18))
        dh = ImageDraw.Draw(head)
        dh.text((8, 5), f'План {sid}: {desc}  [{a / FPS:.2f}–{(b + 1) / FPS:.2f} с, кадры {a}–{b}]', fill=(235, 235, 235), font=bold)
        rows.append(np.concatenate([np.asarray(head), row, np.zeros((6, row.shape[1], 3), np.uint8)], 0))
    sheet = np.concatenate(rows, 0)
    title = Image.new('RGB', (sheet.shape[1], 44), (0, 0, 0))
    dt = ImageDraw.Draw(title)
    dt.text((10, 10), 'Великий Океан — Тихое возвращение · тест · контакт-лист (1920×1080, 24 к/с, процедурный рендер)', fill=(255, 255, 255), font=bold)
    Image.fromarray(np.concatenate([np.asarray(title), sheet], 0)).save(out_png)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('video'); ap.add_argument('out')
    ap.add_argument('--f0', type=int, default=0); ap.add_argument('--f1', type=int, required=True)
    ap.add_argument('--sheet', default=None)
    ap.add_argument('--report', default=None)
    a = ap.parse_args()
    mux(a.video, a.out, a.f0, a.f1)
    rep = checks(a.out, a.f0, a.f1, a.video)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    if a.report:
        json.dump(rep, open(a.report, 'w'), ensure_ascii=False, indent=1)
    if a.sheet:
        sys.path.insert(0, HERE)
        import film
        shots = [(s[0], s[1], s[2], s[4]) for s in film.SHOTS]
        contact_sheet(a.video, a.sheet, a.f0, a.f1, shots)
        print('sheet', a.sheet)
