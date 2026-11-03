#version 430
// Depth of field: physically based circle of confusion + scatter-as-gather on a golden-angle spiral.
in vec2 vUV;
layout(location = 0) out vec4 outColor;
uniform sampler2D uHDR;
uniform vec2 uRes;
uniform float uFocusDist;
uniform float uFocal;
uniform float uFStop;
uniform float uMaxCoc;

float coc(float z) {
    float f = uFocal * 0.001;
    float A = f / uFStop;
    float zf = max(uFocusDist, f * 1.5);
    float c = abs(A * f * (z - zf) / (max(z, 0.01) * (zf - f)));
    return min(c / 0.036 * uRes.x * 0.5, uMaxCoc);
}

void main() {
    vec4 c0 = texture(uHDR, vUV);
    float r0 = coc(c0.a);
    if (uMaxCoc < 0.5) { outColor = c0; return; }
    vec2 px = 1.0 / uRes;
    const int N = 40;
    const float GA = 2.39996323;
    vec3 acc = c0.rgb;
    float wsum = 1.0;
    float rad = 0.5;
    float maxR = uMaxCoc;
    for (int i = 0; i < N; i++) {
        float fi = float(i) + 0.5;
        float r = sqrt(fi / float(N)) * maxR;
        float a = fi * GA;
        vec2 uv = vUV + vec2(cos(a), sin(a)) * r * px;
        vec4 s = texture(uHDR, uv);
        float rs = coc(s.a);
        // background samples cannot bleed over a sharper foreground centre
        if (s.a > c0.a) rs = clamp(rs, 0.0, r0 * 2.0);
        float w = smoothstep(r - 1.0, r + 1.0, rs);
        acc += s.rgb * w;
        wsum += w;
    }
    outColor = vec4(acc / wsum, c0.a);
}
