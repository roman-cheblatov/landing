"""Generation runner for the Runway Developer API (one key gives Gen-4.5, Kling 3.0 Pro and Kling 4.0).

SAFETY: default is a DRY RUN that only prints the jobs and their cost. Paid calls need ALL of:
  --run  --confirm  --budget-usd N   and the env var RUNWAYML_API_SECRET.
Every submitted job is written to work/i2v/ledger.json; a run is refused if ledger + estimate > budget.

Stages
  refs   reference pack (refpack.py): candidates per reference image
  keys   photoreal keyframes per shot (needs approved refs in work/i2v/approved/refs/<id>.jpg)
  video  image-to-video per shot (needs approved keyframes in work/i2v/approved/keys/<shot>_<position>.jpg)

Examples
  python src/i2v/runway_gen.py refs  --only hero_master --variants 8           # dry run, prints cost
  python src/i2v/runway_gen.py video --shots 01-04 --run --confirm --budget-usd 40

NOTE: written against the published API schema (X-Runway-Version 2024-11-06); not yet exercised with a live key.
"""
import argparse, base64, io, json, os, sys, time, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(__file__))
import shots_i2v as S
from refpack import REFS, TAG

ROOT = S.ROOT
WORK = os.path.join(ROOT, 'work', 'i2v')
API = 'https://api.dev.runwayml.com/v1'
VERSION = '2024-11-06'
MODEL_ID = {'kling4': 'kling_4', 'kling3pro': 'kling3.0_pro', 'gen45': 'gen4.5'}
IMG = {  # image models: price per image, 16:9 ratio string, max references
    'gen4_image': dict(usd=0.08, ratio='1920:1080', max_refs=3),
    'gemini_image3_pro': dict(usd=0.20, ratio='2752:1536', max_refs=14),   # supports subject='human' references
}


def img_body(model, prompt, seed):
    b = dict(model=model, ratio=IMG[model]['ratio'], promptText=prompt[:1000])
    if model == 'gen4_image':
        b['seed'] = seed
    return b


def data_uri(path, max_side=1920):
    from PIL import Image
    im = Image.open(path).convert('RGB')
    im.thumbnail((max_side, max_side))
    b = io.BytesIO(); im.save(b, 'JPEG', quality=92)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()


def call(method, path, body=None):
    key = os.environ.get('RUNWAYML_API_SECRET')
    if not key:
        sys.exit('RUNWAYML_API_SECRET is not set — refusing to call the API.')
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={'Authorization': 'Bearer ' + key, 'X-Runway-Version': VERSION,
                                          'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        sys.exit(f'API error {e.code}: {e.read().decode()[:800]}')


def wait(task_id, out_path):
    while True:
        t = call('GET', f'/tasks/{task_id}')
        if t.get('status') == 'SUCCEEDED':
            urllib.request.urlretrieve(t['output'][0], out_path)
            return out_path
        if t.get('status') in ('FAILED', 'CANCELLED'):
            print('task failed', task_id, t.get('failure'), t.get('failureCode'))
            return None
        time.sleep(6)


def approved(kind, name):
    p = os.path.join(WORK, 'approved', kind, name + '.jpg')
    return p if os.path.exists(p) else None


def jobs_refs(only, variants, model='gen4_image'):
    out = []
    for rid, r in REFS.items():
        if only and rid not in only:
            continue
        refs = []
        for dep in r['refs']:
            path = approved('refs', dep) or (os.path.join(ROOT, 'refs', 'layout', 'ref_' + rid + '.jpg') if dep == 'layout' else None)
            refs.append(dict(tag=TAG.get(dep, dep[:16]), path=path))
        for v in range(variants):
            out.append(dict(kind='image', name=f'{rid}_{model[:6]}_v{v + 1}', model=model, usd=IMG[model]['usd'],
                            body=img_body(model, r['prompt'], 1000 + v), refs=refs[:IMG[model]['max_refs']]))
    return out


def jobs_keys(shots, variants, hero_model='gemini_image3_pro'):
    out = []
    for r in S.build():
        if r['shot'] not in shots:
            continue
        hero = any(x.startswith('hero') for x in r['refs'])
        model = hero_model if hero else 'gen4_image'
        refs = []
        if hero:
            hero_refs = [x for x in r['refs'] if x.startswith('hero')] + ['hero_master']
            for x in (hero_refs if model == 'gemini_image3_pro' else hero_refs[:1]):
                refs.append(dict(tag='hero', path=approved('refs', x), subject='human'))
        place = next((x for x in r['refs'] if not x.startswith('hero')), None)
        if place:
            refs.append(dict(tag='place', path=approved('refs', place)))
        for k in r['keyframes']:
            lay = os.path.join(ROOT, 'refs', 'layout', f"shot{r['shot']}_{k['position']}.jpg")
            rr = refs + ([dict(tag='layout', path=lay)] if os.path.exists(lay) else [])
            prompt = k['prompt'] + (' Composition as in @layout.' if os.path.exists(lay) else '') + (' Setting like @place.' if place else '')
            for v in range(variants):
                out.append(dict(kind='image', name=f"{r['shot']}_{k['position']}_v{v + 1}", model=model, usd=IMG[model]['usd'],
                                body=img_body(model, prompt, 2000 + v), refs=rr[:IMG[model]['max_refs']]))
    return out


def jobs_video(shots, takes=None, override=None):
    out = []
    for r in S.build():
        if r['shot'] not in shots:
            continue
        if override:
            r = dict(r, model=override, gen_s=min(r['gen_s'], 10) if override == 'gen45' else r['gen_s'])
        n = takes or r['takes']
        frames = [dict(position=k['position'], path=approved('keys', f"{r['shot']}_{k['position']}")) for k in r['keyframes']]
        body = dict(model=MODEL_ID[r['model']], promptText=r['motion_prompt'], duration=r['gen_s'])
        if r['model'] == 'kling4':
            body['ratio'] = 'auto_1080p'
        elif r['model'] == 'kling3pro':
            body['ratio'] = '1920:1080'
        else:
            body['ratio'] = '1280:720'
        if r['model'] == 'gen45':
            frames = frames[:1]
        refs = [dict(path=approved('refs', x)) for x in r['refs']] if r['model'] == 'kling4' else []
        for t in range(n):
            out.append(dict(kind='video', name=f"{r['shot']}_{r['model']}_take{t + 1}", model=r['model'], usd=r['gen_s'] * S.PRICE[r['model']],
                            body=dict(body, seed=3000 + t) if r['model'] != 'kling4' else body, frames=frames, refs=refs[:10 - len(frames)]))
    return out


def ledger():
    p = os.path.join(WORK, 'ledger.json')
    return json.load(open(p)) if os.path.exists(p) else []


def submit(job):
    body = dict(job['body'])
    if job['kind'] == 'image':
        refs = []
        for x in job['refs']:
            if not x['path']:
                continue
            ri = dict(uri=data_uri(x['path']), tag=x['tag'])
            if job['model'] == 'gemini_image3_pro' and x.get('subject'):
                ri['subject'] = x['subject']
            refs.append(ri)
        if refs:
            body['referenceImages'] = refs
        t = call('POST', '/text_to_image', body)
        out = os.path.join(WORK, 'candidates', job['name'] + '.jpg')
    else:
        frames = [dict(uri=data_uri(f['path']), position=f['position']) for f in job['frames']]
        body['promptImage'] = frames if len(frames) > 1 else frames[0]['uri']
        if job['refs']:
            body['references'] = [dict(uri=data_uri(x['path'])) for x in job['refs'] if x['path']]
        t = call('POST', '/image_to_video', body)
        out = os.path.join(WORK, 'takes', job['name'] + '.mp4')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    L = ledger()
    L.append(dict(name=job['name'], task=t.get('id'), usd=job['usd'], time=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())))
    json.dump(L, open(os.path.join(WORK, 'ledger.json'), 'w'), indent=1)
    return wait(t['id'], out)


def parse_shots(s):
    if not s:
        return []
    out = []
    for part in s.split(','):
        if '-' in part:
            a, b = part.split('-'); out += [f'{i:02d}' for i in range(int(a), int(b) + 1)]
        else:
            out.append(f'{int(part):02d}')
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('stage', choices=['refs', 'keys', 'video'])
    ap.add_argument('--shots', default='01-04')
    ap.add_argument('--only', default='')
    ap.add_argument('--variants', type=int, default=6)
    ap.add_argument('--takes', type=int, default=None)
    ap.add_argument('--img-model', default=None, choices=list(IMG))
    ap.add_argument('--model-override', default=None, choices=list(MODEL_ID), help='A/B a shot on another video model')
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--confirm', action='store_true')
    ap.add_argument('--budget-usd', type=float, default=0.0)
    a = ap.parse_args()
    shots = parse_shots(a.shots)
    if a.stage == 'refs':
        J = jobs_refs([x for x in a.only.split(',') if x], a.variants, a.img_model or 'gen4_image')
    elif a.stage == 'keys':
        J = jobs_keys(shots, a.variants, a.img_model or 'gemini_image3_pro')
    else:
        J = jobs_video(shots, a.takes, a.model_override)
    est = sum(j['usd'] for j in J)
    spent = sum(x['usd'] for x in ledger())
    missing = [j['name'] for j in J for f in (j.get('frames', []) + j.get('refs', [])) if f.get('path') is None]
    print(f'{len(J)} jobs, estimate ${est:.2f}; already spent ${spent:.2f}')
    for j in J[:60]:
        print(f"  {j['name']:<22} {j['model']:<10} ${j['usd']:.2f}")
    if missing:
        print(f'  ! {len(set(missing))} jobs still lack approved inputs (refs/keyframes) — they cannot run yet')
    if not (a.run and a.confirm):
        print('DRY RUN — nothing was sent. Paid run needs --run --confirm --budget-usd N.')
        sys.exit(0)
    if spent + est > a.budget_usd:
        sys.exit(f'Refused: spent ${spent:.2f} + estimate ${est:.2f} exceeds budget ${a.budget_usd:.2f}')
    if missing:
        sys.exit('Refused: approve the missing inputs first.')
    for j in J:
        print('submit', j['name'], '->', submit(j))
