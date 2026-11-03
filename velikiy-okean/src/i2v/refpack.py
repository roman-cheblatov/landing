"""Reference pack: one photoreal 'master' image per continuity element. Generated FIRST, approved by the director,
then used as @tags in every keyframe (gen4_image: up to 3 references) and as Kling 4.0 `references` (up to 10).

Order matters: hero_master is chosen first (text only, several candidates); every other hero_* reference is then
generated WITH hero_master as reference, so the face, build and coat are inherited, not re-invented."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from bible import HERO, CAMERA, LOOK, LOCATIONS, compose

NEUTRAL = 'Soft overcast dawn light, neutral grey-blue tones, sharp focus, true-to-life textures'

REFS = {
 # ---- hero (hero_master first; others use @hero = hero_master) ----
 'hero_master': dict(refs=[], prompt=compose(
     'Full-length photograph of ' + HERO + ', standing three-quarter from behind on an empty beach, looking at the sea, hands in coat pockets',
     NEUTRAL, CAMERA, 'Character reference photo for a feature film, no stylisation')),
 'hero_back': dict(refs=['hero_master'], prompt=compose(
     '@hero seen exactly from behind, full body, standing still at the waterline at night, hands in coat pockets, moonlight from the front creating a silver rim on collar and shoulders',
     LOCATIONS['BEACH'], LOOK['N2'], CAMERA)),
 'hero_walk': dict(refs=['hero_master'], prompt=compose(
     '@hero walking slowly on wet sand, three-quarter back view, mid-stride, coat hem swinging, hands in pockets, natural weight on the front foot',
     LOCATIONS['BEACH'], LOOK['N1'], CAMERA)),
 'hero_profile': dict(refs=['hero_master'], prompt=compose(
     '@hero in strict profile facing right toward the sea, medium shot, collar up, face mostly in shadow with a thin moonlit rim along forehead, nose and lips',
     LOOK['N2'], CAMERA)),
 'hero_hair_back': dict(refs=['hero_master'], prompt=compose(
     'Close-up of the back of the head and the raised wool collar of @hero, short dark-brown hair ruffled by wind, fine wool texture, moonlit rim',
     LOOK['N2'], CAMERA)),
 'hero_hands': dict(refs=['hero_master'], prompt=compose(
     'Close-up of the bare hands of @hero, weathered, no rings, coat sleeve cuffs visible, one hand near the surface of shallow sea water',
     NEUTRAL, CAMERA)),
 'hero_kneel': dict(refs=['hero_master'], prompt=compose(
     '@hero kneeling in calm shallow sea water up to his hips, profile, head slightly bowed, the wet coat floating around him',
     LOCATIONS['SHALLOWS'], LOOK['D2'], CAMERA)),
 'hero_face34': dict(refs=['hero_master'], prompt=compose(
     'Three-quarter portrait of @hero, calm, serious, tired eyes, light stubble, natural skin pores and fine lines, no retouching',
     NEUTRAL, CAMERA, 'For internal continuity only')),
 # ---- ocean states ----
 'ocean_n1': dict(refs=['layout'], prompt=compose('Open sea at night seen from 2.5 m above the water', LOOK['N1'], CAMERA)),
 'ocean_n2': dict(refs=['layout'], prompt=compose('The sea from the beach at night with a long moon path', LOOK['N2'], CAMERA)),
 'ocean_n4': dict(refs=[], prompt=compose('The sea from a rocky promontory at night as clouds open', LOOK['N4'], CAMERA)),
 'ocean_d0': dict(refs=[], prompt=compose('Calm sea surface in dense milky fog', LOOK['D0'], CAMERA)),
 'ocean_d2': dict(refs=[], prompt=compose('Horizon over a calm sea', LOOK['D2'], CAMERA)),
 'ocean_d3': dict(refs=[], prompt=compose('Fog bank over a calm sea with the sun rim breaking through', LOOK['D3'], CAMERA)),
 'ocean_d4': dict(refs=[], prompt=compose('Open sea at sunrise from low altitude', LOOK['D4'], CAMERA)),
 'ocean_d5': dict(refs=[], prompt=compose('Horizon with a long sun path on the water', LOOK['D5'], CAMERA)),
 'swash_foam': dict(refs=[], prompt=compose('Close detail of a thin sheet of surf running up mirror-wet sand, real foam lace, bubbles and sand grains, moonlight', CAMERA)),
 # ---- locations ----
 'beach_night': dict(refs=['layout'], prompt=compose(LOCATIONS['BEACH'], LOOK['N1'], CAMERA)),
 'beach_predawn': dict(refs=['beach_night'], prompt=compose('The same beach as @beach', LOOK['D0'], CAMERA)),
 'beach_morning': dict(refs=['beach_night'], prompt=compose('The same beach as @beach, morning, a line of footprints leading into the water', LOOK['D5'], CAMERA)),
 'basalt_night': dict(refs=[], prompt=compose(LOCATIONS['BASALT'], LOOK['N3'], CAMERA)),
 'pools_blue': dict(refs=[], prompt=compose(LOCATIONS['POOLS'], LOOK['D1'], CAMERA)),
 'shallows_fog': dict(refs=[], prompt=compose(LOCATIONS['SHALLOWS'], LOOK['D0'], CAMERA)),
 'shallows_pearl': dict(refs=[], prompt=compose(LOCATIONS['SHALLOWS'], LOOK['D2'], CAMERA)),
 'aerial_shore': dict(refs=[], prompt=compose('Aerial view of the long sandy shoreline with lines of white surf, misty', LOOK['N2'], CAMERA)),
}

TAG = {'hero_master': 'hero', 'beach_night': 'beach', 'layout': 'layout'}


if __name__ == '__main__':
    import shots_i2v as S
    use = {}
    for sid, s in S.SH.items():
        for r in s['refs']:
            use.setdefault(r, []).append(sid)
    out = ['# Единые референсы: герой, Океан, локации\n',
           'Сгенерировано из `src/i2v/refpack.py`. Порядок работы:\n',
           '1. **hero_master** — 8 кандидатов только по тексту. Вы выбираете одного: это «кастинг» героя.',
           '2. Остальные `hero_*` генерируются **с hero_master как референсом** (`@hero`): лицо, телосложение и пальто наследуются, а не придумываются заново.',
           '3. Океан и локации: по 6 кандидатов. Для `ocean_n1`, `ocean_n2` и `beach_night` композиционным референсом (`@layout`) служат кадры утверждённого теста (`refs/layout/`).',
           '4. Утверждённые изображения кладутся в `work/i2v/approved/refs/<id>.jpg`. Дальше они автоматически идут во все ключевые кадры (gen4_image, до 3 референсов) и в видео Kling 4.0 (`references`, до 10).\n',
           '## Описание героя (дословно во всех промптах)\n', f'> {HERO}\n',
           '| ID | Назначение | Зависит от | Используется в планах |', '|---|---|---|---|']
    for rid, r in REFS.items():
        out.append(f"| `{rid}` | {S.REF_IDS.get(rid, 'мастер-образ героя (кастинг)')} | {', '.join(r['refs']) or '—'} | {', '.join(use.get(rid, ['все (через hero_*)'] if rid == 'hero_master' else []))} |")
    out.append('\n## Промпты референсов\n')
    for rid, r in REFS.items():
        out.append(f"**{rid}**\n\n```\n{r['prompt']}\n```\n")
    open(os.path.join(S.ROOT, 'docs', 'i2v', 'REFERENCES.md'), 'w').write('\n'.join(out) + '\n')
    print('ok', len(REFS))
