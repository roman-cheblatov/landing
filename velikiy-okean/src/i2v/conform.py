"""Conform approved I2V takes to the storyboard frame grid and mux the ORIGINAL audio.

Each approved take: work/i2v/approved/takes/<shot>.mp4 plus optional edit decisions in work/i2v/edl.json:
  {"03": {"in": 0.40, "speed": 0.96}, ...}   in = seconds skipped at the head; speed = playback rate (0.85-1.15)
The shot is then cut to exactly (end_frame - start_frame + 1) frames at 24 fps, scaled to 1920x1080, light common
grain/grade, joined, faded in from black for shot 01, and muxed with the untouched MP3 via assemble.mux + checks.

python src/i2v/conform.py --shots 01-04 --out out/photoreal_test_0000-0698.mp4
"""
import argparse, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'engine'))
import shots_i2v as S
from runway_gen import parse_shots

WORK = os.path.join(S.ROOT, 'work', 'i2v')


def conform_shot(sid, edl, out):
    st = S.STORY[sid]
    n = st['end_frame'] - st['start_frame'] + 1
    src = os.path.join(WORK, 'approved', 'takes', f'{sid}.mp4')
    e = edl.get(sid, {})
    speed = float(e.get('speed', 1.0))
    assert 0.85 <= speed <= 1.15, 'speed ramps beyond ±15 % look unnatural'
    vf = [f'setpts=(PTS-STARTPTS)/{speed}', 'fps=24', 'scale=1920:1080:flags=lanczos', 'setsar=1']
    if sid == '01':
        vf.append('fade=t=in:st=0:d=4.2')
    cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', str(e.get('in', 0.0)), '-i', src, '-an', '-vf', ','.join(vf),
           '-frames:v', str(n), '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', out]
    subprocess.run(cmd, check=True)
    got = int(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                              'stream=nb_read_frames', '-of', 'csv=p=0', out], capture_output=True, text=True).stdout.strip())
    assert got == n, f'shot {sid}: {got} frames, expected {n} (take too short after in/speed?)'
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--shots', default='01-04')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    shots = parse_shots(a.shots)
    edl_p = os.path.join(WORK, 'edl.json')
    edl = json.load(open(edl_p)) if os.path.exists(edl_p) else {}
    os.makedirs(os.path.join(WORK, 'conformed'), exist_ok=True)
    parts = [conform_shot(s, edl, os.path.join(WORK, 'conformed', f'{s}.mp4')) for s in shots]
    lst = os.path.join(WORK, 'conformed', 'list.txt')
    open(lst, 'w').write(''.join(f"file '{p}'\n" for p in parts))
    video = os.path.join(WORK, 'conformed', 'video.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', video], check=True)
    f0, f1 = S.STORY[shots[0]]['start_frame'], S.STORY[shots[-1]]['end_frame']
    subprocess.run([sys.executable, os.path.join(S.ROOT, 'src', 'engine', 'assemble.py'), video, a.out, '--f0', str(f0),
                    '--f1', str(f1), '--report', a.out + '.checks.json'], check=True)
