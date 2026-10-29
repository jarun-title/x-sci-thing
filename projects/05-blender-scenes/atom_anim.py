"""Animated 3D oxygen atom, timed to the HyperFrames atom scene (5 s, frames 1..150).

usage: python atom_anim.py <out_dir> [res_pct] [samples] [first] [last]
       python atom_anim.py --still <out.png> <frame> [res_pct] [samples]

Nucleus: 8 protons (red) + 8 neutrons (grey), drawn ~2,000x too large to be visible.
Electrons: a cloud of glowing points shaped like the 1s, 2s and 2p orbitals (where the 8 electrons
are likely to be found), not orbits. From 2.9 s heat arrives: the cloud jitters harder and warms.
At 4.4 s the camera pulls far away (the atom shrinks into a molecule; HyperFrames fades it out).
Every frame is a pure function of t; finished frames are skipped.
"""
import bpy, math, os, random, sys
import numpy as np
from mathutils import Vector

FPS, N = 30, 150
args = sys.argv[1:]
STILL = args and args[0] == '--still'
if STILL:
    out_png, still_frame = args[1], int(args[2])
    res = int(args[3]) if len(args) > 3 else 67; spp = int(args[4]) if len(args) > 4 else 32
else:
    out_dir = args[0]
    res = int(args[1]) if len(args) > 1 else 67; spp = int(args[2]) if len(args) > 2 else 32
    first = int(args[3]) if len(args) > 3 else 1; last = int(args[4]) if len(args) > 4 else N

clamp = lambda x, a=0.0, b=1.0: max(a, min(b, x))
lerp = lambda a, b, k: a + (b - a) * k
mix = lambda c1, c2, k: tuple(lerp(a, b, k) for a, b in zip(c1, c2))
heat_at = lambda t: 0.25 * clamp((t - 2.9) / 2.1)          # same curve as the HyperFrames number: 20 °C -> 40 °C
eo4 = lambda x: 1 - (1 - x) ** 4

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
rng = np.random.default_rng(7)

# ---- electron cloud: three point sets (1s, 2s, 2p), units: 1 = 100 px of the 2D version
def cloud_1s(n): return rng.normal(0, 0.26, (n, 3))
def cloud_2s(n):
    r = 1.12 + rng.normal(0, 0.24, n); u = rng.uniform(-1, 1, n); th = rng.uniform(0, 2 * np.pi, n); s = np.sqrt(1 - u * u)
    return np.stack([r * s * np.cos(th), r * s * np.sin(th), r * u], 1)
def cloud_2p(n_per_axis):
    pts = []
    for ax in range(3):
        d = (0.86 + rng.normal(0, 0.26, n_per_axis)) * np.where(rng.random(n_per_axis) < .5, -1, 1)
        w1 = rng.normal(0, 1, n_per_axis) * (0.18 + np.abs(d) * 0.22); w2 = rng.normal(0, 1, n_per_axis) * (0.18 + np.abs(d) * 0.22)
        p = np.zeros((n_per_axis, 3)); p[:, ax] = d; p[:, (ax + 1) % 3] = w1; p[:, (ax + 2) % 3] = w2; pts.append(p)
    return np.concatenate(pts)

KINDS = [  # base positions, cool colour, emission strength
    (cloud_1s(700), (0.35, 0.72, 1.0), 0.7),
    (cloud_2s(2200), (0.12, 0.52, 1.0), 0.8),
    (cloud_2p(800), (0.18, 0.30, 1.0), 1.0),
]
HOT = (1.0, 0.42, 0.10)


def glow_material(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); e = nt.nodes.new('ShaderNodeEmission'); tr = nt.nodes.new('ShaderNodeBsdfTransparent'); ad = nt.nodes.new('ShaderNodeAddShader')
    e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs[0], ad.inputs[0]); nt.links.new(tr.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], o.inputs['Surface'])
    return m, e


clouds = []
for i, (base, col, strength) in enumerate(KINDS):
    n = len(base)
    pc = bpy.data.pointclouds.new(f'cloud{i}'); pc.resize(n)
    if 'radius' not in pc.attributes: pc.attributes.new('radius', 'FLOAT', 'POINT')
    ob = bpy.data.objects.new(f'cloud{i}', pc); sc.collection.objects.link(ob)
    m, em = glow_material(f'glow{i}', col, strength); pc.materials.append(m)
    clouds.append(dict(pc=pc, base=base.astype(np.float32), seed=rng.uniform(0, 100, n).astype(np.float32), col=col, em=em, strength=strength))

atom = bpy.data.objects.new('Atom', None); sc.collection.objects.link(atom)
for c in clouds: bpy.data.objects[c['pc'].name].parent = atom

# ---- nucleus: 16 nucleons in a tight ball (Fibonacci-ish packing)
def principled(name, base, rough):
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*base, 1); p.inputs['Roughness'].default_value = rough; p.inputs['Coat Weight'].default_value = 0.5
    return m
proton, neutron = principled('Proton', (0.80, 0.14, 0.10), 0.3), principled('Neutron', (0.62, 0.66, 0.72), 0.35)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.095, segments=32, ring_count=16); nmesh_p = bpy.context.object.data; bpy.ops.object.shade_smooth(); bpy.data.objects.remove(bpy.context.object)
nmesh_n = nmesh_p.copy(); nmesh_p.materials.append(proton); nmesh_n.materials.append(neutron)
nucleons = []
for i in range(16):
    phi = math.acos(1 - 2 * (i + .5) / 16); th = math.pi * (1 + 5 ** .5) * i; r = 0.08 if i < 4 else 0.15
    ob = bpy.data.objects.new(f'N{i}', nmesh_p if i % 2 == 0 else nmesh_n); sc.collection.objects.link(ob); ob.parent = atom
    base = Vector((r * math.sin(phi) * math.cos(th), r * math.sin(phi) * math.sin(th), r * math.cos(phi)))
    ob.location = base; nucleons.append((ob, base, i))

# ---- glow around the atom: a soft emissive volume, cool then warm
bpy.ops.mesh.primitive_uv_sphere_add(radius=3.2, segments=48, ring_count=24); halo = bpy.context.object; halo.name = 'Halo'; halo.parent = atom
hm = bpy.data.materials.new('HaloMat'); hm.use_nodes = True; nt = hm.node_tree; nt.nodes.clear()
ho = nt.nodes.new('ShaderNodeOutputMaterial'); vol = nt.nodes.new('ShaderNodeEmission')
tc = nt.nodes.new('ShaderNodeTexCoord'); vm = nt.nodes.new('ShaderNodeVectorMath'); vm.operation = 'LENGTH'
mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 3.2; mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0
pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.2
sm = nt.nodes.new('ShaderNodeMath'); sm.operation = 'MULTIPLY'; sm.inputs[1].default_value = 0.06
nt.links.new(tc.outputs['Object'], vm.inputs[0]); nt.links.new(vm.outputs['Value'], mr.inputs['Value']); nt.links.new(mr.outputs['Result'], pw.inputs[0])
nt.links.new(pw.outputs[0], sm.inputs[0]); nt.links.new(sm.outputs[0], vol.inputs['Strength'])
nt.links.new(vol.outputs[0], ho.inputs['Volume']); halo.data.materials.append(hm)
halo_strength = sm.inputs[1]

w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs['Color'].default_value = (0.004, 0.007, 0.014, 1); bg.inputs['Strength'].default_value = 1.0

bpy.ops.object.light_add(type='AREA', location=(-3, -4, 3)); key = bpy.context.object; key.data.energy = 140; key.data.size = 2
key.rotation_euler = (Vector((0, 0, 0)) - key.location).to_track_quat('-Z', 'Y').to_euler()

cam_d = bpy.data.cameras.new('C'); cam_d.lens = 50; cam_d.clip_start = 0.05; cam_d.clip_end = 400
cam = bpy.data.objects.new('C', cam_d); sc.collection.objects.link(cam); sc.camera = cam


def set_frame(f):
    t = (f - 1) / FPS
    h = heat_at(t); hn = h / 0.25
    # camera: ease in from 17 to 12 over 1.4 s, then pull far away from 4.4 s (the atom shrinks)
    d = 17.0 + (12.0 - 17.0) * eo4(clamp(t / 1.4))
    k = clamp((t - 4.4) / 0.55); d *= math.exp(math.log(9.0) * k ** 3)
    cam.location = (0.0, -d, 0.12 * d)
    cam.rotation_euler = (Vector((0, 0, 0)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    atom.rotation_euler = (0.3, 0.0, t * 0.25)
    jit = 0.02 + 0.09 * hn; ex = 1 + 0.12 * hn
    for c in clouds:
        b, s = c['base'], c['seed']
        off = np.stack([np.sin(s * 9 + t * 9), np.cos(s * 7 + t * 8), np.sin(s * 5 + t * 7)], 1) * jit
        c['pc'].attributes['position'].data.foreach_set('vector', (b * ex + off).astype(np.float32).ravel())
        flick = 0.45 + 0.55 * np.abs(np.sin(s * 50 + t * (5 + 10 * hn)))
        c['pc'].attributes['radius'].data.foreach_set('value', (0.0095 * flick).astype(np.float32))
        c['em'].inputs['Color'].default_value = (*mix(c['col'], HOT, 0.12 * hn), 1)
        c['pc'].update_tag()
    for ob, base, i in nucleons:
        sh = 0.006 * hn
        ob.location = base + Vector((math.sin(t * 30 + i) * sh, math.cos(t * 27 + i) * sh, math.sin(t * 23 + i) * sh))
    hc = mix((0.25, 0.55, 1.0), (1.0, 0.5, 0.18), hn)
    vol.inputs['Color'].default_value = (*hc, 1); halo_strength.default_value = 0.06 + 0.16 * hn
    bg.inputs['Color'].default_value = (*mix((0.004, 0.007, 0.014), (0.03, 0.012, 0.006), hn), 1)
    sc.frame_set(f)


sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = spp
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.04; sc.cycles.use_denoising = True
sc.cycles.volume_step_rate = 2.0; sc.cycles.max_bounces = 4; sc.cycles.transparent_max_bounces = 64
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, res
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.image_settings.file_format = 'PNG'

if STILL:
    set_frame(still_frame); sc.render.filepath = out_png; bpy.ops.render.render(write_still=True)
else:
    os.makedirs(out_dir, exist_ok=True)
    for f in range(first, last + 1):
        path = os.path.join(out_dir, f'f_{f:04d}.png')
        if os.path.exists(path) and os.path.getsize(path) > 0: continue
        tmp = path + '.tmp.png'
        set_frame(f); sc.render.filepath = tmp; bpy.ops.render.render(write_still=True)
        os.replace(tmp, path); print('done', f, flush=True)
