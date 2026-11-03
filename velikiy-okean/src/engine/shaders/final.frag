#version 430
// Tone mapping, grade, bloom/halation, vignette, film grain, dither. Display-referred output.
#include "common.glsl"
in vec2 vUV;
layout(location = 0) out vec4 outColor;
uniform sampler2D uImg;     // linear HDR with mipmaps
uniform vec2 uRes;
uniform int uFrame;
uniform float uExposure;
uniform vec3 uLift;
uniform vec3 uGammaG;
uniform vec3 uGain;
uniform float uSat;
uniform float uContrast;
uniform vec3 uShadowTint;
uniform vec3 uHighTint;
uniform float uBloom;
uniform float uHalation;
uniform float uVignette;
uniform float uGrain;
uniform float uFade;
uniform vec3 uFadeCol;

vec3 acesFit(vec3 x) {   // Narkowicz 2015 fit of the ACES RRT+ODT
    return saturate((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14));
}
vec3 tentLod(vec2 uv, float lod) {
    vec2 o = exp2(lod) / uRes;
    return 0.25 * (textureLod(uImg, uv + vec2(o.x, o.y) * 0.5, lod).rgb + textureLod(uImg, uv + vec2(-o.x, o.y) * 0.5, lod).rgb +
                   textureLod(uImg, uv + vec2(o.x, -o.y) * 0.5, lod).rgb + textureLod(uImg, uv + vec2(-o.x, -o.y) * 0.5, lod).rgb);
}
float gauss(ivec2 p, int f) {   // approx. normal noise from 4 uniform hashes
    vec3 a = hash3i(ivec3(p, f));
    vec3 b = hash3i(ivec3(p.yx + 7919, f + 31));
    return (a.x + a.y + a.z + b.x - 2.0) * 1.7;
}
void main() {
    vec3 hdr = textureLod(uImg, vUV, 0.0).rgb;
    vec3 bl = tentLod(vUV, 2.0) * 0.30 + tentLod(vUV, 3.0) * 0.26 + tentLod(vUV, 4.0) * 0.22 + tentLod(vUV, 5.0) * 0.14 + tentLod(vUV, 6.0) * 0.08;
    vec3 hal = tentLod(vUV, 3.0) * 0.6 + tentLod(vUV, 4.0) * 0.4;
    vec3 c = hdr + bl * uBloom;
    c += max(hal - 0.08, 0.0) * vec3(1.0, 0.42, 0.22) * uHalation;
    c *= uExposure;
    c = acesFit(c);
    // grade (display referred)
    c = pow(max(c, 0.0), vec3(1.0 / 2.2));
    float L = luma(c);
    c = mix(vec3(L), c, uSat);
    c = (c - 0.45) * uContrast + 0.45;
    c = c * uGain + uLift * (1.0 - c);
    c = pow(max(c, 0.0), 1.0 / uGammaG);
    L = luma(c);
    c += uShadowTint * (1.0 - smoothstep(0.0, 0.45, L)) + uHighTint * smoothstep(0.5, 1.0, L);
    // vignette
    vec2 q = (vUV - 0.5) * vec2(uRes.x / uRes.y, 1.0);
    float vig = 1.0 - uVignette * smoothstep(0.35, 1.05, length(q * vec2(0.82, 1.0)));
    c *= vig;
    c = mix(c, uFadeCol, uFade);
    // film grain: two scales, luminance dependent (strongest in mids)
    ivec2 p = ivec2(gl_FragCoord.xy);
    float g = gauss(p, uFrame) * 0.6 + gauss(p / 2, uFrame + 101) * 0.55;
    L = luma(c);
    float resp = 0.35 + 0.65 * (1.0 - abs(L - 0.4) * 1.6);
    c += g * uGrain * max(resp, 0.15) * (0.6 + 0.4 * vec3(1.0, 0.95, 1.08));
    // triangular dither before 8-bit quantisation
    vec3 dth = hash3i(ivec3(p, uFrame + 977)) - hash3i(ivec3(p + 13, uFrame + 541));
    c += dth / 255.0;
    outColor = vec4(saturate(c), 1.0);
}
