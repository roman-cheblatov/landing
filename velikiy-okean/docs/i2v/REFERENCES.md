# Единые референсы: герой, Океан, локации

Сгенерировано из `src/i2v/refpack.py`. Порядок работы:

1. **hero_master** — 8 кандидатов только по тексту. Вы выбираете одного: это «кастинг» героя.
2. Остальные `hero_*` генерируются **с hero_master как референсом** (`@hero`): лицо, телосложение и пальто наследуются, а не придумываются заново.
3. Океан и локации: по 6 кандидатов. Для `ocean_n1`, `ocean_n2` и `beach_night` композиционным референсом (`@layout`) служат кадры утверждённого теста (`refs/layout/`).
4. Утверждённые изображения кладутся в `work/i2v/approved/refs/<id>.jpg`. Дальше они автоматически идут во все ключевые кадры (gen4_image, до 3 референсов) и в видео Kling 4.0 (`references`, до 10).

## Описание героя (дословно во всех промптах)

> a lean man in his early forties, about 1.82 m tall, short dark-brown hair slightly ruffled at the nape, light stubble, wearing a knee-length heavy charcoal-grey wool overcoat with a raised stand-up collar, slightly worn felted wool with a single back vent, dark straight trousers, dark matte leather ankle boots; no hat, no scarf, no bag, no logos, no jewellery

| ID | Назначение | Зависит от | Используется в планах |
|---|---|---|---|
| `hero_master` | мастер-образ героя (кастинг) | — | все (через hero_*) |
| `hero_back` | Hero — full body from behind, standing, hands in pockets (night, neutral backlight) | hero_master | 02, 03, 04, 05, 06, 09, 11, 13, 15, 16, 17, 19, 20, 22, 23, 25, 27, 29, 34, 37, 38, 39, 40 |
| `hero_walk` | Hero — walking, 3/4 back, mid-stride | hero_master | 02, 10, 15, 20, 22, 38 |
| `hero_profile` | Hero — profile, standing, rim light | hero_master | 02, 06, 09, 10, 11, 16, 27, 31, 32 |
| `hero_hair_back` | Hero — back of head, collar and hair close-up | hero_master | 03 |
| `hero_hands` | Hero — hands (bare, weathered, no rings) | hero_master | 06, 11, 12, 13, 24, 26 |
| `hero_kneel` | Hero — kneeling in shallow water, profile | hero_master | 31, 32, 33, 34, 37 |
| `hero_face34` | Hero — face 3/4, neutral, for internal consistency only (never shown frontally) | hero_master | 32 |
| `ocean_n1` | Ocean N1 — night, veiled moon | layout | 01, 02 |
| `ocean_n2` | Ocean N2 — night, moon path | layout | 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14 |
| `ocean_n4` | Ocean N4 — clearing | — | 17, 18, 19 |
| `ocean_d0` | Ocean D0 — pre-dawn milky | — | 21 |
| `ocean_d2` | Ocean D2 — pearl dawn | — | 29 |
| `ocean_d3` | Ocean D3 — sun rim through fog | — | 34 |
| `ocean_d4` | Ocean D4 — sunrise glitter | — | 35, 36, 37, 38 |
| `ocean_d5` | Ocean D5 — white-gold sun path | — | 39, 40, 41, 42, 44 |
| `swash_foam` | Water — swash and foam lace on wet sand (texture reference) | — | 04, 05, 13 |
| `beach_night` | Location — sandy beach with dunes, night | layout | 02, 03, 04, 09, 10, 11 |
| `beach_predawn` | Location — same beach, pre-dawn fog | beach_night | 20 |
| `beach_morning` | Location — same beach, morning | beach_night | 43 |
| `basalt_night` | Location — basalt shore, night | — | 15, 16, 17 |
| `pools_blue` | Location — tide pools, blue hour | — | 24, 25, 26, 27, 28 |
| `shallows_fog` | Location — shallows in milky fog | — | 22, 23 |
| `shallows_pearl` | Location — shallows at pearl dawn | — | 29, 30, 31, 33 |
| `aerial_shore` | Location — aerial of the shoreline | — | 09, 14, 18, 30, 33, 39 |

## Промпты референсов

**hero_master**

```
Full-length photograph of a lean man in his early forties, about 1.82 m tall, short dark-brown hair slightly ruffled at the nape, light stubble, wearing a knee-length heavy charcoal-grey wool overcoat with a raised stand-up collar, slightly worn felted wool with a single back vent, dark straight trousers, dark matte leather ankle boots; no hat, no scarf, no bag, no logos, no jewellery, standing three-quarter from behind on an empty beach, looking at the sea, hands in coat pockets. Soft overcast dawn light, neutral grey-blue tones, sharp focus, true-to-life textures. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps. Character reference photo for a feature film, no stylisation.
```

**hero_back**

```
@hero seen exactly from behind, full body, standing still at the waterline at night, hands in coat pockets, moonlight from the front creating a silver rim on collar and shoulders. A wide, empty Atlantic-style sandy beach with low dunes and marram grass behind, dark fine sand, a broad band of mirror-wet sand at the waterline, gentle spilling surf. Night, full moon low over the sea about 13 degrees high, cold silver moonlight, a long glittering moon path on the water, backlit mist, silver rim light on wet surfaces, deep blue-black shadows. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**hero_walk**

```
@hero walking slowly on wet sand, three-quarter back view, mid-stride, coat hem swinging, hands in pockets, natural weight on the front foot. A wide, empty Atlantic-style sandy beach with low dunes and marram grass behind, dark fine sand, a broad band of mirror-wet sand at the waterline, gentle spilling surf. Night, the full moon hidden behind a bank of thin stratus, only its soft halo glowing through; cold blue-grey sea mist hanging low; lead-coloured sea with long slow swells; horizon dissolving into haze; deep blue shadows. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**hero_profile**

```
@hero in strict profile facing right toward the sea, medium shot, collar up, face mostly in shadow with a thin moonlit rim along forehead, nose and lips. Night, full moon low over the sea about 13 degrees high, cold silver moonlight, a long glittering moon path on the water, backlit mist, silver rim light on wet surfaces, deep blue-black shadows. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**hero_hair_back**

```
Close-up of the back of the head and the raised wool collar of @hero, short dark-brown hair ruffled by wind, fine wool texture, moonlit rim. Night, full moon low over the sea about 13 degrees high, cold silver moonlight, a long glittering moon path on the water, backlit mist, silver rim light on wet surfaces, deep blue-black shadows. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**hero_hands**

```
Close-up of the bare hands of @hero, weathered, no rings, coat sleeve cuffs visible, one hand near the surface of shallow sea water. Soft overcast dawn light, neutral grey-blue tones, sharp focus, true-to-life textures. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**hero_kneel**

```
@hero kneeling in calm shallow sea water up to his hips, profile, head slightly bowed, the wet coat floating around him. Vast calm shallows over smooth sand, the water ankle- to waist-deep, perfectly calm silky surface. Pearl dawn: the sea fog glowing softly from within with warm mother-of-pearl light, a faint rose band along the horizon, calm silky water, very soft contrast. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**hero_face34**

```
Three-quarter portrait of @hero, calm, serious, tired eyes, light stubble, natural skin pores and fine lines, no retouching. Soft overcast dawn light, neutral grey-blue tones, sharp focus, true-to-life textures. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps. For internal continuity only.
```

**ocean_n1**

```
Open sea at night seen from 2.5 m above the water. Night, the full moon hidden behind a bank of thin stratus, only its soft halo glowing through; cold blue-grey sea mist hanging low; lead-coloured sea with long slow swells; horizon dissolving into haze; deep blue shadows. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**ocean_n2**

```
The sea from the beach at night with a long moon path. Night, full moon low over the sea about 13 degrees high, cold silver moonlight, a long glittering moon path on the water, backlit mist, silver rim light on wet surfaces, deep blue-black shadows. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**ocean_n4**

```
The sea from a rocky promontory at night as clouds open. Night, a clearing opens in the clouds above the sea, a path of moonlight lays down on the water, deep blue and silver. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**ocean_d0**

```
Calm sea surface in dense milky fog. Pre-dawn blue hour, the moon low and pale, the eastern sky turning milky steel-blue, dense milky sea fog that erases the horizon, soft shadowless light. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**ocean_d2**

```
Horizon over a calm sea. Pearl dawn: the sea fog glowing softly from within with warm mother-of-pearl light, a faint rose band along the horizon, calm silky water, very soft contrast. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**ocean_d3**

```
Fog bank over a calm sea with the sun rim breaking through. Pearl light turning to the first direct ray: the upper rim of the sun just appearing through thinning fog, soft warm gold touching the water. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**ocean_d4**

```
Open sea at sunrise from low altitude. Sunrise: low warm sun, soft gold light, the ocean glittering with countless natural sun glints, backlit wave crests translucent gold and turquoise, layers of mist lifting. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**ocean_d5**

```
Horizon with a long sun path on the water. Sun above a thin veil of mist, white-gold light, long glittering sun path, gentle god rays in the haze, restrained natural saturation. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**swash_foam**

```
Close detail of a thin sheet of surf running up mirror-wet sand, real foam lace, bubbles and sand grains, moonlight. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**beach_night**

```
A wide, empty Atlantic-style sandy beach with low dunes and marram grass behind, dark fine sand, a broad band of mirror-wet sand at the waterline, gentle spilling surf. Night, the full moon hidden behind a bank of thin stratus, only its soft halo glowing through; cold blue-grey sea mist hanging low; lead-coloured sea with long slow swells; horizon dissolving into haze; deep blue shadows. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**beach_predawn**

```
The same beach as @beach. Pre-dawn blue hour, the moon low and pale, the eastern sky turning milky steel-blue, dense milky sea fog that erases the horizon, soft shadowless light. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**beach_morning**

```
The same beach as @beach, morning, a line of footprints leading into the water. Sun above a thin veil of mist, white-gold light, long glittering sun path, gentle god rays in the haze, restrained natural saturation. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**basalt_night**

```
A rugged stretch of the same coast with black wet basalt boulders and ledges, cracks filled with seawater, waves bursting white against the rocks. Night, wind, ragged clouds racing across the moon so the light flickers with cloud shadows, black wet basalt, steel-blue palette, spray and wind-driven mist, no warmth. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**pools_blue**

```
A flat rock platform at low tide with many small still tide pools reflecting the sky, rock walls on both sides. Blue hour, absolutely still water in rock pools acting as mirrors, soft shadowless pastel-blue light, pearl-grey sky reflected. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**shallows_fog**

```
Vast calm shallows over smooth sand, the water ankle- to waist-deep, perfectly calm silky surface. Pre-dawn blue hour, the moon low and pale, the eastern sky turning milky steel-blue, dense milky sea fog that erases the horizon, soft shadowless light. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**shallows_pearl**

```
Vast calm shallows over smooth sand, the water ankle- to waist-deep, perfectly calm silky surface. Pearl dawn: the sea fog glowing softly from within with warm mother-of-pearl light, a faint rose band along the horizon, calm silky water, very soft contrast. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

**aerial_shore**

```
Aerial view of the long sandy shoreline with lines of white surf, misty. Night, full moon low over the sea about 13 degrees high, cold silver moonlight, a long glittering moon path on the water, backlit mist, silver rim light on wet surfaces, deep blue-black shadows. Photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps.
```

