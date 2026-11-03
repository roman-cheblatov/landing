#version 430
// world.frag — raymarched world: sky, ocean with surf & swash, beach, volumetric mist, the hero.
// Output: HDR radiance (rgb) + linear view depth in metres (a).
#include "common.glsl"

in vec2 vUV;
layout(location = 0) out vec4 outColor;

uniform vec2 uRes;
uniform float uTime;
uniform int uFrame;
uniform vec3 uCamPos;
uniform mat3 uCamRot;      // columns: right, up, forward
uniform float uFocal;      // mm on a 36 mm wide gate
uniform vec2 uJitter;
uniform vec4 uCrop;        // xy offset, zw scale (for tiled/preview renders); (0,0,1,1) = full frame

// ---- sky / light ----
uniform vec3 uMoonDir;
uniform vec3 uMoonCol;     // moonlight irradiance colour (key light)
uniform float uMoonDisk;   // visible disk radiance multiplier
uniform vec3 uSunDir;
uniform vec3 uSunCol;
uniform float uSunDisk;
uniform vec3 uZenith;
uniform vec3 uHorizon;
uniform vec3 uAmbient;
uniform float uStars;
uniform float uCloudCover;
uniform float uCloudDens;
uniform vec2 uCloudOfs;
uniform float uMoonClear;  // radius (radians) of a clearing in the clouds around the moon (0 = none)
uniform vec3 uCloudLit;    // colour of cloud edges lit by moon/sun
uniform float uMoonVeil;   // 0..1 extra cloud veiling the moon (animated to 'part the clouds')

// ---- mist ----
uniform float uFogDens;
uniform float uFogH;
uniform vec3 uFogCol;
uniform float uMist;
uniform vec3 uWindVel;
uniform float uFogG;
uniform float uFogFar;     // extra uniform haze for horizon dissolve
uniform float uGroundMist; // dense low-lying mist layer (wisps over sand and water)

// ---- ocean ----
uniform float uWaveAmp;
uniform float uSwellAng;
uniform float uSwashT;     // run-up cycle period (s)
uniform float uSwashPhase;
uniform float uSwashReach;  // inland reach multiplier of the run-up
uniform float uFoamAmt;
uniform vec4 uRip[4];
uniform vec4 uGlow;
uniform vec3 uGlowCol;
uniform vec3 uDeepCol;     // water body colour

// ---- terrain ----
uniform float uRocky;
uniform float uBeachSlope;

// ---- hero ----
uniform int uHero;
uniform vec3 uJ[20];
uniform vec3 uBodyFwd;
uniform vec3 uHeadFwd;
uniform float uCoatWind;
uniform float uHemY;
uniform vec4 uHeroBound;   // centre, radius
uniform int uStudio;       // 1 = character turnaround (neutral backdrop, no world)

const float G = 9.81;
float gCamDist = 0.0;      // distance from camera of current shading point (for LOD)

// =====================================================================
// SKY
// =====================================================================
float cloudDensity(vec3 rd, out vec2 cuv) {
    float h = max(rd.y, 0.0) + 0.035;
    cuv = rd.xz / h * 0.055 + uCloudOfs;
    vec4 a = n2v(cuv * 0.35);
    vec4 b = n2v(cuv * 1.3 + vec2(0.31, 0.17));
    float f = a.b * 0.62 + a.r * 0.25 + b.r * 0.13;
    float cov = mix(-0.6, 0.6, uCloudCover);
    float d = smoothstep(-cov - 0.05, -cov + 0.35, f);
    // clearing around the moon
    if (uMoonClear > 0.0) {
        float ang = acos(clamp(dot(rd, uMoonDir), -1.0, 1.0));
        d *= smoothstep(uMoonClear * 0.55, uMoonClear * 1.25, ang + 0.04 * a.g);
    }
    if (uMoonVeil > 0.0) {
        float ang = acos(clamp(dot(rd, uMoonDir), -1.0, 1.0));
        float veil = 1.0 - smoothstep(0.03, 0.16, ang + 0.05 * a.r + 0.03 * b.g);
        d = max(d, uMoonVeil * veil * (0.85 + 0.15 * a.b));
    }
    return d * smoothstep(-0.02, 0.06, rd.y);
}

float gMoonVis = 1.0;   // set once per pixel in main()
vec3 gMoon = vec3(0.0); // effective moonlight after the cloud veil
float moonVisibility() {
    vec2 cuv;
    float cd = cloudDensity(uMoonDir, cuv) * uCloudDens;
    return exp(-cd * 5.0);
}

vec3 skyRadiance(vec3 rd, bool withDisk) {
    float y = rd.y;
    float yy = max(y, 0.0);
    vec3 col = mix(uHorizon, uZenith, pow(yy, 0.42));
    // slightly darker below horizon (only reached by reflections)
    col *= (y < 0.0) ? mix(1.0, 0.7, saturate(-y * 6.0)) : 1.0;
    float cm = dot(rd, uMoonDir);
    float ang = acos(clamp(cm, -1.0, 1.0));
    // aureole / corona of the moon in thin high haze
    vec3 halo = uMoonCol * (0.55 * exp(-ang * ang / (2.0 * 0.035 * 0.035)) + 0.16 * exp(-ang / 0.22) + 0.05 * exp(-ang / 0.8));
    float cs = dot(rd, uSunDir);
    float angS = acos(clamp(cs, -1.0, 1.0));
    vec3 sunGlow = uSunCol * (0.9 * exp(-angS / 0.09) + 0.25 * exp(-angS / 0.45)) * smoothstep(-0.25, 0.02, rd.y + 0.1);
    vec3 stars = vec3(0.0);
    if (uStars > 0.0 && y > 0.0) {
        vec3 sd = rd * 420.0;
        ivec3 c = ivec3(floor(sd));
        vec3 h = hash3i(c);
        vec3 f = fract(sd) - 0.5 - (h - 0.5) * 0.6;
        float s = smoothstep(0.08, 0.0, length(f)) * step(0.985, h.x);
        float tw = 0.75 + 0.25 * sin(uTime * (1.0 + h.y * 3.0) + h.z * 30.0);
        stars = vec3(0.8, 0.88, 1.0) * s * tw * uStars * (0.3 + 2.0 * h.y * h.y) * smoothstep(0.0, 0.25, y);
    }
    vec2 cuv;
    float cd = cloudDensity(rd, cuv) * uCloudDens;
    float trans = exp(-cd * 4.0);
    // cloud lighting: forward scattering toward the moon/sun, silver edges where thin
    float edge = cd * (1.0 - cd) * 4.0;
    vec3 cloudCol = uHorizon * 0.42 + uZenith * 0.25
                  + uCloudLit * (edge * 1.5 + 0.14) * (0.08 + 2.1 * exp(-ang / 0.16) + 0.4 * exp(-ang / 0.5))
                  + uSunCol * (edge * 1.2 + 0.3) * (0.3 + 1.8 * exp(-angS / 0.3));
    vec3 disk = vec3(0.0);
    if (withDisk) {
        float r = 0.0085;   // slightly larger than true size: telephoto feel
        float m = smoothstep(r, r * 0.88, ang);
        // faint maria
        vec2 mp = vec2(dot(rd, normalize(cross(uMoonDir, vec3(0, 1, 0)))), dot(rd, normalize(cross(normalize(cross(uMoonDir, vec3(0, 1, 0))), uMoonDir)))) / r;
        float maria = 0.82 + 0.18 * smoothstep(0.1, 0.6, n2v(mp * 0.25 + 0.5).b + 0.2);
        disk += uMoonCol * uMoonDisk * m * maria * exp(-cd * 10.0);
        float rs = 0.0105;
        disk += uSunCol * uSunDisk * smoothstep(rs, rs * 0.8, angS);
    }
    vec3 behind = col + stars;
    return behind * trans + disk + mix(cloudCol, col, 0.15) * (1.0 - trans) + (halo * (0.35 + 0.65 * gMoonVis) + sunGlow) * mix(1.0, 0.55, 1.0 - trans);
}

// =====================================================================
// TERRAIN
// =====================================================================
float terrainH(vec2 xz) {
    float z = xz.y;
    float h = -uBeachSlope * z;
    // offshore the bottom drops away; far out it flattens; inland it rises into dunes / bluffs
    h -= 0.11 * max(z - 9.0, 0.0);
    h = max(h, -9.0 + 0.5 * n2v(xz * 0.004).r);
    float inland = smoothstep(-14.0, -48.0, z);
    vec4 dn = n2v(xz * 0.006 + 0.13);
    h += inland * (3.5 + 3.0 * dn.r + 2.0 * dn.b) * smoothstep(-14.0, -70.0, z);
    // soft sand undulation
    h += 0.06 * n2v(xz * 0.03).g * smoothstep(2.0, -6.0, z);
    // rocks (Verse 2): scattered basalt boulders
    if (uRocky > 0.0) {
        vec4 r = n2v(xz * 0.045 + 0.77);
        float rk = smoothstep(0.05, 0.45, r.b + 0.25 * r.r) * (0.9 + 0.5 * n2v(xz * 0.31).r);
        h += uRocky * rk * 1.25 * smoothstep(-35.0, -2.0, z) * smoothstep(30.0, 6.0, z);
    }
    return h;
}

// =====================================================================
// OCEAN — sum of sharpened directional waves with analytic gradient
// =====================================================================
const int NW = 15;
// explicit wave set: wavelength (m), relative amplitude, direction offset (rad), crest sharpness
const vec4 WAVES[NW] = vec4[NW](
    vec4(52.0, 1.00,  0.00, 2.2), vec4(41.0, 0.55,  0.10, 2.0), vec4(33.0, 0.38, -0.12, 1.9),
    vec4(14.0, 0.16,  0.32, 1.6), vec4(10.5, 0.11, -0.25, 1.5), vec4(7.6, 0.075, 0.45, 1.4),
    vec4(5.5, 0.050, -0.38, 1.3), vec4(4.0, 0.034,  0.20, 1.2), vec4(2.9, 0.022, -0.55, 1.1),
    vec4(2.1, 0.014,  0.62, 1.0), vec4(1.5, 0.009, -0.30, 1.0), vec4(1.1, 0.0058, 0.75, 1.0),
    vec4(0.8, 0.0037, -0.70, 1.0), vec4(0.58, 0.0024, 0.40, 1.0), vec4(0.42, 0.0015, -0.9, 1.0));
// returns height; grad = (dh/dx, dh/dz)
float swell(vec2 p, int n, out vec2 grad, out float crest) {
    float h = 0.0;
    grad = vec2(0.0);
    crest = 0.0;
    for (int i = 0; i < NW; i++) {
        if (i >= n) break;
        vec4 W = WAVES[i];
        float a = uSwellAng + W.z;
        vec2 d = vec2(cos(a), sin(a));
        float k = TAU / W.x;
        float w = sqrt(G * k);
        float ph = float(i) * 2.3999 + 0.7;
        float x = dot(d, p) * k - w * uTime + ph;
        float s = sin(x), c = cos(x);
        float u = 0.5 + 0.5 * s;
        float up = pow(u, W.w);
        float amp = uWaveAmp * W.y;
        h += amp * (2.0 * up - 1.0);
        grad += d * amp * 2.0 * W.w * pow(max(u, 1e-4), W.w - 1.0) * 0.5 * c * k;
        if (i < 3) crest = max(crest, up * (i == 0 ? 1.0 : 0.6));
    }
    return h;
}

// swash (run-up on the beach). returns leading edge z for column x
float swashEdge(float x, float t) {
    float ph = t / uSwashT + uSwashPhase + 0.06 * sin(x * 0.09) + 0.05 * n2v(vec2(x * 0.012, 0.3)).r;
    float f = fract(ph);
    // fast up-rush (0..0.32), slow backwash
    float up = (f < 0.32) ? 1.0 - sq(1.0 - f / 0.32) : 1.0 - smoothstep(0.32, 1.0, f);
    float cyc = floor(ph);
    float reach = 0.75 + 0.35 * hash2i(ivec2(int(cyc), 11)) ;   // each wave reaches differently
    return mix(1.4, -4.6 * reach * uSwashReach, up);
}

float waterH(vec2 xz, float tH, int n, out vec2 grad, out float crest, out float sheet) {
    float depth = -tH;                         // mean sea level is 0
    float shoal = smoothstep(-0.2, 3.0, depth) * (1.0 + 0.5 * exp(-max(depth, 0.0) / 1.6));
    float h = swell(xz, n, grad, crest);
    h *= shoal; grad *= shoal;
    sheet = 0.0;
    // swash sheet over the sand
    float ze = swashEdge(xz.x, uTime);
    if (xz.y > ze) {
        float th = 0.003 + 0.032 * smoothstep(ze, ze + 2.8, xz.y);
        float hs = tH + th;
        if (hs > h) { h = hs; grad = vec2(0.0, -uBeachSlope); sheet = 1.0; }
    }
    // ripples (touch rings)
    for (int i = 0; i < 4; i++) {
        if (uRip[i].w <= 0.0) continue;
        float age = uTime - uRip[i].z;
        if (age < 0.0) continue;
        vec2 dv = xz - uRip[i].xy;
        float r = length(dv) + 1e-4;
        float front = age * 0.55;
        float env = exp(-sq((r - front) / (0.18 + 0.12 * age))) * exp(-age * 0.45) * uRip[i].w;
        float ph = (r - front) * 26.0;
        h += 0.012 * env * sin(ph);
        grad += (dv / r) * 0.012 * env * 26.0 * cos(ph);
    }
    return h;
}

float waterHTrace(vec2 xz, float tH) {
    vec2 g; float c, s;
    return waterH(xz, tH, 6, g, c, s);
}

// =====================================================================
// HERO — signed distance figure, joints from CPU forward kinematics
// =====================================================================
float gHeroMat;
float sdHero(vec3 p) {
    float d = 1e5;
    float mat = 0.0;
    vec3 J0 = uJ[0], J2 = uJ[2], J3 = uJ[3];
    // ---- head ----
    vec3 hf = normalize(uHeadFwd);
    vec3 hr = normalize(cross(vec3(0, 1, 0), hf));
    vec3 hu = cross(hf, hr);
    vec3 q = p - J3;
    if (length(q) < 0.25) {
        vec3 hl = vec3(dot(q, hr), dot(q, hu), dot(q, hf));
        float skull = sdEllipsoid(hl - vec3(0.0, 0.01, -0.005), vec3(0.077, 0.1, 0.094));
        float jaw = sdEllipsoid(hl - vec3(0.0, -0.06, 0.028), vec3(0.058, 0.05, 0.066));
        float face = smin(skull, jaw, 0.045);
        float brow = sdEllipsoid(hl - vec3(0.0, 0.028, 0.068), vec3(0.06, 0.02, 0.03));
        face = smin(face, brow, 0.02);
        float nose = sdTaper(hl, vec3(0.0, 0.012, 0.086), vec3(0.0, -0.028, 0.104), 0.009, 0.014);
        face = smin(face, nose, 0.012);
        vec3 ha = vec3(abs(hl.x), hl.y, hl.z);
        float ear = sdEllipsoid(ha - vec3(0.077, -0.005, -0.01), vec3(0.011, 0.029, 0.019));
        face = smin(face, ear, 0.008);
        float hairShell = sdEllipsoid(hl - vec3(0.0, 0.03, -0.014), vec3(0.085, 0.108, 0.103)) - 0.004 * n3(hl * 3.1 + 0.3) - 0.0025 * n3(hl * 9.0 + 1.7);
        float line = (hl.y - 0.058 - 0.85 * (hl.z - 0.07)) * 0.762;
        float side = hl.y + 0.035 - 0.5 * max(0.0, hl.z);          // sideburn line
        float hair = max(hairShell, -max(line, side * 0.8));
        hair = max(hair, -(hl.y + 0.085));
        if (hair < face) { d = hair; mat = 2.0; } else { d = face; mat = 1.0; }
        d = min(d, hair);
    }
    // ---- neck & collar ----
    vec3 up = normalize(J2 - J0);
    vec3 fw = normalize(uBodyFwd - up * dot(uBodyFwd, up));
    vec3 rt = cross(up, fw);
    float neck = sdTaper(p, J2 - up * 0.04, J3 - up * 0.07 + hf * 0.012, 0.056, 0.05);
    if (neck < d) { d = neck; mat = 1.0; }
    // stand-up collar of the coat, higher at the back
    float collar = sdTaper(p, J2 - up * 0.03 - fw * 0.008, J2 + up * 0.042 - fw * 0.02, 0.069, 0.073);
    collar = smax(collar, -sdTaper(p, J2 - up * 0.02 + fw * 0.05, J2 + up * 0.12 + fw * 0.08, 0.05, 0.07), 0.01); // open at the throat
    // ---- torso (coat over body) ----
    vec3 tq = p - J0;
    vec3 tl = vec3(dot(tq, rt), dot(tq, up), dot(tq, fw));
    float chest = sdEllipsoid(tl - vec3(0.0, 0.30, -0.008), vec3(0.165, 0.18, 0.115));
    float waist = sdEllipsoid(tl - vec3(0.0, 0.10, 0.0), vec3(0.157, 0.17, 0.11));
    float hips = sdEllipsoid(tl - vec3(0.0, -0.04, 0.004), vec3(0.17, 0.12, 0.124));
    float torso = smin(smin(chest, waist, 0.08), hips, 0.08);
    vec3 nb = J2 - up * 0.012 - fw * 0.014;
    float trapL = sdTaper(p, nb, uJ[4] + up * 0.012 - fw * 0.006, 0.05, 0.05);
    float trapR = sdTaper(p, nb, uJ[8] + up * 0.012 - fw * 0.006, 0.05, 0.05);
    float delt = min(sdSphere(p - uJ[4] + up * 0.022, 0.05), sdSphere(p - uJ[8] + up * 0.022, 0.05));
    float coat = smin(torso, min(trapL, trapR), 0.06);
    coat = smin(coat, delt, 0.045);
    coat = smin(coat, collar, 0.022);
    // centre back seam / vent hint (subtle groove)
    coat += 0.0025 * exp(-sq(tl.x / 0.006)) * step(tl.z, 0.0) * smoothstep(0.35, 0.0, tl.y);
    // sleeves
    float armL = smin(sdTaper(p, uJ[4], uJ[5], 0.06, 0.051), sdTaper(p, uJ[5], uJ[6], 0.051, 0.045), 0.018);
    float armR = smin(sdTaper(p, uJ[8], uJ[9], 0.06, 0.051), sdTaper(p, uJ[9], uJ[10], 0.051, 0.045), 0.018);
    coat = smin(coat, armL, 0.03);
    coat = smin(coat, armR, 0.03);
    // ---- skirt of the long coat ----
    vec3 wind = vec3(0.8, 0.0, 0.6);
    float below = saturate((J0.y - p.y) / max(J0.y - uHemY, 0.2));
    vec3 ps = p + wind * uCoatWind * 0.07 * below * below * (0.75 + 0.25 * sin(uTime * 1.3 + p.y * 3.0));
    vec3 sq0 = ps - J0;
    vec2 cs = vec2(dot(sq0, rt), dot(sq0, fw));
    float ang = atan(cs.y, cs.x);
    float flare = below;
    vec2 rad = vec2(0.172 + 0.045 * flare, 0.126 + 0.042 * flare);
    rad *= 1.0 + 0.025 * uCoatWind * below * sin(ang * 3.0 + uTime * 1.9 + p.y * 5.0);
    float skirt = (length(cs / rad) - 1.0) * min(rad.x, rad.y);
    // legs push the coat
    for (int s = 0; s < 2; s++) {
        int o = 12 + s * 4;
        float th = sdTaper(ps, uJ[o], uJ[o + 1], 0.12, 0.105);
        float sh = sdTaper(ps, uJ[o + 1], mix(uJ[o + 1], uJ[o + 2], 0.5), 0.105, 0.095);
        skirt = smin(skirt, min(th, sh), 0.12);
    }
    skirt = smax(skirt, ps.y - J0.y - 0.02, 0.06);
    float hem = uHemY + 0.018 * uCoatWind * sin(ang * 2.0 + uTime * 1.6) + 0.01 * sin(ang * 5.0 + 1.3);
    skirt = smax(skirt, hem - p.y, 0.012);
    coat = smin(coat, skirt, 0.06);
    if (coat < d) { d = coat; mat = 0.0; }
    // ---- hands ----
    for (int s = 0; s < 2; s++) {
        int o = 6 + s * 4;
        vec3 a = uJ[o], b = uJ[o + 1];
        float hand = sdTaper(p, a + (b - a) * 0.1, b, 0.034, 0.024);
        if (hand < d) { d = hand; mat = 1.0; }
    }
    // ---- trousers & boots ----
    for (int s = 0; s < 2; s++) {
        int o = 12 + s * 4;
        float leg = smin(sdTaper(p, uJ[o], uJ[o + 1], 0.088, 0.066), sdTaper(p, uJ[o + 1], uJ[o + 2], 0.063, 0.056), 0.03);
        leg -= 0.004 * sin(p.y * 70.0 + float(s) * 2.0) * smoothstep(0.32, 0.12, p.y);
        if (leg < d) { d = leg; mat = 3.0; }
        vec3 ank = uJ[o + 2], toe = uJ[o + 3];
        vec3 fd = toe - ank; fd.y = 0.0; float fl = length(fd); fd /= max(fl, 1e-4);
        vec3 fr = vec3(fd.z, 0.0, -fd.x);
        vec3 c = ank + fd * (fl * 0.5 - 0.02) - vec3(0, ank.y - 0.045, 0);
        vec3 bq = p - c;
        vec3 bl = vec3(dot(bq, fr), bq.y, dot(bq, fd));
        float boot = sdRoundBox(bl, vec3(0.044, 0.04, fl * 0.5 + 0.03), 0.032);
        boot = smin(boot, sdTaper(p, ank - vec3(0, 0.03, 0), ank + vec3(0, 0.08, 0), 0.05, 0.052), 0.03);
        if (boot < d) { d = boot; mat = 4.0; }
    }
    gHeroMat = mat;
    return d;
}

bool heroBoundHit(vec3 ro, vec3 rd, out float t0, out float t1) {
    vec3 oc = ro - uHeroBound.xyz;
    float b = dot(oc, rd);
    float c = dot(oc, oc) - uHeroBound.w * uHeroBound.w;
    float disc = b * b - c;
    if (disc < 0.0) return false;
    float s = sqrt(disc);
    t0 = max(-b - s, 0.0); t1 = -b + s;
    return t1 > 0.0;
}

float traceHero(vec3 ro, vec3 rd, float tmax, out float minRatio) {
    minRatio = 1e5;
    if (uHero == 0) return -1.0;
    float t0, t1;
    if (!heroBoundHit(ro, rd, t0, t1)) return -1.0;
    t1 = min(t1, tmax);
    float t = t0;
    for (int i = 0; i < 72; i++) {
        if (t > t1) break;
        float d = sdHero(ro + rd * t);
        minRatio = min(minRatio, d / max(t, 0.05));
        if (d < 0.0006 * t + 0.0004) return t;
        t += d * 0.8;
    }
    return -1.0;
}

vec3 heroNormal(vec3 p) {
    const vec2 k = vec2(1.0, -1.0);
    float e = 0.0012;
    return normalize(k.xyy * sdHero(p + k.xyy * e) + k.yyx * sdHero(p + k.yyx * e) +
                     k.yxy * sdHero(p + k.yxy * e) + k.xxx * sdHero(p + k.xxx * e));
}

// soft shadow of the hero toward a light (for the sand / water)
float heroShadow(vec3 p, vec3 l) {
    if (uHero == 0) return 1.0;
    float t0, t1;
    if (!heroBoundHit(p, l, t0, t1)) return 1.0;
    float res = 1.0;
    float t = max(t0, 0.02);
    for (int i = 0; i < 28; i++) {
        if (t > t1) break;
        float d = sdHero(p + l * t);
        res = min(res, 9.0 * d / t);
        if (res < 0.01) break;
        t += clamp(d, 0.02, 0.25);
    }
    return smoothstep(0.0, 1.0, res);
}

// =====================================================================
// HEIGHTFIELD TRACE (terrain + water)
// =====================================================================
float sceneH(vec2 xz, out float tH) {
    tH = terrainH(xz);
    float wH = waterHTrace(xz, tH);
    return max(tH, wH);
}

bool traceHF(vec3 ro, vec3 rd, float tmax, out float tHit) {
    float yTop = (rd.z < 0.0) ? 14.0 : 2.2 + uRocky * 1.6;
    float t = 0.02;
    if (ro.y > yTop) {
        if (rd.y >= 0.0) return false;
        t = (ro.y - yTop) / -rd.y;
    }
    float tPrev = t;
    float th;
    for (int i = 0; i < 140; i++) {
        vec3 p = ro + rd * t;
        float h = sceneH(p.xz, th);
        float d = p.y - h;
        if (d < 0.0) {
            float a = tPrev, b = t;
            for (int j = 0; j < 7; j++) {
                float m = 0.5 * (a + b);
                vec3 pm = ro + rd * m;
                if (pm.y - sceneH(pm.xz, th) < 0.0) b = m; else a = m;
            }
            tHit = 0.5 * (a + b);
            return true;
        }
        if (t > tmax || (p.y > yTop && rd.y > 0.0)) return false;
        tPrev = t;
        t += max(d * 0.55, 0.008 + 0.012 * t);
    }
    return false;
}

// =====================================================================
// MIST (volumetric near field + analytic far field)
// =====================================================================
float fogDensity(vec3 p) {
    float hf = exp(-max(p.y, -1.0) / uFogH);
    vec3 q = p - uWindVel * uTime;
    float n = n3(q * 0.012) * 0.65 + n3(q * 0.041 + 0.37) * 0.35;
    float m = saturate(1.0 + uMist * 1.6 * n);
    float d = uFogDens * hf * m;
    if (uGroundMist > 0.0) {
        vec3 qg = (p - uWindVel * 1.4 * uTime) * vec3(0.035, 0.16, 0.05);
        float w = n3(qg) * 0.7 + n3(qg * 2.7 + 0.21) * 0.3;
        float wisps = smoothstep(-0.05, 0.45, w);
        d += uGroundMist * exp(-max(p.y - 0.05 * n3(qg * 3.0), 0.0) / 0.75) * wisps;
    }
    return d;
}

vec3 fogLight(vec3 rd) {
    float cm = dot(rd, uMoonDir);
    float cs = dot(rd, uSunDir);
    vec3 l = gMoon * (phaseHG(cm, uFogG) * 0.8 + phaseHG(cm, 0.2) * 0.2)
           + uSunCol * (phaseHG(cs, uFogG) * 0.75 + phaseHG(cs, 0.1) * 0.25)
           + uAmbient * 0.5;
    return l * uFogCol;
}

// analytic height fog integral from ro along rd for distance t
float fogOptical(vec3 ro, vec3 rd, float t) {
    float k = 1.0 / uFogH;
    float a = uFogDens * exp(-ro.y * k);
    float b = rd.y * k;
    float od = (abs(b) > 1e-4) ? a * (1.0 - exp(-b * t)) / b : a * t;
    return od + uFogFar * t;
}

// =====================================================================
// SHADING
// =====================================================================
vec3 heroShade(vec3 p, vec3 rd, float mat) {
    vec3 n = heroNormal(p);
    vec3 v = -rd;
    float ndl = dot(n, uMoonDir);
    float ndv = saturate(dot(n, v));
    vec3 alb = vec3(0.028, 0.03, 0.034);                     // charcoal wool coat
    float sheen = 0.8;
    if (mat > 0.5 && mat < 1.5) { alb = vec3(0.32, 0.22, 0.18); sheen = 0.25; }   // skin
    else if (mat > 1.5 && mat < 2.5) { alb = vec3(0.018, 0.015, 0.013); sheen = 0.5; } // hair
    else if (mat > 2.5 && mat < 3.5) { alb = vec3(0.022, 0.023, 0.026); sheen = 0.6; }// trousers
    else if (mat > 3.5) { alb = vec3(0.018, 0.016, 0.015); sheen = 0.3; }          // boots
    float wrap = saturate((ndl + 0.35) / 1.35);
    // ambient occlusion (cheap)
    float ao = 0.0, sca = 1.0;
    for (int i = 1; i <= 3; i++) {
        float h = 0.03 * float(i);
        ao += (h - sdHero(p + n * h)) * sca; sca *= 0.6;
    }
    ao = saturate(1.0 - 6.0 * ao);
    vec3 skyAmb = uAmbient * (0.55 + 0.45 * n.y) + uFogCol * uFogDens * 30.0 * uAmbient;
    vec3 col = alb * (gMoon * wrap + uSunCol * saturate((dot(n, uSunDir) + 0.3) / 1.3) + skyAmb * ao);
    // rim / sheen from back light through mist (fabric fibres)
    float back = saturate(dot(-v, uMoonDir));
    float rim = pow(1.0 - ndv, 3.0);
    col += (gMoon * (0.25 + 1.6 * pow(back, 6.0)) + uSunCol * pow(saturate(dot(-v, uSunDir)), 4.0)) * rim * sheen * 0.22 * ao;
    if (mat > 0.5 && mat < 1.5) {
        // skin subsurface in the terminator
        col += vec3(0.25, 0.08, 0.05) * gMoon * saturate(1.0 - abs(ndl) * 2.5) * 0.05;
        col += (uSunCol * 0.12) * pow(saturate(dot(reflect(rd, n), uSunDir)), 24.0);
    }
    if (mat > 1.5 && mat < 2.5) col += gMoon * (0.05 * pow(saturate(dot(reflect(rd, n), uMoonDir)), 16.0) + 0.12 * rim * pow(back, 3.0));
    return col;
}

vec3 sandShade(vec3 p, vec3 rd, float t, out float wetOut) {
    vec2 xz = p.xz;
    float ze = swashEdge(xz.x, uTime);
    float wetZone = smoothstep(-6.8, -4.2, xz.y);                  // reached by waves
    float glisten = smoothstep(ze - 2.6, ze - 0.05, xz.y) * smoothstep(-6.0, -3.0, xz.y);
    float wet = max(wetZone * 0.75, glisten);
    wetOut = wet;
    // normal: base slope + sand micro ripples (fade with distance)
    float e = 0.04 + 0.002 * t;
    float th;
    float hx = terrainH(xz + vec2(e, 0.0)) - terrainH(xz - vec2(e, 0.0));
    float hz = terrainH(xz + vec2(0.0, e)) - terrainH(xz - vec2(0.0, e));
    vec3 n = normalize(vec3(-hx, 2.0 * e, -hz));
    float lod = saturate(1.0 - t / 60.0);
    vec4 d2 = n2v(xz * vec2(0.9, 1.6));
    n = normalize(n + lod * vec3(d2.a, 0.0, d2.g) * (0.05 - 0.035 * wet));
    vec3 dry = vec3(0.30, 0.285, 0.265);
    vec3 dampc = vec3(0.115, 0.11, 0.105);
    vec3 alb = mix(dry, dampc, wet) * (0.85 + 0.3 * n2v(xz * 0.17).b);
    if (uRocky > 0.0) {
        float rk = saturate((p.y - (-uBeachSlope * xz.y)) / 0.4) * uRocky;
        alb = mix(alb, vec3(0.045, 0.047, 0.05) * (0.8 + 0.4 * n2v(xz * 0.8).r), saturate(rk * 1.5));
    }
    float sh = heroShadow(p + n * 0.01, uMoonDir);
    float shS = (uSunCol.r + uSunCol.g > 0.001) ? heroShadow(p + n * 0.01, uSunDir) : 1.0;
    vec3 col = alb * (gMoon * saturate(dot(n, uMoonDir)) * sh + uSunCol * saturate(dot(n, uSunDir)) * shS + uAmbient * (0.6 + 0.4 * n.y));
    // wet specular: film of water reflects sky, moon and the hero
    if (wet > 0.05) {
        vec3 nw = normalize(mix(n, vec3(0.0, 1.0, 0.0), 0.6 * glisten));
        vec3 r = reflect(rd, nw);
        r.y = abs(r.y);
        float fr = fresnelSchlick(saturate(dot(-rd, nw)), 0.02) * wet;
        vec3 refl = skyRadiance(r, false);
        float rough = mix(0.16, 0.06, glisten);
        vec3 hv = normalize(uMoonDir - rd);
        refl += gMoon * uMoonDisk * 0.00022 * ggxD(saturate(dot(nw, hv)), rough) * gMoonVis;
        vec3 hvs = normalize(uSunDir - rd);
        refl += uSunCol * uSunDisk * 0.0012 * ggxD(saturate(dot(nw, hvs)), rough);
        // hero reflection
        float mr;
        float th2 = traceHero(p + nw * 0.01, r, 30.0, mr);
        if (th2 > 0.0) {
            float hm = gHeroMat;
            vec3 hp = p + r * th2;
            vec3 hc = heroShade(hp, r, hm);
            refl = mix(refl, hc, exp(-th2 * 0.25 * (1.0 - glisten)));
        }
        col = mix(col, refl, fr * (0.7 + 0.3 * glisten));
        col += refl * 0.0;
    }
    return col;
}

vec3 waterShade(vec3 p, vec3 rd, float t, out float foamOut) {
    gCamDist = t;
    float tH = terrainH(p.xz);
    float depth = max(-tH, 0.0);
    vec2 grad; float crest, sheet;
    int nn = (t < 25.0) ? NW : ((t < 90.0) ? 12 : ((t < 250.0) ? 9 : 6));
    float h = waterH(p.xz, tH, nn, grad, crest, sheet);
    vec3 n = normalize(vec3(-grad.x, 1.0, -grad.y));
    // small-scale ripples from scrolling detail maps, faded with distance (anti-alias)
    float lod = saturate(1.0 - t / 90.0);
    vec2 uvA = p.xz * vec2(0.9, 0.35) + vec2(0.021, -0.06) * uTime;
    vec2 uvB = p.xz * vec2(2.1, 0.9) + vec2(-0.043, -0.09) * uTime;
    vec4 a = n2v(uvA), b = n2v(uvB);
    vec3 dn = vec3(a.g + 0.5 * b.g, 0.0, a.a + 0.5 * b.a);
    n = normalize(n + dn * 0.042 * lod * (1.0 - 0.7 * sheet));
    vec3 v = -rd;
    float nv = saturate(dot(n, v));
    float fr = fresnelSchlick(nv, 0.02);
    vec3 r = reflect(rd, n);
    if (r.y < 0.0) r = normalize(vec3(r.x, -r.y * 0.3 + 0.002, r.z));
    vec3 refl = skyRadiance(r, false);
    // unresolved slope variance grows with distance → moon/sun glitter path widens into a smooth glade
    float rough = 0.018 + 0.07 * (1.0 - lod) + 0.0006 * t;
    vec3 hv = normalize(uMoonDir + v);
    float spec = ggxD(saturate(dot(n, hv)), rough) * fr / max(4.0 * nv * saturate(dot(n, uMoonDir)) + 0.05, 0.05);
    refl += gMoon * uMoonDisk * 0.0009 * spec * saturate(dot(n, uMoonDir) * 4.0) * gMoonVis;
    vec3 hvs = normalize(uSunDir + v);
    float specS = ggxD(saturate(dot(n, hvs)), rough) * fr / max(4.0 * nv * saturate(dot(n, uSunDir)) + 0.05, 0.05);
    refl += uSunCol * uSunDisk * 0.0016 * specS * saturate(dot(n, uSunDir) * 4.0);
    // hero reflection
    float mr;
    float thh = traceHero(p + vec3(0, 0.01, 0), r, 40.0, mr);
    if (thh > 0.0) {
        float hm = gHeroMat;
        refl = mix(refl, heroShade(p + r * thh, r, hm), 0.9);
    }
    // body of water: upwelling + see-through to the sand in the shallows
    vec3 body = uDeepCol * (uAmbient * 0.6 + gMoon * 0.25 * saturate(uMoonDir.y + 0.2));
    // translucency of crests in back light
    float back = pow(saturate(dot(rd, uMoonDir)), 3.0) * crest;
    body += uDeepCol * gMoon * back * 0.9 * vec3(0.6, 1.0, 0.9);
    float backS = pow(saturate(dot(rd, uSunDir)), 3.0) * crest;
    body += vec3(0.25, 0.5, 0.45) * uSunCol * backS * 0.25;
    float thick = (sheet > 0.5) ? (h - tH) : depth;
    if (thick < 3.0) {
        float wtmp;
        vec3 bottomP = p + refract(rd, n, 0.75) * (thick / max(-refract(rd, n, 0.75).y, 0.3));
        vec3 bottom = sandShade(vec3(bottomP.x, terrainH(bottomP.xz), bottomP.z), rd, t, wtmp);
        vec3 att = exp(-vec3(1.6, 0.55, 0.42) * thick * 2.2);
        body = mix(body, bottom, att);
    }
    // glow from the depth (Ocean answering)
    if (uGlow.w > 0.0) {
        float gd = length(p.xz - uGlow.xz);
        body += uGlowCol * uGlow.w * exp(-gd * gd / 6.0) * (0.5 + 0.5 * nv);
    }
    vec3 col = mix(body, refl, fr);
    // ---- foam ----
    float ze = swashEdge(p.x, uTime);
    vec2 fuv = p.xz * vec2(0.22, 0.55) + vec2(0.0, -0.11 * uTime);
    vec4 fn = n2v(fuv), fn2 = n2v(fuv * vec2(3.1, 2.2) + 0.3);
    float lace = saturate(0.55 + 0.9 * fn.r + 0.45 * fn2.g);
    float edgeF = smoothstep(ze - 0.05, ze + 0.25, p.z) * (1.0 - smoothstep(ze + 0.3, ze + 2.2, p.z));
    float surf = smoothstep(0.55, 0.95, crest) * smoothstep(0.15, 0.6, depth) * (1.0 - smoothstep(0.9, 2.2, depth));
    float trail = smoothstep(0.0, 0.3, depth) * (1.0 - smoothstep(0.45, 1.2, depth)) * 0.16 * smoothstep(0.1, 0.5, fn2.b + 0.3);
    float foam = saturate((edgeF * 0.9 + surf + trail) * lace) * uFoamAmt;
    foam *= smoothstep(-0.3, 0.6, lace - 0.35);
    foamOut = foam;
    vec3 foamCol = vec3(0.78, 0.8, 0.82) * (gMoon * saturate(n.y * 0.8 + 0.2) + uSunCol * 0.9 + uAmbient * 1.1);
    col = mix(col, foamCol, foam * 0.85);
    return col;
}

// =====================================================================
// MAIN
// =====================================================================
void main() {
    gMoonVis = moonVisibility();
    gMoon = uMoonCol * (0.4 + 0.6 * gMoonVis);
    vec2 frag = (vUV * uCrop.zw + uCrop.xy) * uRes + uJitter;
    vec2 ndc = (frag / uRes) * 2.0 - 1.0;
    float aspect = uRes.x / uRes.y;
    float halfW = 18.0 / uFocal;            // tan(hfov/2) for 36 mm gate
    vec3 rd = normalize(uCamRot * vec3(ndc.x * halfW, ndc.y * halfW / aspect, 1.0));
    vec3 ro = uCamPos;

    if (uStudio == 1) {
        float mr;
        float th = traceHero(ro, rd, 50.0, mr);
        vec3 c = mix(vec3(0.16, 0.165, 0.17), vec3(0.06, 0.062, 0.066), vUV.y);
        float tf = (rd.y < 0.0) ? -ro.y / rd.y : 1e9;
        if (tf < 1e8) {
            vec3 pf = ro + rd * tf;
            c = vec3(0.09) * (0.6 + 0.4 * heroShadow(pf + vec3(0, 0.002, 0), uMoonDir));
        }
        if (th > 0.0 && th < tf) { float hm = gHeroMat; c = heroShade(ro + rd * th, rd, hm); }
        outColor = vec4(c, min(th > 0.0 ? th : 50.0, tf));
        return;
    }
    float tMax = 1200.0;
    float tHF;
    bool hitHF = traceHF(ro, rd, 700.0, tHF);
    float minRatio;
    float tHero = traceHero(ro, rd, hitHF ? tHF : tMax, minRatio);

    vec3 col;
    float tHit = tMax;
    if (tHero > 0.0) {
        float hm = gHeroMat;
        vec3 p = ro + rd * tHero;
        col = heroShade(p, rd, hm);
        tHit = tHero;
    } else if (hitHF) {
        vec3 p = ro + rd * tHF;
        float th = terrainH(p.xz);
        vec2 g; float c, s;
        float wh = waterH(p.xz, th, 6, g, c, s);
        float dummy;
        if (wh > th + 0.0015) col = waterShade(p, rd, tHF, dummy);
        else col = sandShade(p, rd, tHF, dummy);
        tHit = tHF;
    } else if (rd.y < 0.0) {
        // far ocean beyond trace range: flat plane with averaged (rough) shading
        float tp = -ro.y / rd.y;
        vec3 p = ro + rd * tp;
        float dummy;
        col = waterShade(p, rd, tp, dummy);
        tHit = tp;
    } else {
        col = skyRadiance(rd, true);
        tHit = tMax;
    }

    // ---- mist: near-field volumetric march ----
    float marchEnd = min(tHit, 140.0);
    const int NS = 26;
    float jit = fract(hash2i(ivec2(gl_FragCoord.xy)) + float(uFrame % 64) * 0.61803398);
    vec3 fl = fogLight(rd);
    float T = 1.0;
    vec3 scat = vec3(0.0);
    float tPrev = 0.0;
    for (int i = 0; i < NS; i++) {
        float f0 = (float(i) + jit) / float(NS);
        float tt = marchEnd * f0 * f0;
        float dt = tt - tPrev;
        tPrev = tt;
        vec3 p = ro + rd * tt;
        float dens = fogDensity(p);
        float tr = exp(-dens * dt);
        scat += T * (1.0 - tr) * fl;
        T *= tr;
    }
    // far field: analytic
    if (tHit > marchEnd) {
        vec3 p0 = ro + rd * marchEnd;
        float od = fogOptical(p0, rd, min(tHit, 6000.0) - marchEnd);
        float tr = exp(-od);
        vec3 farL = fl;
        scat += T * (1.0 - tr) * farL;
        T *= tr;
    }
    col = col * T + scat;
    outColor = vec4(max(col, 0.0), tHit);
}
