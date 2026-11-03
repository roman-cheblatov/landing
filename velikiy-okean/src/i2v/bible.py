"""Continuity bible: fixed English descriptors reused verbatim in every keyframe / video prompt.
Changing a descriptor here changes it everywhere — that is the point (character & world continuity)."""

HERO = ("a lean man in his early forties, about 1.82 m tall, short dark-brown hair slightly ruffled at the nape, "
        "light stubble, wearing a knee-length heavy charcoal-grey wool overcoat with a raised stand-up collar, "
        "slightly worn felted wool with a single back vent, dark straight trousers, dark matte leather ankle boots; "
        "no hat, no scarf, no bag, no logos, no jewellery")
HERO_SHORT = "the man in the knee-length charcoal wool overcoat with the raised collar"

CAMERA = ("photographed on an ARRI Alexa 35 with Cooke S4/i spherical primes, natural exposure, high dynamic range, "
          "fine 35 mm film grain, gentle halation only on the brightest speculars, 180-degree shutter motion blur, 24 fps")

REALISM = ("real location photography, natural ocean physics, real water with true foam and spray, realistic skin and "
           "fabric texture, natural human movement with weight and balance")

AVOID = ("CGI, 3D render, video-game or Unreal look, plastic or waxy skin, artificial smooth water, fake foam, "
         "oversaturated colour, neon, excessive glow or bloom, lens-flare streaks, magic particles, sparkles, stars "
         "in daylight, planets, fantasy creatures, text, watermark, extra limbs, morphing faces, flicker, frozen still "
         "image with zoom")

LOOK = {
    'N1': ("night, the full moon hidden behind a bank of thin stratus, only its soft halo glowing through; cold blue-grey "
           "sea mist hanging low; lead-coloured sea with long slow swells; horizon dissolving into haze; deep blue shadows"),
    'N2': ("night, full moon low over the sea about 13 degrees high, cold silver moonlight, a long glittering moon path on "
           "the water, backlit mist, silver rim light on wet surfaces, deep blue-black shadows"),
    'N3': ("night, wind, ragged clouds racing across the moon so the light flickers with cloud shadows, black wet basalt, "
           "steel-blue palette, spray and wind-driven mist, no warmth"),
    'N4': ("night, a clearing opens in the clouds above the sea, a path of moonlight lays down on the water, deep blue "
           "and silver"),
    'D0': ("pre-dawn blue hour, the moon low and pale, the eastern sky turning milky steel-blue, dense milky sea fog that "
           "erases the horizon, soft shadowless light"),
    'D1': ("blue hour, absolutely still water in rock pools acting as mirrors, soft shadowless pastel-blue light, "
           "pearl-grey sky reflected"),
    'D2': ("pearl dawn: the sea fog glowing softly from within with warm mother-of-pearl light, a faint rose band along "
           "the horizon, calm silky water, very soft contrast"),
    'D3': ("pearl light turning to the first direct ray: the upper rim of the sun just appearing through thinning fog, "
           "soft warm gold touching the water"),
    'D4': ("sunrise: low warm sun, soft gold light, the ocean glittering with countless natural sun glints, backlit "
           "wave crests translucent gold and turquoise, layers of mist lifting"),
    'D5': ("sun above a thin veil of mist, white-gold light, long glittering sun path, gentle god rays in the haze, "
           "restrained natural saturation"),
}

LOCATIONS = {
    'BEACH': ("a wide, empty Atlantic-style sandy beach with low dunes and marram grass behind, dark fine sand, a broad "
              "band of mirror-wet sand at the waterline, gentle spilling surf"),
    'BASALT': ("a rugged stretch of the same coast with black wet basalt boulders and ledges, cracks filled with seawater, "
               "waves bursting white against the rocks"),
    'POOLS': ("a flat rock platform at low tide with many small still tide pools reflecting the sky, rock walls on both "
              "sides"),
    'SHALLOWS': ("vast calm shallows over smooth sand, the water ankle- to waist-deep, perfectly calm silky surface"),
    'OPEN': ("open sea far from shore, long calm swells, no land visible"),
}


def compose(*parts):
    return ' '.join((p.strip()[0].upper() + p.strip()[1:]).rstrip('.') + '.' for p in parts if p and p.strip())
