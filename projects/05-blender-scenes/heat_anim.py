"""Animated 3D heat scene: liquid water heats up, hydrogen bonds break, molecules escape as vapour.

usage: python heat_anim.py <out_dir> [res_pct] [samples] [first] [last]
       python heat_anim.py --still <out.png> <frame> [res_pct] [samples]

7 s at 30 fps (frames 1..210), timed to match the HyperFrames heat scene:
  heat(t)  = 0.25 + 0.75 * ease(t / 4.2)      -> 40 °C .. 100 °C (HyperFrames shows the number)
  vapor(t) = clamp((t - 4.1) / 2.9)
Every frame is a pure function of t: the scene is built once, then each frame sets transforms and
material values and renders a still. Frames already on disk are skipped, so a restart loses at most one.
1 unit = 100 pm. Seeded.
"""
import bpy, math, os, random, sys
from mathutils import Vector, Euler, Matrix, Quaternion

FPS, N = 30, 210
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
io = lambda x: 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
heat_at = lambda t: 0.25 + 0.75 * io(clamp(t / 4.2))
vap_at = lambda t: clamp((t - 4.1) / 2.9)

# agitation clock: heat integrated once, so vibration speeds up smoothly
DT = 0.005; TAU = [0.0]
for i in range(1, int(7.2 / DT) + 2): TAU.append(TAU[-1] + DT * (1 + 3.2 * heat_at(i * DT)))
def tau_at(t):
    k = clamp(t, 0, 7.2) / DT; i = int(k); return TAU[i] + (TAU[min(i + 1, len(TAU) - 1)] - TAU[i]) * (k - i)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
rnd = random.Random(11)


def principled(name, base, rough, coat=0.4):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = base; p.inputs['Roughness'].default_value = rough; p.inputs['Coat Weight'].default_value = coat
    p.inputs['Emission Color'].default_value = (1.0, 0.35, 0.05, 1); p.inputs['Emission Strength'].default_value = 0.0
    return m, p


def emissive(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = color; e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs[0], o.inputs['Surface'])
    return m, e


def mesh_of(op, **kw):
    op(**kw); ob = bpy.context.object; me = ob.data
    bpy.ops.object.shade_smooth(); bpy.data.objects.remove(ob); return me


o_mesh = mesh_of(bpy.ops.mesh.primitive_uv_sphere_add, radius=0.62, segments=48, ring_count=24)
h_mesh = mesh_of(bpy.ops.mesh.primitive_uv_sphere_add, radius=0.36, segments=32, ring_count=16)
b_mesh = mesh_of(bpy.ops.mesh.primitive_cylinder_add, radius=0.11, depth=1.0, vertices=24)
hb_mesh = mesh_of(bpy.ops.mesh.primitive_cylinder_add, radius=0.016, depth=1.0, vertices=8)
o_mat, o_bsdf = principled('Oxygen', (0.78, 0.13, 0.10, 1), 0.28)
h_mat, _ = principled('Hydrogen', (0.92, 0.94, 0.97, 1), 0.3)
b_mat, _ = principled('Bond', (0.72, 0.76, 0.82, 1), 0.4, coat=0.0)
hb_mat, hb_em = emissive('HBond', (0.4, 0.78, 1.0, 1), 0.9)
o_mesh.materials.append(o_mat); h_mesh.materials.append(h_mat); b_mesh.materials.append(b_mat); hb_mesh.materials.append(hb_mat)


def new(name, mesh):
    ob = bpy.data.objects.new(name, mesh); bpy.context.collection.objects.link(ob); return ob


def place_between(ob, a, b):
    d = b - a; ob.location = (a + b) / 2
    ob.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); ob.scale = (1, 1, max(d.length, 1e-4))


# ---- liquid packing (min O–O distance ~2.75), with a clear cone toward the camera
HALF = math.radians(104.5 / 2); OH = 0.96
L1 = Vector((math.sin(HALF) * OH, 0, -math.cos(HALF) * OH)); L2 = Vector((-math.sin(HALF) * OH, 0, -math.cos(HALF) * OH))
base = [Vector((0, 0, 0))]
tries = 0
while len(base) < 520 and tries < 90000:
    tries += 1
    p = Vector((rnd.uniform(-17, 17), rnd.uniform(-2.2, 20), rnd.uniform(-8.5, 8.5)))
    if p.y < 0.6 and math.hypot(p.x, p.z) < 2.6 + 0.45 * max(0.0, -p.y): continue  # keep the lens clear
    if all((p - q).length > 2.75 for q in base): base.append(p)

mols = []
for i, p in enumerate(base):
    r0 = Euler((0, 0, 0)).to_matrix() if i == 0 else Euler((rnd.uniform(0, 6.28), rnd.uniform(0, 6.28), rnd.uniform(0, 6.28))).to_matrix()
    axis = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
    out = Vector((p.x, abs(p.y) + 4.0, p.z + 3.0)).normalized()  # drift away from the camera, a little upward
    m = dict(p=p, r0=r0, axis=axis, ph=[rnd.uniform(0, 7) for _ in range(4)], fr=rnd.uniform(0.7, 1.3),
             drift=out * (0 if i == 0 else rnd.uniform(0.7, 1.3)), spin=rnd.uniform(-2, 2),
             O=new(f'O{i}', o_mesh), H1=new(f'H{i}a', h_mesh), H2=new(f'H{i}b', h_mesh), B1=new(f'B{i}a', b_mesh), B2=new(f'B{i}b', b_mesh))
    mols.append(m)

# hydrogen bonds from the cool arrangement: an H to the nearest O of another molecule
def pose(m, t):
    tau, h, v = tau_at(t), heat_at(t), vap_at(t)
    hn = (h - 0.25) / 0.75
    amp = 0.06 + 0.45 * h; ph = m['ph']
    p = m['p'] * (1 + 0.12 * hn)
    p = p + Vector((amp * math.sin(tau * 1.7 * m['fr'] + ph[0]), amp * math.sin(tau * 1.5 * m['fr'] + ph[1]), amp * math.cos(tau * 1.3 * m['fr'] + ph[2])))
    p = p + m['drift'] * (26 * v ** 1.8)
    ang = (0.12 + 0.6 * h) * math.sin(tau * 1.1 * m['fr'] + ph[3]) + m['spin'] * v * v * 8
    r = Matrix.Rotation(ang, 3, m['axis']) @ m['r0']
    return p, p + r @ L1, p + r @ L2, r

poses0 = [pose(m, 0) for m in mols]
hbonds = []
for i, (p, h1, h2, _) in enumerate(poses0):
    for k, h in ((1, h1), (2, h2)):
        best, bd = None, 9.0
        for j, (q, _, _, _) in enumerate(poses0):
            if j != i and (q - h).length < bd: best, bd = j, (q - h).length
        if best is not None and bd < 2.3:
            hbonds.append(dict(i=i, k=k, j=best, s=rnd.uniform(0.05, 1.0), ob=new(f'HB{i}{k}', hb_mesh)))

# ---- world, fog, lights, camera
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs['Strength'].default_value = 1.0
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 10, 0)); fog = bpy.context.object; fog.scale = (70, 40, 50); fog.name = 'Fog'
fm = bpy.data.materials.new('FogMat'); fm.use_nodes = True; nt = fm.node_tree; nt.nodes.clear()
fo = nt.nodes.new('ShaderNodeOutputMaterial'); vs = nt.nodes.new('ShaderNodeVolumePrincipled')
nt.links.new(vs.outputs[0], fo.inputs['Volume']); fog.data.materials.append(fm)

def area(loc, energy, size, color, aim=(0, 0, 0)):
    bpy.ops.object.light_add(type='AREA', location=loc); L = bpy.context.object
    L.data.energy, L.data.size, L.data.color = energy, size, color
    L.rotation_euler = (Vector(aim) - L.location).to_track_quat('-Z', 'Y').to_euler(); return L
key = area((-6, -8, 7), 2600, 6, (1.0, 0.93, 0.85))
rim = area((7, 10, 3), 3000, 5, (0.45, 0.72, 1.0))
warm = area((0, 2, -9), 0, 14, (1.0, 0.45, 0.15), aim=(0, 2, 0))

cam_d = bpy.data.cameras.new('C'); cam_d.lens = 50; cam_d.clip_start = 0.05
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 1.2; cam_d.dof.focus_object = mols[0]['O']
cam = bpy.data.objects.new('C', cam_d); bpy.context.collection.objects.link(cam); sc.camera = cam
LOOK = Vector((0.15, 0, -0.15))

COOL_BG, HOT_BG, AIR_BG = (0.010, 0.040, 0.085, 1), (0.06, 0.025, 0.015, 1), (0.008, 0.010, 0.016, 1)
COOL_FOG, HOT_FOG, AIR_FOG = (0.25, 0.55, 0.85, 1), (0.55, 0.22, 0.08, 1), (0.12, 0.13, 0.16, 1)


def set_frame(f):
    t = (f - 1) / FPS
    h, v = heat_at(t), vap_at(t); hn = (h - 0.25) / 0.75
    warmth = clamp((h - 0.2) / 0.8)
    poses = [pose(m, t) for m in mols]
    for m, (p, h1, h2, _) in zip(mols, poses):
        m['O'].location = p; m['H1'].location = h1; m['H2'].location = h2
        place_between(m['B1'], p, h1); place_between(m['B2'], p, h2)
    breakage = 0.75 * hn + 1.2 * v
    for b in hbonds:
        p_i, h1, h2, _ = poses[b['i']]; hpos = h1 if b['k'] == 1 else h2; q = poses[b['j']][0]
        d = q - hpos
        hide = b['s'] < breakage or d.length > 3.2
        b['ob'].hide_render = hide
        if not hide:
            u = d.normalized(); place_between(b['ob'], hpos + u * 0.36, q - u * 0.62)
    # materials and atmosphere follow the temperature, then thin out into vapour
    o_bsdf.inputs['Base Color'].default_value = mix((0.78, 0.13, 0.10, 1), (0.95, 0.32, 0.05, 1), warmth)
    o_bsdf.inputs['Emission Strength'].default_value = 0.45 * warmth
    hb_em.inputs['Strength'].default_value = 0.9 * (1 - 0.8 * hn)
    bg.inputs['Color'].default_value = mix(mix(COOL_BG, HOT_BG, warmth), AIR_BG, 0.85 * v)
    vs.inputs['Color'].default_value = mix(mix(COOL_FOG, HOT_FOG, warmth), AIR_FOG, v)
    vs.inputs['Density'].default_value = 0.03 * (1 - 0.6 * v)
    warm.data.energy = 1400 * warmth * (1 - 0.5 * v)
    rim.data.color = mix((0.45, 0.72, 1.0), (1.0, 0.6, 0.3), warmth)
    # camera: pull out of the atom in 0.9 s, slow orbit, then drift back as the vapour spreads
    k = clamp(t / 0.9); d = 2.6 + (9.0 - 2.6) * (1 - (1 - k) ** 4)
    d += 6.0 * io(clamp((t - 4.2) / 2.8))
    a = -0.06 + 0.035 * t; e = 0.09
    cam.location = LOOK + Vector((d * math.sin(a) * math.cos(e), -d * math.cos(a) * math.cos(e), d * math.sin(e)))
    cam.rotation_euler = (LOOK - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.frame_set(f)  # keeps any frame-dependent internals consistent


sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = spp
sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.04; sc.cycles.use_denoising = True
sc.cycles.volume_step_rate = 4.0; sc.cycles.max_bounces = 6
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, res
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.image_settings.file_format = 'PNG'
print('molecules', len(mols), 'hbonds', len(hbonds))

if STILL:
    set_frame(still_frame); sc.render.filepath = out_png; bpy.ops.render.render(write_still=True)
else:
    os.makedirs(out_dir, exist_ok=True)
    for f in range(first, last + 1):
        path = os.path.join(out_dir, f'f_{f:04d}.png')
        if os.path.exists(path) and os.path.getsize(path) > 0: continue
        tmp = path + '.tmp.png'
        set_frame(f); sc.render.filepath = tmp; bpy.ops.render.render(write_still=True)
        os.replace(tmp, path)  # only a finished frame ever gets its final name
        print('done', f, flush=True)
