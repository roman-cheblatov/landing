"""Offline GL renderer (moderngl on Mesa llvmpipe; run under xvfb-run). No GPU required.
Pipeline per frame: world.frag (HDR + depth) -> dof.frag -> mipmaps -> final.frag (tonemap/grade/grain) -> RGB8.
"""
import os
import re
import numpy as np
import moderngl

HERE = os.path.dirname(os.path.abspath(__file__))
SHD = os.path.join(HERE, 'shaders')


def load_shader(name):
    src = open(os.path.join(SHD, name)).read()

    def inc(m):
        return open(os.path.join(SHD, m.group(1))).read()
    return re.sub(r'#include "([^"]+)"', inc, src)


class Renderer:
    def __init__(self, out_w=1920, out_h=1080, ss=1.0, cache_dir=None):
        self.ctx = moderngl.create_standalone_context(require=430)
        self.out_w, self.out_h = out_w, out_h
        self.rw, self.rh = int(round(out_w * ss)), int(round(out_h * ss))
        self.ss = ss
        vs = load_shader('quad.vert')
        self.p_world = self.ctx.program(vertex_shader=vs, fragment_shader=load_shader('world.frag'))
        self.p_dof = self.ctx.program(vertex_shader=vs, fragment_shader=load_shader('dof.frag'))
        self.p_final = self.ctx.program(vertex_shader=vs, fragment_shader=load_shader('final.frag'))
        self.vao_world = self.ctx.vertex_array(self.p_world, [])
        self.vao_dof = self.ctx.vertex_array(self.p_dof, [])
        self.vao_final = self.ctx.vertex_array(self.p_final, [])
        cache_dir = cache_dir or os.path.join(HERE, '..', '..', 'work', 'cache')
        n3 = np.load(os.path.join(cache_dir, 'noise3d.npy')).astype('f4')
        n2 = np.load(os.path.join(cache_dir, 'noise2d.npy')).astype('f4')
        self.t_n3 = self.ctx.texture3d(n3.shape[:3][::-1], 4, n3.tobytes(), dtype='f4')
        self.t_n3.repeat_x = self.t_n3.repeat_y = self.t_n3.repeat_z = True
        self.t_n3.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.t_n2 = self.ctx.texture(n2.shape[:2][::-1], 4, n2.tobytes(), dtype='f4')
        self.t_n2.repeat_x = self.t_n2.repeat_y = True
        self.t_n2.build_mipmaps()
        self.t_n2.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        self.t_hdr = self.ctx.texture((self.rw, self.rh), 4, dtype='f4')
        self.t_hdr.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.t_hdr.repeat_x = self.t_hdr.repeat_y = False
        self.f_hdr = self.ctx.framebuffer([self.t_hdr])
        self.t_dof = self.ctx.texture((self.rw, self.rh), 4, dtype='f2')
        self.t_dof.repeat_x = self.t_dof.repeat_y = False
        self.f_dof = self.ctx.framebuffer([self.t_dof])
        self.t_out = self.ctx.texture((out_w, out_h), 4, dtype='f1')
        self.f_out = self.ctx.framebuffer([self.t_out])

    @staticmethod
    def _set(prog, name, val):
        if name not in prog:
            return
        u = prog[name]
        if isinstance(val, np.ndarray):
            if val.ndim == 2 and val.shape == (3, 3):
                u.write(val.T.astype('f4').tobytes())   # column-major
            else:
                u.write(val.astype('f4').tobytes())
        elif isinstance(val, (list, tuple)):
            u.value = tuple(float(x) for x in val)
        elif isinstance(val, bool):
            u.value = int(val)
        else:
            u.value = val

    def render(self, U, P, frame=0, crop=(0.0, 0.0, 1.0, 1.0)):
        """U: world uniforms dict; P: post uniforms dict. Returns HxWx3 uint8."""
        ctx = self.ctx
        self.t_n3.use(0)
        self.t_n2.use(1)
        pw = self.p_world
        self._set(pw, 'uN3', 0)
        self._set(pw, 'uN2', 1)
        self._set(pw, 'uRes', (self.rw, self.rh))
        self._set(pw, 'uFrame', frame)
        self._set(pw, 'uCrop', crop)
        for k, v in U.items():
            self._set(pw, k, v)
        self.f_hdr.use()
        self.vao_world.render(moderngl.TRIANGLES, vertices=3)
        # depth of field
        self.t_hdr.use(2)
        pd = self.p_dof
        self._set(pd, 'uHDR', 2)
        self._set(pd, 'uRes', (self.rw, self.rh))
        for k in ('uFocusDist', 'uFocal', 'uFStop', 'uMaxCoc'):
            self._set(pd, k, P[k] if k in P else U[k])
        self.f_dof.use()
        self.vao_dof.render(moderngl.TRIANGLES, vertices=3)
        self.t_dof.build_mipmaps()
        self.t_dof.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
        # final
        self.t_dof.use(3)
        pf = self.p_final
        self._set(pf, 'uImg', 3)
        self._set(pf, 'uN3', 0)
        self._set(pf, 'uN2', 1)
        self._set(pf, 'uRes', (self.out_w, self.out_h))
        self._set(pf, 'uFrame', frame)
        for k, v in P.items():
            self._set(pf, k, v)
        self.f_out.use()
        self.vao_final.render(moderngl.TRIANGLES, vertices=3)
        data = self.f_out.read(components=3, alignment=1)
        img = np.frombuffer(data, np.uint8).reshape(self.out_h, self.out_w, 3)[::-1]
        ctx.finish()
        return img
