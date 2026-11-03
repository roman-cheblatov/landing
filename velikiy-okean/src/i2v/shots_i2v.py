"""Image-to-Video production plan per shot, built on top of the approved storyboard (docs/shots.json).
Generates docs/i2v/SHOT_PROMPTS.md and docs/i2v/prompts.json and computes the budget.

Per shot:
  model      kling4 (Kling 4.0 1080p: first/middle/last keyframes + up to 10 references, 3-30 s)
             kling3pro (Kling 3.0 Pro 1920x1080: first/last keyframes, 1-15 s, cheapest 1080p)
             gen45 (Runway Gen-4.5: first frame, 2-10 s, 1280x720 -> needs upscale; used as A/B for water)
  gen_s      generated duration (shot length + handles, rounded up)
  keys       keyframes to create as photoreal stills: (position, description)
  motion     what happens + camera, written for the video model
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from bible import HERO, HERO_SHORT, CAMERA, REALISM, AVOID, LOOK, LOCATIONS, compose

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Official Runway API prices, USD per output second (docs.dev.runwayml.com/guides/pricing, read 2026-11-03; $0.01/credit)
PRICE = {
    'kling4': 0.188,        # Kling 4.0 1080p, promo through 2026-11-30 UTC (list 0.235)
    'kling4_list': 0.235,
    'kling3pro': 0.12,      # Kling 3.0 Pro, no audio
    'gen45': 0.12,          # Gen-4.5 (720p)
}
IMG_PRICE = 0.08            # gen4_image 1080p, per image
IMG_PRICE_HQ = 0.20         # gemini_image3_pro per image (A/B for hero sheets)

R = 'refs'  # shorthand

SH = {
 '01': dict(model='kling3pro', gen_s=8, loc='OPEN', refs=['ocean_n1'],
   keys=[('first', 'Extreme wide shot low over the open night sea, camera 2.5 m above the water looking toward the horizon; '
                   'the moon hidden in a cloud bank, its halo glowing; long slow swells, low mist; nobody in frame')],
   motion=('Slow steady glide forward over the water toward the veiled moon, slight descent, a barely perceptible roll. '
           'Long swells rise and fall slowly, mist drifts left to right, the moon halo breathes softly behind thin clouds. '
           'No people. Calm, contemplative.'),
   note='Fade from black 0–4.2 s is done in the edit, not generated.'),
 '02': dict(model='kling4', gen_s=9, loc='BEACH', refs=['hero_back', 'hero_walk', 'hero_profile', 'beach_night', 'ocean_n1'],
   keys=[('first', 'Wide shot on the dark beach at night, 35 mm, camera 1.2 m high; the man small in frame on the left, '
                   'walking from the dunes toward the waterline, hands in his coat pockets; mirror-wet sand reflects the moon halo'),
         ('last', 'Same framing slightly tracked left: the man now standing still at the edge of the swash, facing the sea')],
   motion=('Lateral dolly from right to left with foreground sand parallax. @hero walks slowly and heavily toward the '
           'waterline with hands in his coat pockets, coat hem swaying with each step, wet sand darkening under his boots; '
           'he slows down and stops at the edge of the swash. Thin foam slides up the sand and back. Mist drifts. '),
   note='The stop must land just before the cut at 14.79 s.'),
 '03': dict(model='kling4', gen_s=9, loc='BEACH', refs=['hero_back', 'hero_hair_back', 'beach_night', 'ocean_n2'],
   keys=[('first', 'Medium shot from behind, 50 mm, the man standing on the right third at the waterline facing the night '
                   'sea; moon still veiled, sea dark lead-grey, faint glow behind clouds on the left'),
         ('last', 'Same composition 2 m closer: the clouds have parted, the moon is out of frame top-left and a long '
                  'glittering silver moon path lies on the sea on the left third; his head slightly raised toward it, rim light '
                  'on collar and hair')],
   motion=('Very slow push-in toward @hero from behind. Gradually the clouds part and the moonlight comes through: a silver '
           'moon path ignites across the sea on the left and brightens, the mist lights up; he slowly lifts his head toward '
           'the light. His coat moves gently in the wind, fine hair at the nape stirs. Real water glitter, no glow effects.'),
   note='Light change must peak around 16.0–18.5 s (full entrance of the voice); chosen take may be speed-ramped ±8 %.'),
 '04': dict(model='kling4', gen_s=8, loc='BEACH', refs=['hero_back', 'beach_night', 'ocean_n2', 'swash_foam'],
   keys=[('first', 'High wide shot from behind, camera 2 m high, the man small at the waterline, long misty shoreline curving away, moon path ahead'),
         ('last', 'Camera now 6 m high and tilted toward the sea: the long shoreline, lace of foam around his boots, the moon path')],
   motion=('Smooth crane up from 2 m to 6 m while tilting down toward the sea. A thin sheet of surf runs up the mirror-wet '
           'sand, foam lace flows around @hero\'s boots and slides back; he stands still, coat hem moving in the wind. '
           'Long misty shoreline, glittering moon path.'),
   note='Run-up peak ≈ 26.4 s; backwash with the end of the vocal phrase at 29.07 s.'),
 '05': dict(model='kling3pro', gen_s=10, loc='BEACH', refs=['hero_back', 'swash_foam', 'ocean_n2'],
   keys=[('first', 'Close-up low over mirror-wet sand at night: in the thin film of water the upside-down reflection of the man '
                   'and the moon path; his boots at the top edge of frame, out of focus')],
   motion=('Slow sideways drift a few centimetres above the sand. A thin sheet of water slides in and gently erases the '
           'reflection into trembling silver fragments, then drains away leaving glistening sand.'),
   note=''),
 '06': dict(model='kling4', gen_s=6, loc='BEACH', refs=['hero_back', 'hero_profile', 'hero_hands', 'ocean_n2'],
   keys=[('first', 'Medium close-up 3/4 from behind, 65 mm, moonlit: his shoulders, collar and the back of his head; hands in coat pockets')],
   motion=('Static camera with a barely perceptible float. @hero slowly takes his hands out of the coat pockets and lets them '
           'hang open by his sides; he exhales and his breath turns to vapour that drifts and dissolves into the sea mist.'),
   note='Breath vapour must stay subtle and real (cold night).'),
 '07': dict(model='kling3pro', gen_s=6, loc='OPEN', refs=['ocean_n2'],
   keys=[('first', 'Macro photograph at night: droplets of sea spray suspended in moonlight above dark water, each droplet refracting '
                   'the moon; in the water below a few faint blue-green specks of natural bioluminescent plankton; very shallow depth of field')],
   motion=('Slow macro slider movement through the suspended droplets in slow motion; droplets drift and fall, a few tiny '
           'bioluminescent specks flicker faintly in the dark water below. Natural, restrained, no particles effect.'),
   note='Keep bioluminescence documentary-real (sparse, dim).'),
 '08': dict(model='kling3pro', gen_s=7, loc='OPEN', refs=['ocean_n2'],
   keys=[('first', 'Extreme wide shot over the open sea at night, long swell lines marching toward land under a moonlit sky with streaked clouds')],
   motion=('Very slow rise over the sea. The long swells move in slow motion while the clouds above race in time-lapse — '
           'two scales of time at once. Silver moonlight on the swell backs.'),
   note='If the model refuses mixed time scales: generate swell plate (slow) and sky plate (time-lapse) separately and composite.'),
 '09': dict(model='kling4', gen_s=9, loc='BEACH', refs=['hero_back', 'hero_profile', 'beach_night', 'ocean_n2', 'aerial_shore'],
   keys=[('first', 'Top-down aerial 60 m above the sea at night: only water edge to edge and a tiny figure standing on the line of white foam'),
         ('middle', 'Top-down aerial 12 m above: the man at the foam line seen from directly above, his long shadow from the moon'),
         ('last', 'Medium close-up in profile at head height: the man\'s breath vapour drifting into the sea mist, moonlit rim on his profile')],
   motion=('Continuous vertical descent from high above the sea down to the man, ending at head height in profile; his '
           'breath turns to vapour and merges with the drifting sea mist.'),
   note='Complex move. Fallback: two cuts at 59.35 s (aerial descent | profile with breath).'),
 '10': dict(model='kling4', gen_s=8, loc='BEACH', refs=['hero_walk', 'hero_profile', 'beach_night', 'ocean_n2'],
   keys=[('first', 'Wide tracking shot parallel to the waterline at night, the man walking along the edge of the surf, sea on the right')],
   motion=('Camera tracks alongside at walking pace. @hero walks along the waterline; a thin wave runs up behind him and '
           'erases his footprints. Natural gait, coat swinging, wet sand shining.'),
   note=''),
 '11': dict(model='kling4', gen_s=12, loc='BEACH', refs=['hero_profile', 'hero_back', 'hero_hands', 'beach_night', 'ocean_n2'],
   keys=[('first', 'Medium shot in profile, 50 mm: the man standing at the waterline turning toward the sea'),
         ('last', 'Low medium close-up: he has crouched at the edge of the swash, right hand reaching toward the water surface')],
   motion=('The camera follows and lowers with him. @hero turns to face the sea, steps into the thin swash and slowly '
           'crouches, reaching his bare right hand toward the water. Coat folds bunch naturally at the knees, hem touches '
           'the wet sand. Unhurried, reverent.'),
   note=''),
 '12': dict(model='kling3pro', gen_s=5, loc='BEACH', refs=['hero_hands', 'ocean_n2'],
   keys=[('first', 'Extreme close-up from above: a man\'s fingertips about to touch the moonlit water surface, wet sand under a thin layer of water')],
   motion=('The fingertips touch the water; clean concentric ripples spread outward and, beneath the surface around the hand, '
           'a soft faint cold glow of natural bioluminescence wakes and fades. Slight slow motion.'),
   note='The "answer" of the Ocean — keep it dim and natural.'),
 '13': dict(model='kling4', gen_s=7, loc='BEACH', refs=['hero_back', 'hero_hands', 'swash_foam', 'ocean_n2'],
   keys=[('first', 'Wide shot from behind: the man crouched at the waterline with his hand in the water, a larger sheet of surf approaching')],
   motion=('Slow pull-back. A larger run-up of surf washes over @hero\'s hand and boots; he does not pull back. Faint natural '
           'bioluminescent ripples travel outward from his hand along the moon path.'),
   note=''),
 '14': dict(model='kling3pro', gen_s=6, loc='OPEN', refs=['ocean_n2', 'aerial_shore'],
   keys=[('first', 'Aerial view rising over the moonlit sea: faint concentric rings of pale light spreading through the water from a tiny figure at the shore')],
   motion=('Camera rises and drifts away into the sky. Wide concentric rings of very faint natural light spread across the '
           'moonlit sea and pulse slowly like breathing.'),
   note='Female answer 92.92 s — the rings are the voice.'),
 '15': dict(model='kling4', gen_s=6, loc='BASALT', refs=['hero_walk', 'hero_back', 'basalt_night'],
   keys=[('first', 'Wide shot on a black basalt shore at night in wind, the man walking heavily between wet boulders, head down, hands in pockets')],
   motion=('Camera follows with heavy, steady movement. @hero walks against the wind between black boulders, coat flapping, '
           'spray drifting, cloud shadows racing over the rocks.'),
   note=''),
 '16': dict(model='kling4', gen_s=7, loc='BASALT', refs=['hero_profile', 'hero_back', 'basalt_night'],
   keys=[('first', 'Medium close-up from the side: the man leaning with one hand against a wet basalt rock, wind in his coat; in the '
                   'foreground cracks in the wet stone with seawater seeping; behind him a wave about to burst on the rocks')],
   motion=('Static camera. Wind whips the coat; behind him a wave bursts against the rocks in slow motion, white spray '
           'hangs in the air; seawater trickles through the cracks in the foreground. He breathes heavily, eyes closed.'),
   note=''),
 '17': dict(model='kling4', gen_s=10, loc='BASALT', refs=['hero_back', 'basalt_night', 'ocean_n4'],
   keys=[('first', 'Top-down view: the man standing motionless among black boulders as the tide rushes around them'),
         ('last', 'Medium shot from behind and slightly below: he lifts his head; above the sea the clouds part and a moon path lays on the water')],
   motion=('Slow rotating top-down view, then a crane down to him. The tide rushes around the boulders; as he lifts his head '
           'the clouds part over the sea and a path of moonlight lays down on the water toward him.'),
   note='Clouds must part on «веди меня» (115.95 s).'),
 '18': dict(model='kling3pro', gen_s=7, loc='BASALT', refs=['ocean_n4', 'aerial_shore'],
   keys=[('first', 'Wide shot of the man as a small figure on a rock promontory facing the vast breathing sea at night')],
   motion=('Camera pulls back and rises, revealing the vast sea; long swells rise and fall slowly like breathing.'),
   note=''),
 '19': dict(model='kling3pro', gen_s=10, loc='BEACH', refs=['ocean_n4', 'hero_back'],
   keys=[('first', 'Low shot from the water surface looking back to the shore: the man standing small at the waterline, moon path between camera and him')],
   motion=('The camera floats on the sea surface, rising and falling with the swell, looking at the man on the shore; '
           'water occasionally laps across the lower frame.'),
   note='Ends with a 1.5 s dissolve to shot 20 — generate with handles.'),
 '20': dict(model='kling4', gen_s=7, loc='BEACH', refs=['hero_walk', 'hero_back', 'beach_predawn'],
   keys=[('first', 'Wide shot at pre-dawn blue hour: the man walking back on the sandy shore through milky sea fog')],
   motion=('Slow lateral dolly. @hero walks along the shore through dense milky fog; the light is soft and blue; the moon '
           'sinks pale in the haze.'),
   note='Act II. Dissolve in from shot 19.'),
 '21': dict(model='kling3pro', gen_s=7, loc='SHALLOWS', refs=['ocean_d0'],
   keys=[('first', 'Macro over calm water at dawn: fine drizzle starting to fall, first rings on the silky surface reflecting pale light')],
   motion=('Static macro with slight drift. Fine drizzle falls; each drop makes a ring; the rings overlap and merge into one '
           'shared pattern; first pale dawn light in the drops.'),
   note=''),
 '22': dict(model='kling4', gen_s=7, loc='SHALLOWS', refs=['hero_back', 'hero_walk', 'shallows_fog'],
   keys=[('first', 'Medium shot from behind: the man wading into calm water up to his ankles, dense milky fog, horizon invisible')],
   motion=('Slow follow from behind. @hero wades deeper, ankle- then calf-deep; trousers darken with water; the fog erases '
           'the horizon until sea and sky are one milky space.'),
   note='Costume continuity: wet trousers from here on.'),
 '23': dict(model='kling3pro', gen_s=6, loc='SHALLOWS', refs=['shallows_fog', 'hero_back'],
   keys=[('first', 'Extreme wide shot: a tiny figure standing in a milky continuum where sea and sky merge; perfectly calm mirror water')],
   motion=('Camera slowly descends toward the mirror surface until the figure and its reflection form one symmetrical shape.'),
   note=''),
 '24': dict(model='kling3pro', gen_s=4, loc='POOLS', refs=['pools_blue', 'hero_hands'],
   keys=[('first', 'Extreme close-up at blue hour: a single drop hanging from a man\'s fingertip above perfectly still mirror water')],
   motion=('Extreme slow motion: the drop falls and touches the mirror; a single clean ring spreads outward in silence.'),
   note='Impact must land at 163.4 s.'),
 '25': dict(model='kling3pro', gen_s=6, loc='POOLS', refs=['pools_blue', 'hero_back'],
   keys=[('first', 'Top-down: a still rock pool at blue hour reflecting a man looking down into it — we see only his dark, slightly blurred reflection')],
   motion=('Static top-down. The water barely trembles; the reflection breathes subtly.'),
   note=''),
 '26': dict(model='kling4', gen_s=6, loc='POOLS', refs=['hero_hands', 'pools_blue'],
   keys=[('first', 'Close-up: a man\'s cupped hands lifting water from a rock pool at blue hour')],
   motion=('He lifts water in his cupped hands; it trickles through his fingers back into the pool in thin silver threads.'),
   note='Hands close-up — needs the hands reference.'),
 '27': dict(model='kling4', gen_s=7, loc='POOLS', refs=['pools_blue', 'hero_back', 'hero_profile'],
   keys=[('first', 'Tight medium shot past a row of small tide pools between rock walls, each pool showing the man\'s reflection from a different angle')],
   motion=('Slow lateral move along the row of pools; the reflections shift with the parallax; rock walls hem in the frame.'),
   note=''),
 '28': dict(model='kling3pro', gen_s=7, loc='POOLS', refs=['pools_blue'],
   keys=[('first', 'Close top-down: his reflection in a still pool, pale sky behind it'),
         ('last', 'Same pool, calm again: only the reflected pale dawn sky, no reflection of the man')],
   motion=('A ripple runs across the pool and breaks the reflection into fragments; the fragments dissolve into the '
           'reflected sky; when the water calms, his reflection is gone — only sky and the first light remain.'),
   note='Match-dissolve into shot 29.'),
 '29': dict(model='kling4', gen_s=17, loc='SHALLOWS', refs=['hero_back', 'shallows_pearl', 'ocean_d2'],
   keys=[('first', 'Extreme wide shot of the horizon at pearl dawn: a warm rose band under glowing sea fog, calm sea'),
         ('last', 'Medium shot from behind: the man standing in shallow water, gentle waves embracing his legs, the fog glowing warm')],
   motion=('Static on the horizon, then a slow approach to the man. The fog begins to glow from within; soft gentle waves '
           'touch his legs and retreat like a hand stroking; his shoulders drop as he exhales.'),
   note='Starts with the female consolation at 189.50 s.'),
 '30': dict(model='kling3pro', gen_s=8, loc='SHALLOWS', refs=['shallows_pearl', 'aerial_shore'],
   keys=[('first', 'Aerial above a tiny figure standing in mother-of-pearl shallows at dawn')],
   motion=('Very slow rise; a soft warm ring of light gathers in the water around the figure, natural and subtle.'),
   note=''),
 '31': dict(model='kling4', gen_s=7, loc='SHALLOWS', refs=['hero_profile', 'hero_kneel', 'shallows_pearl'],
   keys=[('first', 'Wide profile: the man standing in calm shallows at pearl dawn'),
         ('last', 'Same framing: he is kneeling in the water, the water at his hips, coat floating slightly')],
   motion=('Static. @hero slowly lowers himself to his knees in the shallow water; the coat spreads and floats around him; the light warms.'),
   note='Costume: coat wet to the waist from here.'),
 '32': dict(model='kling4', gen_s=6, loc='SHALLOWS', refs=['hero_profile', 'hero_kneel', 'hero_face34'],
   keys=[('first', 'Medium close-up in backlit profile: the man kneeling in water, head bowed, eyes closed, pearl light behind')],
   motion=('Static. He kneels with bowed head, breathing calmly; drops fall from his hair; tiny ripples around him.'),
   note='Only face shot of the film: profile, backlit, never frontal.'),
 '33': dict(model='kling4', gen_s=14, loc='SHALLOWS', refs=['hero_kneel', 'shallows_pearl', 'aerial_shore'],
   keys=[('first', 'Top-down: the man kneeling in clear shallows; loops of his old footprints visible in the sand bottom around him')],
   motion=('Very slow rise. Three gentle waves pass over the shallows one after another and smooth the footprint loops away '
           'until the sand is clean.'),
   note='Three waves on «боли… страха… грусти» (232.8, 233.4, 235.1 s).'),
 '34': dict(model='kling4', gen_s=7, loc='SHALLOWS', refs=['hero_back', 'hero_kneel', 'ocean_d3'],
   keys=[('first', 'Wide shot from behind: the man kneeling in the shallows facing a fog bank'),
         ('last', 'Same, closer: his head raised, the upper rim of the sun breaking through the fog on the horizon')],
   motion=('Slow push-in. He raises his head toward the horizon; the upper rim of the sun breaks through the fog and the '
           'first direct ray touches the water.'),
   note='Sun rim on «дан» (241.6–243.7 s).'),
 '35': dict(model='kling3pro', gen_s=7, loc='OPEN', refs=['ocean_d4'],
   keys=[('first', 'Extreme wide aerial over the sea at sunrise, mist in layers, the sea starting to glitter')],
   motion=('Camera rises over the water; the sun climbs, the sea ignites with natural glints, mist lifts in layers.'),
   note='Gen-4.5 A/B candidate (water physics).'),
 '36': dict(model='kling3pro', gen_s=7, loc='OPEN', refs=['ocean_d4'],
   keys=[('first', 'Low over the water at sunrise flying along the sun path, wave crests backlit translucent gold and turquoise')],
   motion=('Fast low flight along the sun path toward the horizon; backlit crests glow translucent gold and turquoise.'),
   note=''),
 '37': dict(model='kling4', gen_s=7, loc='SHALLOWS', refs=['hero_kneel', 'hero_back', 'ocean_d4'],
   keys=[('first', 'Wide shot: the man kneeling in the shallows at sunrise, a gentle wave approaching')],
   motion=('@hero stands up from his knees; water streams from his coat; a gentle wave breaks against him and he stays standing, steady.'),
   note=''),
 '38': dict(model='kling4', gen_s=7, loc='SHALLOWS', refs=['hero_back', 'hero_walk', 'ocean_d4'],
   keys=[('first', 'Medium shot from behind at sunrise: the man standing knee-deep facing the sun path')],
   motion=('Slow follow. He takes the first step deeper toward the sun; warm light wraps around him.'),
   note=''),
 '39': dict(model='kling4', gen_s=14, loc='OPEN', refs=['hero_back', 'ocean_d5', 'aerial_shore'],
   keys=[('first', 'Extreme wide aerial: vast golden sea, a tiny figure walking into the sun path, mist streaming')],
   motion=('Long smooth aerial orbit. The tiny figure walks into the sun path; streams of mist; slow-motion backlit spray; soft light shafts in the haze.'),
   note=''),
 '40': dict(model='kling4', gen_s=8, loc='OPEN', refs=['hero_back', 'ocean_d5'],
   keys=[('first', 'Wide shot from behind at water level: the man waist-deep in the glittering sun path')],
   motion=('Slow follow at water level. He wades on; the edges of his silhouette are gradually swallowed by the dense sun glints on the water.'),
   note='"Dissolution" = real specular glare, not a VFX effect.'),
 '41': dict(model='kling3pro', gen_s=6, loc='OPEN', refs=['ocean_d5'],
   keys=[('first', 'Telephoto 85 mm toward the horizon: a tiny silhouette barely distinguishable inside the sun glints'),
         ('last', 'Same framing: only the sun path on the water, nobody')],
   motion=('Static telephoto. The tiny silhouette merges with the glittering sun path and is gone; only the light remains.'),
   note='Gone by 296.6 s when the music fades.'),
 '42': dict(model='kling4', gen_s=20, loc='OPEN', refs=['ocean_d5'],
   keys=[('first', 'Locked-off wide shot of the horizon at sunrise, calm breathing sea, thin mist, sun low')],
   motion=('One continuous locked-off take with an almost imperceptible push-in over 20 seconds. The water breathes gently, '
           'the sun climbs slowly, the mist thins. Nothing else happens.'),
   note='Epilogue 298.97–316.08 s: no cuts, holds through the 1.63 s pause.'),
 '43': dict(model='kling3pro', gen_s=10, loc='BEACH', refs=['beach_morning'],
   keys=[('first', 'Wide shot of the empty beach in soft morning light: a line of footprints leading into the water')],
   motion=('Slow lateral dolly. A wave slides up the sand and washes the footprints away.'),
   note='Echo of shot 02, now warm.'),
 '44': dict(model='kling3pro', gen_s=13, loc='OPEN', refs=['ocean_d5'],
   keys=[('first', 'Close-up of a calm golden water surface')],
   motion=('Static. A single ring spreads slowly from the centre of the frame across the golden water.'),
   note='Fade to warm light 334.6–337.5 s in the edit.'),
}

REF_IDS = {
 'hero_back': 'Hero — full body from behind, standing, hands in pockets (night, neutral backlight)',
 'hero_walk': 'Hero — walking, 3/4 back, mid-stride',
 'hero_profile': 'Hero — profile, standing, rim light',
 'hero_hair_back': 'Hero — back of head, collar and hair close-up',
 'hero_hands': 'Hero — hands (bare, weathered, no rings)',
 'hero_kneel': 'Hero — kneeling in shallow water, profile',
 'hero_face34': 'Hero — face 3/4, neutral, for internal consistency only (never shown frontally)',
 'ocean_n1': 'Ocean N1 — night, veiled moon', 'ocean_n2': 'Ocean N2 — night, moon path', 'ocean_n4': 'Ocean N4 — clearing',
 'ocean_d0': 'Ocean D0 — pre-dawn milky', 'ocean_d2': 'Ocean D2 — pearl dawn', 'ocean_d3': 'Ocean D3 — sun rim through fog',
 'ocean_d4': 'Ocean D4 — sunrise glitter', 'ocean_d5': 'Ocean D5 — white-gold sun path',
 'swash_foam': 'Water — swash and foam lace on wet sand (texture reference)',
 'beach_night': 'Location — sandy beach with dunes, night', 'beach_predawn': 'Location — same beach, pre-dawn fog',
 'beach_morning': 'Location — same beach, morning', 'basalt_night': 'Location — basalt shore, night',
 'pools_blue': 'Location — tide pools, blue hour', 'shallows_fog': 'Location — shallows in milky fog',
 'shallows_pearl': 'Location — shallows at pearl dawn', 'aerial_shore': 'Location — aerial of the shoreline',
}

STORY = {s['shot']: s for s in json.load(open(os.path.join(ROOT, 'docs', 'shots.json')))['shots']}


def is_hero(sid):
    return any(r.startswith('hero') for r in SH[sid]['refs'])


def keyframe_prompt(sid, pos, desc):
    st = STORY[sid]
    look = LOOK[st['light'].split('→')[-1] if pos == 'last' else st['light'].split('→')[0]]
    hero = ('@hero is ' + HERO_SHORT + '.') if is_hero(sid) else ''
    p = compose(desc, hero, LOCATIONS[SH[sid]['loc']], look, CAMERA, 'Still frame from a feature film')
    return p


def motion_prompt(sid):
    st = STORY[sid]
    look = LOOK[st['light'].split('→')[-1]]
    # video models take references untagged, so name the hero in words
    mot = SH[sid]['motion'].replace("@hero's", "the man's").replace('@hero', 'the man in the charcoal wool overcoat')
    p = compose(mot, look, REALISM, CAMERA)
    if SH[sid]['model'] != 'kling4' and len(p) > 1000:
        p = compose(mot, look, REALISM)
    if len(p) > 1000 and SH[sid]['model'] != 'kling4':
        p = p[:997] + '...'
    return p


def build(takes_hero=4, takes_nature=3):
    rows = []
    for sid in sorted(SH):
        s, st = SH[sid], STORY[sid]
        takes = takes_hero if is_hero(sid) else takes_nature
        rows.append(dict(shot=sid, title=st['title'], start_s=st['start_s'], end_s=st['end_s'], start_frame=st['start_frame'],
                         end_frame=st['end_frame'], frames=st['frames'], dur_s=st['dur_s'], light=st['light'],
                         model=s['model'], gen_s=s['gen_s'], takes=takes, refs=s['refs'], location=s['loc'],
                         keyframes=[dict(position=p, description=d, prompt=keyframe_prompt(sid, p, d)) for p, d in s['keys']],
                         motion_prompt=motion_prompt(sid), avoid=AVOID, note=s['note'],
                         video_cost=round(s['gen_s'] * takes * PRICE[s['model']], 2),
                         video_cost_list=round(s['gen_s'] * takes * (PRICE['kling4_list'] if s['model'] == 'kling4' else PRICE[s['model']]), 2),
                         key_images=len(s['keys']) * 6))
    return rows


def budget(rows):
    vid = sum(r['video_cost'] for r in rows)
    vid_list = sum(r['video_cost_list'] for r in rows)
    imgs = sum(r['key_images'] for r in rows)
    refs = len(REF_IDS) * 8
    img_cost = (imgs + refs) * IMG_PRICE + 30 * IMG_PRICE_HQ
    gen_sec = sum(r['gen_s'] * r['takes'] for r in rows)
    return dict(video_usd=round(vid, 2), video_usd_list=round(vid_list, 2), images=imgs + refs + 30, images_usd=round(img_cost, 2),
                generated_seconds=gen_sec, net_seconds=round(sum(r['dur_s'] for r in rows), 2))


if __name__ == '__main__':
    rows = build()
    B = budget(rows)
    test = [r for r in rows if r['shot'] in ('01', '02', '03', '04')]
    os.makedirs(os.path.join(ROOT, 'docs', 'i2v'), exist_ok=True)
    json.dump(dict(price_usd_per_second=PRICE, image_price_usd=IMG_PRICE, budget=B, shots=rows, references=REF_IDS),
              open(os.path.join(ROOT, 'docs', 'i2v', 'prompts.json'), 'w'), ensure_ascii=False, indent=1)
    M = {'kling4': 'Kling 4.0 (1080p, ключевые кадры + референсы)', 'kling3pro': 'Kling 3.0 Pro (1920×1080, первый/последний кадр)', 'gen45': 'Runway Gen-4.5'}
    out = ['# Промпты по планам (Image-to-Video)\n',
           'Сгенерировано из `src/i2v/shots_i2v.py` и `src/i2v/bible.py`. Тайминг, кадры и свет совпадают с утверждённой раскадровкой (`docs/STORYBOARD.md`). '
           'Промпты на английском: модели понимают его точнее всего. Описания героя, света и камеры подставляются **дословно одинаковыми** во все планы, это часть стратегии непрерывности.\n',
           f"**Общие запреты (в каждый запрос, где модель их принимает):** {AVOID}\n",
           f"**Итог:** {len(rows)} планов, {B['net_seconds']} с чистого экранного времени; к генерации {B['generated_seconds']} с с учётом дублей.\n"]
    for r in rows:
        out.append(f"## {r['shot']}. {r['title']}")
        out.append(f"`{STORY[r['shot']]['start_tc']} – {STORY[r['shot']]['end_tc']}` · кадры {r['start_frame']}–{r['end_frame']} · {r['dur_s']:.2f} с · свет {r['light']} · локация {r['location']}\n")
        out.append(f"- **Модель:** {M[r['model']]}; генерация {r['gen_s']} с × {r['takes']} дубля ≈ **${r['video_cost']:.2f}**")
        out.append(f"- **Референсы:** {', '.join('`' + x + '`' for x in r['refs'])}")
        for k in r['keyframes']:
            out.append(f"- **Ключевой кадр ({k['position']}):** {k['prompt']}")
        out.append(f"- **Движение (I2V):** {r['motion_prompt']}")
        if r['note']:
            out.append(f"- **Примечание:** {r['note']}")
        out.append('')
    open(os.path.join(ROOT, 'docs', 'i2v', 'SHOT_PROMPTS.md'), 'w').write('\n'.join(out) + '\n')
    print(json.dumps(B, ensure_ascii=False))
    tb = sum(r['video_cost'] for r in test)
    print('test video usd', round(tb, 2), 'test keyframe imgs', sum(r['key_images'] for r in test))
    for r in rows:
        if r['model'] != 'kling4' and len(r['motion_prompt']) > 1000: print('LONG', r['shot'])
    for r in rows:
        for k in r['keyframes']:
            if len(k['prompt']) > 1000: print('KEY LONG', r['shot'], len(k['prompt']))
