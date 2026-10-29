"""A still of liquid water at the molecular scale, in real 3D.

usage: python molecules.py <out.png> <heat 0..1> [res_pct] [samples]
Ball-and-stick H2O (O–H 0.96, H–O–H 104.5°, 1 unit = 100 pm), packed like a liquid,
dashed-looking hydrogen bonds as faint glowing threads, shallow depth of field on the
centre molecule. heat=1 tints the oxygens hot, adds a warm glow from below and loosens
the packing. Seeded, so both stills share the same arrangement.
"""
import bpy, math, random, sys
from mathutils import Vector, Euler, Matrix

out = sys.argv[1]; heat = float(sys.argv[2])
res = int(sys.argv[3]) if len(sys.argv) > 3 else 67
spp = int(sys.argv[4]) if len(sys.argv) > 4 else 64

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
rnd = random.Random(11)
lerp = lambda a, b, k: a + (b - a) * k


def mat(name, base, rough, emit=None, strength=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = base; p.inputs['Roughness'].default_value = rough
    p.inputs['Coat Weight'].default_value = coat
    if emit:
        p.inputs['Emission Color'].default_value = emit; p.inputs['Emission Strength'].default_value = strength
    return m


def mat_emit(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    o = nt.nodes.new('ShaderNodeOutputMaterial'); e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = color; e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs[0], o.inputs['Surface'])
    return m


# ---- shared meshes (every molecule reuses them)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.62, segments=48, ring_count=24); o_mesh = bpy.context.object.data
bpy.ops.object.shade_smooth(); bpy.data.objects.remove(bpy.context.object)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.36, segments=32, ring_count=16); h_mesh = bpy.context.object.data
bpy.ops.object.shade_smooth(); bpy.data.objects.remove(bpy.context.object)
bpy.ops.mesh.primitive_cylinder_add(radius=0.11, depth=1.0, vertices=24); b_mesh = bpy.context.object.data
bpy.ops.object.shade_smooth(); bpy.data.objects.remove(bpy.context.object)
bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=1.0, vertices=8); hb_mesh = bpy.context.object.data
bpy.data.objects.remove(bpy.context.object)

o_cool, o_hot = (0.78, 0.13, 0.10, 1), (0.95, 0.32, 0.05, 1)
o_mat = mat('Oxygen', tuple(lerp(a, b, heat) for a, b in zip(o_cool, o_hot)), 0.28, (1.0, 0.35, 0.05, 1) if heat > 0 else None, 0.45 * heat, coat=0.4)
h_mat = mat('Hydrogen', (0.92, 0.94, 0.97, 1), 0.3, coat=0.4)
b_mat = mat('Bond', (0.72, 0.76, 0.82, 1), 0.4)
hb_mat = mat_emit('HBond', (0.4, 0.78, 1.0, 1), 0.9 * (1 - 0.8 * heat))
o_mesh.materials.append(o_mat); h_mesh.materials.append(h_mat); b_mesh.materials.append(b_mat); hb_mesh.materials.append(hb_mat)


def link(name, mesh, loc, rot=None, scale=None):
    ob = bpy.data.objects.new(name, mesh); bpy.context.collection.objects.link(ob)
    ob.location = loc
    if rot is not None: ob.rotation_euler = rot
    if scale is not None: ob.scale = scale
    return ob


def cylinder_between(name, mesh, a, b):
    d = b - a; ob = link(name, mesh, (a + b) / 2)
    ob.rotation_euler = d.to_track_quat('Z', 'Y').to_euler(); ob.scale = (1, 1, d.length)
    return ob


# ---- pack molecules like a liquid: random positions with a minimum O–O distance (~2.8 Å)
HALF = math.radians(104.5 / 2); OH = 0.96
spacing = 2.75 + 0.5 * heat
box = (14.0, 11.0, 18.0)  # x, y (depth), z
pos = [Vector((0, 0, 0))]
tries = 0
while len(pos) < 420 and tries < 60000:
    tries += 1
    p = Vector((rnd.uniform(-box[0], box[0]), rnd.uniform(-2.2, box[2]), rnd.uniform(-box[1] / 1.6, box[1] / 1.6)))
    if all((p - q).length > spacing for q in pos): pos.append(p)

mols = []
for i, p in enumerate(pos):
    # centre molecule faces the camera with its H atoms pointing down, like the textbook drawing
    rot = Euler((0, 0, 0)) if i == 0 else Euler((rnd.uniform(0, 6.28), rnd.uniform(0, 6.28), rnd.uniform(0, 6.28)))
    m = rot.to_matrix()
    h1 = p + m @ Vector((math.sin(HALF) * OH, 0, -math.cos(HALF) * OH))
    h2 = p + m @ Vector((-math.sin(HALF) * OH, 0, -math.cos(HALF) * OH))
    link(f'O{i}', o_mesh, p); link(f'H{i}a', h_mesh, h1); link(f'H{i}b', h_mesh, h2)
    cylinder_between(f'B{i}a', b_mesh, p, h1); cylinder_between(f'B{i}b', b_mesh, p, h2)
    mols.append((p, h1, h2))

# hydrogen bonds: H of one molecule to the nearest O of another, when close enough
for i, (p, h1, h2) in enumerate(mols):
    for h in (h1, h2):
        best, bd = None, 9.0
        for j, (q, _, _) in enumerate(mols):
            if j == i: continue
            d = (q - h).length
            if d < bd: best, bd = q, d
        if best is not None and bd < 2.3 + 0.2 * heat and rnd.random() > 0.6 * heat:
            # shorten so the thread stops at the atom surfaces
            dirv = (best - h).normalized()
            cylinder_between(f'HB{i}', hb_mesh, h + dirv * 0.36, best - dirv * 0.62)

# ---- world, lights, camera
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']
bg.inputs['Color'].default_value = tuple(lerp(a, b, heat) for a, b in zip((0.010, 0.040, 0.085, 1), (0.06, 0.025, 0.015, 1)))
bg.inputs['Strength'].default_value = 1.0

bpy.ops.object.light_add(type='AREA', location=(-6, -8, 7))
key = bpy.context.object; key.data.energy = 2600; key.data.size = 6; key.data.color = (1.0, 0.93, 0.85)
key.rotation_euler = (Vector((0, 0, 0)) - key.location).to_track_quat('-Z', 'Y').to_euler()
bpy.ops.object.light_add(type='AREA', location=(7, 10, 3))
rim = bpy.context.object; rim.data.energy = 3000; rim.data.size = 5; rim.data.color = (0.45, 0.72, 1.0) if heat < 0.5 else (1.0, 0.6, 0.3)
rim.rotation_euler = (Vector((0, 0, 0)) - rim.location).to_track_quat('-Z', 'Y').to_euler()
if heat > 0:
    bpy.ops.object.light_add(type='AREA', location=(0, 2, -9))
    warm = bpy.context.object; warm.data.energy = 1400 * heat; warm.data.size = 14; warm.data.color = (1.0, 0.45, 0.15)
    warm.rotation_euler = Euler((0, 0, 0))

cam_d = bpy.data.cameras.new('C'); cam_d.lens = 50
cam_d.dof.use_dof = True; cam_d.dof.focus_distance = 9.0; cam_d.dof.aperture_fstop = 1.2
cam = bpy.data.objects.new('C', cam_d); bpy.context.collection.objects.link(cam); sc.camera = cam
cam.location = (1.2, -9.0, 0.9)
cam.rotation_euler = (Vector((0.15, 0, -0.15)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
# keep the near field clear so the centre molecule is the subject
for ob in list(bpy.data.objects):
    if ob.type == 'MESH' and ob.name != 'Cube' and (ob.location - cam.location).length < 6.5:
        bpy.data.objects.remove(ob)

# mist-like depth falloff: a soft volume makes far molecules fade into the water colour
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 8, 0)); fog = bpy.context.object; fog.scale = (60, 34, 40)
fm = bpy.data.materials.new('Fog'); fm.use_nodes = True; nt = fm.node_tree; nt.nodes.clear()
fo = nt.nodes.new('ShaderNodeOutputMaterial'); vs = nt.nodes.new('ShaderNodeVolumePrincipled')
vs.inputs['Color'].default_value = tuple(lerp(a, b, heat) for a, b in zip((0.25, 0.55, 0.85, 1), (0.55, 0.22, 0.08, 1)))
vs.inputs['Density'].default_value = 0.03
nt.links.new(vs.outputs[0], fo.inputs['Volume']); fog.data.materials.append(fm)

sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = spp; sc.cycles.use_denoising = True
sc.cycles.volume_step_rate = 4.0
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, res
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print('molecules:', len(mols))
