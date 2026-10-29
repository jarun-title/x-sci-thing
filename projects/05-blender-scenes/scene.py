"""3D glass of water for the HyperFrames film.

Usage (headless):
  python scene.py intro  <out_dir> [res_pct] [samples] [frame_start] [frame_end]
  python scene.py outro  <out_dir> ...
  python scene.py still  <out_png> <shot> <frame>

intro : 5.5 s. Glass on a table, slow push, then a dive into the water (fastest at ~5.3 s).
outro : 5.5 s. Lowered water, boiling: bubbles rise and the surface churns. Camera pulls back
        from just above the rim to the whole glass in the first 1.5 s. Steam is added in HyperFrames.
Units are metres. All randomness is seeded.
"""
import bpy, bmesh, math, random, sys
from mathutils import Vector

FPS = 30
N_FRAMES = 165  # 5.5 s
GLASS_H, R_TOP, R_BOT, WALL, BASE = 0.12, 0.042, 0.034, 0.0025, 0.008
X_GLASS = 0.0


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, N_FRAMES
    return sc


def mat_glass(name, ior=1.5, color=(1, 1, 1, 1), rough=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    g = nt.nodes.new('ShaderNodeBsdfGlass'); g.inputs['IOR'].default_value = ior
    g.inputs['Color'].default_value = color; g.inputs['Roughness'].default_value = rough
    nt.links.new(g.outputs[0], out.inputs['Surface'])
    return m


def mat_water():
    m = bpy.data.materials.new('Water'); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    g = nt.nodes.new('ShaderNodeBsdfGlass'); g.inputs['IOR'].default_value = 1.333
    g.inputs['Color'].default_value = (0.86, 0.95, 1.0, 1)
    # a faint blue absorption so a deep view through the water reads as water
    vol = nt.nodes.new('ShaderNodeVolumeAbsorption'); vol.inputs['Color'].default_value = (0.55, 0.8, 0.95, 1); vol.inputs['Density'].default_value = 6.0
    nt.links.new(g.outputs[0], out.inputs['Surface']); nt.links.new(vol.outputs[0], out.inputs['Volume'])
    return m


def mat_principled(name, color, rough, emission=None, strength=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = color; p.inputs['Roughness'].default_value = rough
    if emission:
        p.inputs['Emission Color'].default_value = emission; p.inputs['Emission Strength'].default_value = strength
    return m


def frustum(name, r_bot, r_top, z0, z1, segs=160, cap_bottom=True, cap_top=True):
    bm = bmesh.new()
    bot = [bm.verts.new((r_bot * math.cos(2 * math.pi * i / segs), r_bot * math.sin(2 * math.pi * i / segs), z0)) for i in range(segs)]
    top = [bm.verts.new((r_top * math.cos(2 * math.pi * i / segs), r_top * math.sin(2 * math.pi * i / segs), z1)) for i in range(segs)]
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    if cap_bottom: bm.faces.new(list(reversed(bot)))
    if cap_top: bm.faces.new(top)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    for f in me.polygons: f.use_smooth = True
    return ob


def build(level, boiling):
    sc = bpy.context.scene
    # ---- world: almost black, a hint of navy
    w = bpy.data.worlds.new('World'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (0.006, 0.009, 0.016, 1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0

    # ---- table
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, 0))
    bpy.context.object.data.materials.append(mat_principled('Table', (0.004, 0.006, 0.010, 1), 0.42))

    # ---- backdrop strips (soft emissive bars give the glass something to refract)
    for i, (x, y, wdt, col, s) in enumerate([(-0.24, 1.1, 0.018, (0.55, 0.75, 1.0, 1), 2.2), (0.30, 1.0, 0.012, (1.0, 0.82, 0.62, 1), 1.6), (0.02, 1.4, 0.5, (0.12, 0.22, 0.42, 1), 0.12)]):
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, 0.32), rotation=(math.radians(90), 0, 0))
        ob = bpy.context.object; ob.scale = (wdt, 0.6, 1)
        ob.data.materials.append(mat_principled(f'Strip{i}', (0, 0, 0, 1), 1.0, col, s))
        ob.visible_camera = False  # lights the glass, never seen directly

    # ---- lights: warm key, cool rim
    bpy.ops.object.light_add(type='AREA', location=(-0.4, -0.15, 0.45))
    key = bpy.context.object; key.data.energy = 7; key.data.size = 0.3; key.data.color = (1.0, 0.86, 0.72)
    key.rotation_euler = (Vector((X_GLASS, 0, 0.06)) - key.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.ops.object.light_add(type='AREA', location=(0.22, 0.4, 0.4))
    rim = bpy.context.object; rim.data.energy = 6; rim.data.size = 0.2; rim.data.color = (0.55, 0.78, 1.0)
    rim.rotation_euler = (Vector((X_GLASS, 0, 0.06)) - rim.location).to_track_quat('-Z', 'Y').to_euler()

    # ---- glass: outer + inner wall, thick base
    gm = mat_glass('Glass', 1.5, (1, 1, 1, 1))
    outer = frustum('GlassOuter', R_BOT, R_TOP, 0.0, GLASS_H, cap_top=False)
    inner = frustum('GlassInner', R_BOT - WALL, R_TOP - WALL, BASE, GLASS_H, cap_top=False)
    for f in inner.data.polygons: f.flip()
    rimring = frustum('GlassRim', R_TOP, R_TOP, GLASS_H, GLASS_H + 0.0001, cap_bottom=False, cap_top=False)
    # close the lip between outer and inner
    bm = bmesh.new(); segs = 160
    o = [bm.verts.new((R_TOP * math.cos(2 * math.pi * i / segs), R_TOP * math.sin(2 * math.pi * i / segs), GLASS_H)) for i in range(segs)]
    n = [bm.verts.new(((R_TOP - WALL) * math.cos(2 * math.pi * i / segs), (R_TOP - WALL) * math.sin(2 * math.pi * i / segs), GLASS_H)) for i in range(segs)]
    for i in range(segs):
        j = (i + 1) % segs; bm.faces.new((o[i], o[j], n[j], n[i]))
    me = bpy.data.meshes.new('Lip'); bm.to_mesh(me); bm.free()
    lip = bpy.data.objects.new('Lip', me); bpy.context.collection.objects.link(lip)
    for ob in (outer, inner, rimring, lip):
        ob.data.materials.append(gm); ob.location.x = X_GLASS

    # ---- water (sits just inside the inner wall)
    wz = BASE + level * (GLASS_H - BASE)
    r_at = lambda z: (R_BOT - WALL) + ((R_TOP - WALL) - (R_BOT - WALL)) * (z / GLASS_H)
    water = frustum('Water', r_at(BASE) - 0.0003, r_at(wz) - 0.0003, BASE + 0.0003, wz, segs=160, cap_top=False)
    water.location.x = X_GLASS; water.data.materials.append(mat_water())
    # surface ripples: subdivide the top cap and displace it with a moving noise
    bpy.context.view_layer.objects.active = water; water.select_set(True)
    # top surface as concentric rings of quads (an even grid, so displacement has no radial streaks)
    bm = bmesh.new(); bm.from_mesh(water.data)
    rim = sorted([v for v in bm.verts if abs(v.co.z - wz) < 1e-7], key=lambda v: math.atan2(v.co.y, v.co.x))
    segs, rings, R = len(rim), 28, r_at(wz) - 0.0003
    prev = rim
    for k in range(rings - 1, 0, -1):
        rr = R * k / rings
        ring = [bm.verts.new((rr * math.cos(math.atan2(v.co.y, v.co.x)), rr * math.sin(math.atan2(v.co.y, v.co.x)), wz)) for v in rim]
        for i in range(segs):
            j = (i + 1) % segs; bm.faces.new((prev[i], prev[j], ring[j], ring[i]))
        prev = ring
    c = bm.verts.new((0, 0, wz))
    for i in range(segs):
        bm.faces.new((prev[i], prev[(i + 1) % segs], c))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(water.data); bm.free()
    for f in water.data.polygons: f.use_smooth = True
    vg = water.vertex_groups.new(name='surface'); vg.add([v.index for v in water.data.vertices if abs(v.co.z - wz) < 1e-6 and (v.co.x ** 2 + v.co.y ** 2) < (r_at(wz) - 0.004) ** 2], 1.0, 'REPLACE')
    sub = water.modifiers.new('sub', 'SUBSURF'); sub.levels = sub.render_levels = 2; sub.subdivision_type = 'SIMPLE'
    tex = bpy.data.textures.new('ripples', 'CLOUDS'); tex.noise_scale = 0.012 if boiling else 0.02
    ctrl = bpy.data.objects.new('RippleCtrl', None); bpy.context.collection.objects.link(ctrl)
    disp = water.modifiers.new('ripple', 'DISPLACE'); disp.texture = tex; disp.direction = 'Z'; disp.vertex_group = 'surface'
    disp.texture_coords = 'OBJECT'; disp.texture_coords_object = ctrl
    disp.strength = 0.004 if boiling else 0.0006; disp.mid_level = 0.5
    for f, z in ((1, 0.0), (N_FRAMES, 0.25 if boiling else 0.03)):
        ctrl.location = (0, 0, z); ctrl.keyframe_insert('location', frame=f)
    for fc in ctrl.animation_data.action.fcurves if ctrl.animation_data.action and hasattr(ctrl.animation_data.action, 'fcurves') else []:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

    # ---- bubbles while boiling: rise from the bottom, pop at the surface
    if boiling:
        bmat = mat_glass('Bubble', 1.0 / 1.333, (1, 1, 1, 1))
        rnd = random.Random(5)
        for i in range(70):
            r = rnd.uniform(0.0012, 0.0042); per = rnd.uniform(0.9, 1.8) * FPS; ph = rnd.random()
            ang, rad = rnd.uniform(0, 2 * math.pi), math.sqrt(rnd.random()) * 0.8
            bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=16, ring_count=8)
            b = bpy.context.object; b.data.materials.append(bmat); bpy.ops.object.shade_smooth()
            for f in range(1, N_FRAMES + 1):
                a = ((f / per) + ph) % 1.0
                z = BASE + 0.003 + a * (wz - BASE - 0.004)
                rr = rad * (r_at(z) - 0.004)
                b.location = (X_GLASS + rr * math.cos(ang) + 0.002 * math.sin(a * 9 + i), rr * math.sin(ang), z)
                s = (0.6 + 0.6 * a) if a < 0.97 else 0.0
                b.scale = (s, s, s)
                b.keyframe_insert('location', frame=f); b.keyframe_insert('scale', frame=f)
    return wz


def camera_intro(wz):
    cam_data = bpy.data.cameras.new('Cam'); cam_data.lens = 50; cam_data.clip_start = 0.002
    cam = bpy.data.objects.new('Cam', cam_data); bpy.context.collection.objects.link(cam); bpy.context.scene.camera = cam
    tgt = bpy.data.objects.new('Target', None); bpy.context.collection.objects.link(tgt)
    con = cam.constraints.new('TRACK_TO'); con.target = tgt; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
    # (frame, camera position, look-at). Glass sits right of centre: the look-at is offset left.
    keys = [
        (1,   (-0.17, -0.50, 0.17), (-0.048, 0, 0.062)),
        (118, (-0.12, -0.37, 0.14), (-0.034, 0, 0.062)),
        (162, (X_GLASS - 0.004, -0.012, wz - 0.03), (X_GLASS, 0.05, wz - 0.035)),
    ]
    for f, p, t in keys:
        cam.location = p; cam.keyframe_insert('location', frame=f)
        tgt.location = t; tgt.keyframe_insert('location', frame=f)
    return cam, tgt


def camera_outro(wz):
    cam_data = bpy.data.cameras.new('Cam'); cam_data.lens = 50; cam_data.clip_start = 0.002
    cam = bpy.data.objects.new('Cam', cam_data); bpy.context.collection.objects.link(cam); bpy.context.scene.camera = cam
    tgt = bpy.data.objects.new('Target', None); bpy.context.collection.objects.link(tgt)
    con = cam.constraints.new('TRACK_TO'); con.target = tgt; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
    keys = [
        (1,   (-0.02, -0.11, 0.17), (-0.008, 0, wz + 0.01)),
        (45,  (-0.17, -0.50, 0.17), (-0.048, 0, 0.062)),
        (165, (-0.18, -0.52, 0.175), (-0.048, 0, 0.062)),
    ]
    for f, p, t in keys:
        cam.location = p; cam.keyframe_insert('location', frame=f)
        tgt.location = t; tgt.keyframe_insert('location', frame=f)
    return cam, tgt


def ease(cam, tgt, mode):
    # intro: gentle push, then the dive accelerates into the water (ease in)
    # outro: pull back with ease in-out, then a near-still hold
    for ob in (cam, tgt):
        ad = ob.animation_data
        act = ad.action if ad else None
        if not act: continue
        curves = act.fcurves if hasattr(act, 'fcurves') else [fc for layer in act.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]
        for fc in curves:
            kps = fc.keyframe_points
            for k, kp in enumerate(kps):
                if mode == 'intro':
                    kp.interpolation = 'BEZIER' if k == 0 else 'CUBIC'
                    if k == 1: kp.easing = 'EASE_IN'
                else:
                    kp.interpolation = 'CUBIC' if k == 0 else 'LINEAR'
                    if k == 0: kp.easing = 'EASE_IN_OUT'


def setup_render(res_pct, samples):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
    sc.cycles.samples = samples; sc.cycles.use_denoising = True
    sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = 0.03
    sc.cycles.max_bounces = 16; sc.cycles.transmission_bounces = 16; sc.cycles.transparent_max_bounces = 16
    sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, res_pct
    sc.render.image_settings.file_format = 'PNG'
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
    sc.render.threads_mode = 'AUTO'


def make(shot):
    reset()
    if shot == 'intro':
        wz = build(level=0.72, boiling=False); cam, tgt = camera_intro(wz)
    else:
        wz = build(level=0.52, boiling=True); cam, tgt = camera_outro(wz)
    ease(cam, tgt, shot)
    return wz


if __name__ == '__main__':
    args = sys.argv[1:]
    if args[0] == 'still':
        out, shot, frame = args[1], args[2], int(args[3])
        res = int(args[4]) if len(args) > 4 else 50; spp = int(args[5]) if len(args) > 5 else 32
        make(shot); setup_render(res, spp)
        bpy.context.scene.frame_set(frame); bpy.context.scene.render.filepath = out
        bpy.ops.render.render(write_still=True)
    else:
        shot, out = args[0], args[1]
        res = int(args[2]) if len(args) > 2 else 50; spp = int(args[3]) if len(args) > 3 else 48
        fs = int(args[4]) if len(args) > 4 else 1; fe = int(args[5]) if len(args) > 5 else N_FRAMES
        make(shot); setup_render(res, spp)
        sc = bpy.context.scene; sc.frame_start, sc.frame_end = fs, fe
        sc.render.filepath = out.rstrip('/') + '/f_'
        bpy.ops.render.render(animation=True)
