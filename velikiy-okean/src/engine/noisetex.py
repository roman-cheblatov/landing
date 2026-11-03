"""Tileable noise textures generated from scratch (no third-party assets).
3D: RGBA float16 128^3 — four independent periodic gradient-noise fields at different base frequencies.
2D: RGBA float16 1024^2 — periodic gradient noise fbm channels for sand/rock/foam detail."""
import numpy as np

def _fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)

def perlin3(n, period, seed):
    rng = np.random.default_rng(seed)
    g = rng.normal(size=(period, period, period, 3)).astype(np.float32)
    g /= np.linalg.norm(g, axis=-1, keepdims=True)
    c = (np.arange(n, dtype=np.float32) + 0.5) * period / n
    X, Y, Z = np.meshgrid(c, c, c, indexing='ij')
    xi, yi, zi = np.floor(X).astype(int), np.floor(Y).astype(int), np.floor(Z).astype(int)
    xf, yf, zf = X - xi, Y - yi, Z - zi
    u, v, w = _fade(xf), _fade(yf), _fade(zf)
    out = np.zeros_like(X)
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                gg = g[(xi + dx) % period, (yi + dy) % period, (zi + dz) % period]
                d = gg[..., 0] * (xf - dx) + gg[..., 1] * (yf - dy) + gg[..., 2] * (zf - dz)
                wx = u if dx else 1 - u
                wy = v if dy else 1 - v
                wz = w if dz else 1 - w
                out += wx * wy * wz * d
    return out

def perlin2(n, period, seed):
    rng = np.random.default_rng(seed)
    a = rng.uniform(0, 2 * np.pi, size=(period, period)).astype(np.float32)
    g = np.stack([np.cos(a), np.sin(a)], -1)
    c = (np.arange(n, dtype=np.float32) + 0.5) * period / n
    X, Y = np.meshgrid(c, c, indexing='ij')
    xi, yi = np.floor(X).astype(int), np.floor(Y).astype(int)
    xf, yf = X - xi, Y - yi
    u, v = _fade(xf), _fade(yf)
    out = np.zeros_like(X)
    for dx in (0, 1):
        for dy in (0, 1):
            gg = g[(xi + dx) % period, (yi + dy) % period]
            d = gg[..., 0] * (xf - dx) + gg[..., 1] * (yf - dy)
            out += (u if dx else 1 - u) * (v if dy else 1 - v) * d
    return out

def fbm3(n, base, octaves, seed):
    acc, amp, tot = 0, 1.0, 0
    for o in range(octaves):
        acc = acc + amp * perlin3(n, base * 2 ** o, seed + 17 * o)
        tot += amp
        amp *= 0.5
    return acc / tot

def fbm2(n, base, octaves, seed, gain=0.5):
    acc, amp, tot = 0, 1.0, 0
    for o in range(octaves):
        acc = acc + amp * perlin2(n, base * 2 ** o, seed + 31 * o)
        tot += amp
        amp *= gain
    return acc / tot

def make_3d(n=96):
    ch = [fbm3(n, 4, 3, 1), fbm3(n, 8, 2, 101), perlin3(n, 16, 202), perlin3(n, 6, 303)]
    a = np.stack(ch, -1)
    a = a / (np.abs(a).max(axis=(0, 1, 2), keepdims=True) + 1e-6) * 0.5 + 0.5
    return a.astype(np.float16)

def make_2d(n=1024):
    ch = [fbm2(n, 8, 6, 11), fbm2(n, 32, 4, 22), fbm2(n, 4, 7, 33, gain=0.55), perlin2(n, 128, 44)]
    a = np.stack(ch, -1)
    a = a / (np.abs(a).max(axis=(0, 1), keepdims=True) + 1e-6) * 0.5 + 0.5
    return a.astype(np.float16)

if __name__ == '__main__':
    import sys, time
    t = time.time()
    np.save(sys.argv[1] + '/noise3d.npy', make_3d())
    np.save(sys.argv[1] + '/noise2d.npy', make_2d())
    print('ok', time.time() - t)
