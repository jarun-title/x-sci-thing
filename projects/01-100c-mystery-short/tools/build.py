"""Generate index.html and every scene from timeline.json, so the picture follows the narration.
Times inside a scene are local to that scene (seconds from the scene's data-start)."""
import json, re, sys, html
ROOT = sys.argv[1]
TL = json.load(open(f"{ROOT}/timeline.json"))
LINES, SC, FILM = TL["lines"], TL["scenes"], TL["film"]


def word(line, text, nth=1):
    """absolute start time of the nth word in a line that matches text (case/punctuation-insensitive)"""
    n = 0
    for w in LINES[line]["words"]:
        if re.sub(r"[^a-z0-9]", "", w["text"].lower()) == text.lower():
            n += 1
            if n == nth: return w["start"]
    raise KeyError(f"{line}: {text}")


def local(scene, t): return round(t - SC[scene][0], 3)
def dur(scene): return round(SC[scene][1] - SC[scene][0], 3)
def fill(tpl, **kv):
    for k, v in kv.items(): tpl = tpl.replace(f"%%{k}%%", str(v))
    assert "%%" not in tpl, re.findall(r"%%\w+%%", tpl)[:5]
    return tpl


# ------------------------------------------------------------------ hook
HOOK = """<template>
  <style>
    #root { position: absolute; inset: 0; background: #E8EDF1; overflow: hidden; }
    #hk-svg { position: absolute; inset: 0; }
    #hk-note { position: absolute; left: 0; width: 1080px; top: 446px; text-align: center; font-family: Inter; font-weight: 700; font-size: 34px; color: #4A5B68; }
  </style>
  <div id="root" data-composition-id="hook" data-width="1080" data-height="1920">
    <svg id="hk-svg"></svg>
    <div id="hk-note">at sea level · flame on high</div>
  </div>
  <script>
    (() => {
      const k = window.Kitchen(document.getElementById("hk-svg"), "hk");
      // already boiling: the dot creeps along the flat part of the curve while the flame keeps going
      const render = t => k.update(t, { u: 0.86 + 0.1 * Math.min(1, t / %%D%%), flicker: true, boil: 1, flame: 1 });
      const tl = gsap.timeline({ paused: true });
      const clock = { t: 0 };
      tl.fromTo(clock, { t: 0 }, { t: %%D%%, duration: %%D%%, ease: "none", onUpdate: () => render(clock.t) }, 0);
      render(0);
      window.__timelines["hook"] = tl;
    })();
  </script>
</template>
"""

# ------------------------------------------------------------------ zoom
ZOOM = """<template>
  <style>
    #root { position: absolute; inset: 0; background: #0F4C75; overflow: hidden; }
    #zm-k { position: absolute; inset: 0; }
    #zm-svg { position: absolute; inset: 0; }
    #zm-cv { position: absolute; inset: 0; width: 1080px; height: 1920px; }
    #zm-ring { position: absolute; inset: 0; }
    #zm-tag { position: absolute; left: 0; width: 1080px; top: 990px; text-align: center; font-family: Inter; font-weight: 900; font-size: 64px; color: #FFFFFF; paint-order: stroke fill; -webkit-text-stroke: 10px #0B1620; }
  </style>
  <div id="root" data-composition-id="zoom" data-width="1080" data-height="1920">
    <div id="zm-k"><svg id="zm-svg"></svg></div>
    <canvas id="zm-cv" width="1080" height="1920"></canvas>
    <svg id="zm-ring" width="1080" height="1920" viewBox="0 0 1080 1920"><circle id="zm-circle" cx="540" cy="836" r="0" fill="none" stroke="#FFFFFF" stroke-width="10"/></svg>
    <div id="zm-tag">× 300,000,000</div>
  </div>
  <script>
    (() => {
      const W = window.Water2D, k = window.Kitchen(document.getElementById("zm-svg"), "zm");
      const cv = document.getElementById("zm-cv"), ctx = cv.getContext("2d"), circle = document.getElementById("zm-circle");
      const D = %%D%%, CX = 540, CY = 836;
      const ease3in = x => x * x * x, eout = x => 1 - Math.pow(1 - x, 4);
      const radiusAt = t => t < 0.35 ? 130 * eout(t / 0.35) : 130 + 1700 * ease3in(W.clamp((t - 0.55) / (D - 0.55)));
      function render(t) {
        k.update(t, { u: 0.96, temp: 100, boil: 1, flame: 1 });
        const r = radiusAt(t);
        // inside the lens: liquid water, the hero molecule at the lens centre, zooming from 12 to 28 px per Å
        const s = 12 * Math.pow(28 / 12, W.clamp(t / D));
        ctx.clearRect(0, 0, 1080, 1920);
        W.render(ctx, { cx: 0, cy: (960 - CY) / s, s }, t, { T: 20, tau: t, crowd: 1, bondAlpha: 0.9, heroBondAlpha: 0.9, cloud: 0, pairs: 0, pull: 0, heroCalm: 1, heat: 0, flicker: 0, bondScale: 1.4, tile: 1, air: false });
        cv.style.clipPath = `circle(${r.toFixed(1)}px at ${CX}px ${CY}px)`;
        circle.setAttribute("r", r.toFixed(1)); circle.setAttribute("stroke-width", (10 + r * 0.01).toFixed(1));
      }
      const tl = gsap.timeline({ paused: true });
      const clock = { t: 0 };
      tl.fromTo(clock, { t: 0 }, { t: D, duration: D, ease: "none", onUpdate: () => render(clock.t) }, 0);
      // the camera falls through the lens: the kitchen grows away around it
      tl.fromTo("#zm-k", { scale: 1, transformOrigin: "540px 836px" }, { scale: 7, duration: D - 0.55, ease: "power3.in" }, 0.55);
      tl.fromTo("#zm-tag", { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.18, ease: "power4.out" }, 0.4);
      tl.to("#zm-tag", { opacity: 0, filter: "blur(8px)", duration: 0.18, ease: "power2.in" }, 1.75);
      tl.to("#zm-ring", { opacity: 0, duration: 0.25, ease: "power2.in" }, D - 0.3);
      render(0);
      window.__timelines["zoom"] = tl;
    })();
  </script>
</template>
"""

# ------------------------------------------------------------------ world (molecule → bonds → heat → stop → free)
WORLD = """<template>
  <style>
    #root { position: absolute; inset: 0; background: #0F4C75; overflow: hidden; }
    #wd-cv { position: absolute; inset: 0; width: 1080px; height: 1920px; }
    .wd-pos { position: absolute; left: 0; top: 0; width: 0; height: 0; }
    .wd-pos > div { position: absolute; left: -80px; top: -50px; width: 160px; height: 100px; line-height: 100px; text-align: center; white-space: nowrap; transform-origin: 50% 50%; }
    .wd-atom { font-family: Inter; font-weight: 900; font-size: 84px; line-height: 1; }
    .wd-d { font-family: Inter; font-weight: 900; font-size: 58px; line-height: 1; color: #FFFFFF; paint-order: stroke fill; -webkit-text-stroke: 9px #0B1620; }
    .wd-lab { position: absolute; left: 0; top: 0; font-family: Inter; font-weight: 700; font-size: 42px; line-height: 1.15; white-space: nowrap; paint-order: stroke fill; -webkit-text-stroke: 8px #0B1620; color: #FFFFFF; }
    #wd-lead, #wd-lead2 { position: absolute; inset: 0; }
    #wd-panel { position: absolute; left: 230px; top: 196px; width: 620px; height: 240px; border-radius: 28px; background: #0E1A24; }
    #wd-ptitle { position: absolute; left: 38px; top: 26px; font-family: Inter; font-weight: 700; font-size: 34px; color: #9FB0BD; }
    #wd-temp { position: absolute; left: 0; width: 620px; top: 52px; text-align: center; font-family: "League Gothic"; font-size: 190px; line-height: 1; color: #F4F7FA; font-variant-numeric: tabular-nums; }
    #wd-speed { position: absolute; left: 0; width: 1080px; top: 456px; text-align: center; font-family: Inter; font-weight: 700; font-size: 40px; color: #FFFFFF; paint-order: stroke fill; -webkit-text-stroke: 8px #0B1620; }
    #wd-stuck { position: absolute; left: 0; width: 1080px; top: 456px; text-align: center; font-family: Inter; font-weight: 900; font-size: 44px; color: #FF7A2F; paint-order: stroke fill; -webkit-text-stroke: 8px #0B1620; }
  </style>
  <div id="root" data-composition-id="world" data-width="1080" data-height="1920">
    <canvas id="wd-cv" width="1080" height="1920"></canvas>
    <div class="wd-pos" id="wd-O"><div class="wd-atom" id="wd-O-i" style="color:#FFFFFF">O</div></div>
    <div class="wd-pos" id="wd-H1"><div class="wd-atom" id="wd-H1-i" style="color:#24313B">H</div></div>
    <div class="wd-pos" id="wd-H2"><div class="wd-atom" id="wd-H2-i" style="color:#24313B">H</div></div>
    <div class="wd-pos" id="wd-dneg"><div class="wd-d" id="wd-dneg-i">δ−</div></div>
    <div class="wd-pos" id="wd-dpos1"><div class="wd-d" id="wd-dpos1-i">δ+</div></div>
    <div class="wd-pos" id="wd-dpos2"><div class="wd-d" id="wd-dpos2-i">δ+</div></div>
    <div class="wd-pos" id="wd-n1"><div class="wd-d" id="wd-n1-i">δ−</div></div>
    <div class="wd-pos" id="wd-n2"><div class="wd-d" id="wd-n2-i">δ−</div></div>
    <div class="wd-pos" id="wd-n3"><div class="wd-d" id="wd-n3-i">δ+</div></div>
    <div class="wd-pos" id="wd-n4"><div class="wd-d" id="wd-n4-i">δ+</div></div>
    <svg id="wd-lead" width="1080" height="1920" viewBox="0 0 1080 1920"><path id="wd-lead-p" fill="none" stroke="#9ED3FF" stroke-width="4"/></svg>
    <div class="wd-lab" id="wd-hblab" style="color:#9ED3FF">hydrogen bond</div>
    <svg id="wd-lead2" width="1080" height="1920" viewBox="0 0 1080 1920"><path id="wd-lead2-p" fill="none" stroke="#0E1A24" stroke-width="4"/></svg>
    <div class="wd-lab" id="wd-intact" style="color:#0E1A24; -webkit-text-stroke: 8px #E4EFF7">O–H bonds stay intact</div>
    <div id="wd-panel"><div id="wd-ptitle">water temperature</div><div id="wd-temp">20.0 °C</div></div>
    <div id="wd-speed">molecules' average speed +0%</div>
    <div id="wd-stuck">heat still going in ↑</div>
  </div>
  <script>
    (() => {
      const W = window.Water2D, $ = id => document.getElementById(id);
      const cv = $("wd-cv"), ctx = cv.getContext("2d");
      const D = %%D%%;
      const clamp = W.clamp, lerp = W.lerp, smooth = W.smooth;
      const io = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
      const eout = x => 1 - Math.pow(1 - x, 4);
      const seg = (t, a, b) => clamp((t - a) / (b - a));
      // narration marks (scene-local seconds)
      const M = %%MARKS%%;
      // temperature: 20 °C until the heat line, then up to 100 °C right on "hundred"; it never goes higher
      const Tat = t => 20 + 80 * io(seg(t, M.heat + 0.2, M.hundred));
      // agitation clock: integrate how fast things jiggle, so speed-ups are smooth
      const DT = 0.01, NS = Math.ceil(D / DT) + 2, TAU = new Float32Array(NS);
      for (let i = 1; i < NS; i++) { const T = Tat(i * DT); TAU[i] = TAU[i - 1] + DT * (0.6 + 2.6 * clamp((T - 20) / 80)); }
      const tauAt = t => { const k = clamp(t, 0, D) / DT, i = Math.floor(k); return TAU[i] + (TAU[Math.min(i + 1, NS - 1)] - TAU[i]) * (k - i); };
      W.setRelease(M.snap, M.free + 0.9);
      // camera: px per Å and the world point at the screen centre
      function camAt(t) {
        let s, cy;
        const a = eout(seg(t, 0, 1.3));                       // fall in from the lens onto the hero molecule
        s = 28 * Math.pow(230 / 28, a); cy = lerp(4.43, 0.87, a);
        const b = io(seg(t, M.pull0, M.pull0 + 1.4));          // pull back to see the neighbours
        s = s * Math.pow(72 / 230, b); cy = lerp(cy, 3.5, b);
        const c = seg(t, M.heat, M.free0);                     // slow settle while it heats
        s *= lerp(1, 66 / 72, c); cy = lerp(cy, 3.0, c);
        const d = io(seg(t, M.free0 - 0.2, M.free0 + 1.0));   // tilt up to the surface
        s *= lerp(1, 60 / 66, d); cy = lerp(cy, -4.5, d);
        return { cx: 0, cy, s };
      }
      const els = ["wd-O", "wd-H1", "wd-H2", "wd-dneg", "wd-dpos1", "wd-dpos2", "wd-n1", "wd-n2", "wd-n3", "wd-n4", "wd-hblab", "wd-intact"].reduce((o, k) => (o[k] = $(k), o), {});
      const SIZE = {};  // measured once, after the fonts are in
      const measure = () => Object.keys(els).forEach(k => { SIZE[k] = [els[k].offsetWidth, els[k].offsetHeight]; });
      const place = (el, x, y, ax = 0.5, ay = 0.5) => { const [w, h] = SIZE[el.id]; el.style.transform = `translate(${(x - w * ax).toFixed(1)}px, ${(y - h * ay).toFixed(1)}px)`; };
      const tempEl = $("wd-temp"), speedEl = $("wd-speed"), leadP = $("wd-lead-p"), lead2P = $("wd-lead2-p");
      function render(t) {
        const cam = camAt(t), T = Tat(t);
        const P = {
          T, tau: tauAt(t), heroCalm: lerp(0.25, 1, seg(t, M.pull0, M.pull0 + 1.0)),
          crowd: lerp(0.35, 1, seg(t, M.pull0, M.pull0 + 1.0)),
          bondAlpha: smooth(seg(t, M.hb, M.hb + 0.5)), heroBondAlpha: 1,
          cloud: smooth(seg(t, M.sharing - 0.3, M.sharing + 0.4)) * (1 - smooth(seg(t, M.pull0 - 0.4, M.pull0 + 0.1))),
          pairs: smooth(seg(t, M.electrons - 0.25, M.electrons + 0.2)) * (1 - smooth(seg(t, M.pull0 - 0.4, M.pull0 + 0.1))),
          pull: io(seg(t, M.pulls, M.harder + 0.3)),
          heat: smooth(seg(t, M.heat, M.heat + 0.6)), flicker: seg(t, M.heat, M.heat + 1.0),
          bondScale: lerp(1, 1.5, seg(t, M.pull0, M.pull0 + 1.4)),
          tile: 1 - smooth(seg(t, 0.2, 0.75)), air: t > M.pull0, boil: seg(t, M.hundred - 0.5, M.free0),
        };
        ctx.clearRect(0, 0, 1080, 1920);
        const poses = W.render(ctx, cam, t, P);
        const h = poses[0], X = x => W.sx(cam, x), Y = y => W.sy(cam, y);
        // atom letters sit on the atoms of the hero molecule
        place(els["wd-O"], X(h.x), Y(h.y)); place(els["wd-H1"], X(h.h1[0]), Y(h.h1[1])); place(els["wd-H2"], X(h.h2[0]), Y(h.h2[1]));
        // partial charges: δ− beyond O on the lone-pair side, δ+ beyond each H
        const up = h.bis + Math.PI;
        place(els["wd-dneg"], X(h.x + (W.RO + 0.5) * Math.cos(up)), Y(h.y + (W.RO + 0.5) * Math.sin(up)));
        [[h.h1, "wd-dpos1"], [h.h2, "wd-dpos2"]].forEach(([q, id]) => {
          const ux = q[0] - h.x, uy = q[1] - h.y, L = Math.hypot(ux, uy), r = W.RH + 0.42;
          place(els[id], X(q[0] + ux / L * r), Y(q[1] + uy / L * r));
        });
        // opposite charges on the neighbours: the O atoms the hero's H point at (δ−), the H atoms pointing at the hero's O (δ+)
        [[1, "wd-n1"], [2, "wd-n2"]].forEach(([j, id]) => {
          const q = poses[j], ux = q.x - h.x, uy = q.y - h.y, L = Math.hypot(ux, uy), r = W.RO + 0.55;
          place(els[id], X(q.x + ux / L * r), Y(q.y + uy / L * r));
        });
        [[3, 0, "wd-n3"], [4, 1, "wd-n4"]].forEach(([j, k, id]) => {
          const q = poses[j], hh = k === 0 ? q.h1 : q.h2;
          let px = -(hh[1] - h.y), py = hh[0] - h.x; const L = Math.hypot(px, py); px /= L; py /= L;
          if (px * (hh[0] - h.x) + py * (hh[1] - h.y) < 0 || (hh[0] - h.x) * px < 0) { px = -px; py = -py; }
          place(els[id], X(hh[0] + px * (W.RH + 0.45)), Y(hh[1] + py * (W.RH + 0.45)));
        });
        // the hydrogen bond label: on the bond from the hero's first H to its neighbour's O
        const nb = poses[1], hx = (h.h1[0] + nb.x) / 2, hy = (h.h1[1] + nb.y) / 2, bx = X(hx), by = Y(hy);
        const lx = Math.min(980 - SIZE["wd-hblab"][0], bx + 40), ly = by + 150;
        leadP.setAttribute("d", `M${bx} ${by} L${lx + 20} ${ly - 30}`); place(els["wd-hblab"], lx, ly, 0, 0);
        // the escapee keeps its O–H bonds
        const sc = poses[W.showcase], ex = X(sc.x), ey = Y(sc.y);
        // label above the molecule while there is room, below it once it rises toward the readout
        const ix = Math.max(100, Math.min(980 - SIZE["wd-intact"][0], ex - 240)), above = ey - 160 > 540;
        const iy = above ? ey - 160 : ey + W.RO * cam.s + 70;
        lead2P.setAttribute("d", above ? `M${ex} ${ey - W.RO * cam.s - 6} L${ix + 200} ${iy + 52}` : `M${ex} ${ey + W.RO * cam.s + 6} L${ix + 200} ${iy - 6}`);
        place(els["wd-intact"], ix, iy, 0, 0);
        // thermometer readout and average molecular speed (rms speed scales with the square root of kelvin)
        tempEl.textContent = T.toFixed(1) + " °C"; tempEl.style.color = T >= 90 ? "#FF7A2F" : "#F4F7FA";
        speedEl.textContent = `molecules' average speed +${Math.round((Math.sqrt((T + 273.15) / 293.15) - 1) * 100)}%`;
      }
      document.fonts.ready.then(() => {
      measure();
      const tl = gsap.timeline({ paused: true });
      const clock = { t: 0 };
      tl.fromTo(clock, { t: 0 }, { t: D, duration: D, ease: "none", onUpdate: () => render(clock.t) }, 0);
      const pop = (sel, at) => tl.fromTo(sel, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.35, ease: "back.out(1.6)" }, at);
      const out = (sel, at) => { tl.to(sel, { opacity: 0, duration: 0.2, ease: "power2.in" }, at); tl.set(sel, { visibility: "hidden" }, at + 0.2); };
      tl.set(["#wd-O", "#wd-H1", "#wd-H2", "#wd-dneg", "#wd-dpos1", "#wd-dpos2", "#wd-n1", "#wd-n2", "#wd-n3", "#wd-n4", "#wd-hblab", "#wd-lead", "#wd-intact", "#wd-lead2", "#wd-panel", "#wd-speed", "#wd-stuck"], { opacity: 0 }, 0);
      // outer wrappers are positioned every frame; GSAP only animates the inner element
      const show = (id, at) => { tl.set("#" + id, { opacity: 1 }, at); tl.fromTo("#" + id + "-i", { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.35, ease: "back.out(1.6)" }, at); };
      show("wd-O", M.oxygen); show("wd-H1", M.hydrogens); show("wd-H2", M.hydrogens + 0.08);
      show("wd-dneg", M.negative); show("wd-dpos1", M.positive); show("wd-dpos2", M.positive + 0.08);
      out(["#wd-O", "#wd-H1", "#wd-H2"], M.pull0 - 0.4);
      // "opposites attract": the neighbours' charges land next to the hero's, after the pull-back
      show("wd-n1", M.attract); show("wd-n2", M.attract + 0.06); show("wd-n3", M.attract + 0.12); show("wd-n4", M.attract + 0.18);
      out(["#wd-dneg", "#wd-dpos1", "#wd-dpos2", "#wd-n1", "#wd-n2", "#wd-n3", "#wd-n4"], M.hb + 0.2);
      tl.fromTo("#wd-lead", { opacity: 0 }, { opacity: 1, duration: 0.2 }, M.hb + 0.25);
      tl.fromTo("#wd-hblab", { opacity: 0, filter: "blur(6px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.16, ease: "power4.out" }, M.hb + 0.3);
      out(["#wd-hblab", "#wd-lead"], M.heat + 1.6);
      tl.fromTo("#wd-panel", { opacity: 0, y: -30 }, { opacity: 1, y: 0, duration: 0.45, ease: "expo.out" }, M.heat - 0.1);
      tl.fromTo("#wd-speed", { opacity: 0, filter: "blur(6px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.18, ease: "power4.out" }, M.heat + 0.5);
      // at 100 °C the number locks; the speed line gives way to the heat still pouring in
      tl.fromTo("#wd-panel", { scale: 1, transformOrigin: "540px 316px" }, { scale: 1.06, duration: 0.1, ease: "power2.out" }, M.hundred);
      tl.to("#wd-panel", { scale: 1, duration: 0.45, ease: "elastic.out(1, 0.5)" }, M.hundred + 0.1);
      out("#wd-speed", M.stops - 0.35);
      tl.fromTo("#wd-stuck", { opacity: 0, filter: "blur(6px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.18, ease: "power4.out" }, M.stops - 0.15);
      tl.fromTo(["#wd-intact", "#wd-lead2"], { opacity: 0 }, { opacity: 1, duration: 0.2, ease: "power2.out" }, M.intact);
      render(0);
      window.__timelines["world"] = tl;
      });
    })();
  </script>
</template>
"""

# ------------------------------------------------------------------ payoff
PAYOFF = """<template>
  <style>
    #root { position: absolute; inset: 0; background: linear-gradient(#E4EFF7, #C6DDEE); overflow: hidden; }
    #po-cv { position: absolute; inset: 0; width: 1080px; height: 1920px; }
    #po-num { position: absolute; left: 0; width: 1080px; top: 168px; text-align: center; font-family: "League Gothic"; font-size: 260px; line-height: 1; color: #0E1A24; }
    #po-sub { position: absolute; left: 0; width: 1080px; top: 438px; text-align: center; font-family: Inter; font-weight: 700; font-size: 40px; color: #33434F; }
    #po-foot { position: absolute; left: 0; width: 1080px; top: 1122px; text-align: center; font-family: Inter; font-weight: 700; font-size: 34px; color: #4A5B68; }
    #po-one { position: absolute; left: 0; width: 1080px; top: 1060px; text-align: center; font-family: Inter; font-weight: 900; font-size: 52px; color: #0E1A24; }
  </style>
  <div id="root" data-composition-id="payoff" data-width="1080" data-height="1920">
    <canvas id="po-cv" width="1080" height="1920"></canvas>
    <div id="po-num">× 1,600</div>
    <div id="po-sub">cups of steam</div>
    <div id="po-foot">at 100 °C and sea-level pressure</div>
    <div id="po-one">1 cup of water</div>
  </div>
  <script>
    (() => {
      const W = window.Water2D, clamp = W.clamp, lerp = W.lerp;
      const cv = document.getElementById("po-cv"), ctx = cv.getContext("2d");
      const D = %%D%%, M = %%MARKS%%;
      const eout = x => 1 - Math.pow(1 - x, 4), seg = (t, a, b) => clamp((t - a) / (b - a));
      // a mug: body, handle, and (for the water mug) the water inside
      function mug(cx, cy, s, water, alpha) {
        if (alpha <= 0 || s <= 0) return;
        ctx.save(); ctx.globalAlpha = alpha; ctx.translate(cx, cy); ctx.scale(s, s);
        ctx.lineWidth = 7; ctx.strokeStyle = "#0E1A24"; ctx.lineJoin = "round";
        ctx.beginPath(); ctx.moveTo(-40, -46); ctx.lineTo(-34, 44); ctx.quadraticCurveTo(-32, 52, -22, 52); ctx.lineTo(22, 52); ctx.quadraticCurveTo(32, 52, 34, 44); ctx.lineTo(40, -46); ctx.closePath();
        ctx.fillStyle = water ? "#FFFFFF" : "rgba(255,255,255,0.75)"; ctx.fill();
        if (water) { ctx.save(); ctx.clip(); ctx.fillStyle = "#2F7FBA"; ctx.fillRect(-50, -26, 100, 90); ctx.restore(); }
        ctx.stroke();
        ctx.beginPath(); ctx.moveTo(38, -26); ctx.bezierCurveTo(70, -26, 70, 26, 36, 26); ctx.stroke();
        ctx.restore();
      }
      // a few free molecules drifting apart while "free molecules spread out" is said
      const drift = [...Array(26)].map((_, i) => ({ a: i * 2.399, r: 60 + (i % 7) * 26, rot: i * 0.9 }));
      function molecule(x, y, rot, s, a) {
        ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.rotate(rot);
        const H = 104.5 / 2 * Math.PI / 180;
        [[Math.sin(H), Math.cos(H)], [-Math.sin(H), Math.cos(H)]].forEach(([hx, hy]) => { ctx.fillStyle = "#F3F6F8"; ctx.strokeStyle = "#8C9AA5"; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(hx * 0.96 * s, hy * 0.96 * s, 0.36 * s, 0, 7); ctx.fill(); ctx.stroke(); });
        ctx.fillStyle = "#E5484D"; ctx.beginPath(); ctx.arc(0, 0, 0.62 * s, 0, 7); ctx.fill();
        ctx.restore();
      }
      const GX = 540, GY = 800, CELL = 15, N = 40;       // 40 × 40 = 1,600 mugs
      function render(t) {
        ctx.clearRect(0, 0, 1080, 1920);
        const spread = eout(seg(t, 0, M.one));
        const fadeMol = 1 - seg(t, M.one - 0.3, M.one + 0.2);
        drift.forEach((d, i) => molecule(540 + Math.cos(d.a) * d.r * (1 + 4 * spread), 780 + Math.sin(d.a) * d.r * (1 + 4 * spread), d.rot + t * 0.6, 34, fadeMol * 0.9));
        // one mug of water arrives, then shrinks to its cell as the steam mugs fill the grid
        const inA = eout(seg(t, M.one - 0.1, M.one + 0.35));
        const shrink = W.smooth(seg(t, M.becomes, M.becomes + 0.6));
        mug(GX, GY, lerp(3.2, CELL / 100 * 0.9, shrink) * inA, true, inA);
        // keep the original cup findable inside the grid
        if (shrink > 0.9) { ctx.save(); ctx.strokeStyle = "#0E1A24"; ctx.lineWidth = 4; ctx.globalAlpha = (shrink - 0.9) * 10; ctx.beginPath(); ctx.arc(GX, GY, CELL * 1.6, 0, 7); ctx.stroke(); ctx.restore(); }
        const g0 = M.becomes + 0.35;
        for (let r = 0; r < N; r++) for (let c = 0; c < N; c++) {
          if (r === N / 2 && c === N / 2) continue;
          const x = GX + (c - N / 2) * CELL, y = GY + (r - N / 2) * CELL, dist = Math.hypot(c - N / 2, r - N / 2) / (N * 0.71);
          const a = eout(seg(t, g0 + dist * 1.1, g0 + dist * 1.1 + 0.25));
          if (a > 0) mug(x, y, CELL / 100 * 0.9 * a, false, a);
        }
      }
      const tl = gsap.timeline({ paused: true });
      const clock = { t: 0 };
      tl.fromTo(clock, { t: 0 }, { t: D, duration: D, ease: "none", onUpdate: () => render(clock.t) }, 0);
      tl.fromTo("#po-one", { opacity: 0, filter: "blur(6px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.16, ease: "power4.out" }, M.one - 0.1);
      tl.to("#po-one", { opacity: 0, duration: 0.18, ease: "power2.in" }, M.becomes + 0.6);
      tl.fromTo("#po-num", { opacity: 0, scale: 0.8, transformOrigin: "540px 300px" }, { opacity: 1, scale: 1, duration: 0.4, ease: "back.out(1.5)" }, M.sixteen);
      tl.fromTo("#po-sub", { opacity: 0, filter: "blur(6px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.18, ease: "power4.out" }, M.sixteen + 0.2);
      tl.fromTo("#po-foot", { opacity: 0, filter: "blur(6px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.18, ease: "power4.out" }, M.becomes + 0.5);
      render(0);
      window.__timelines["payoff"] = tl;
    })();
  </script>
</template>
"""

# ------------------------------------------------------------------ claim
CLAIM = """<template>
  <style>
    #root { position: absolute; inset: 0; background: #E8EDF1; overflow: hidden; }
    #cl-svg { position: absolute; inset: 0; }
    .cl-lab { position: absolute; font-family: Inter; line-height: 1.1; white-space: nowrap; }
  </style>
  <div id="root" data-composition-id="claim" data-width="1080" data-height="1920">
    <svg id="cl-svg"></svg>
    <div class="cl-lab" id="cl-warm" style="left:318px; top:628px; font-weight:900; font-size:48px; color:#0E1A24">warming</div>
    <div class="cl-lab" id="cl-boil" style="left:560px; top:546px; font-weight:900; font-size:48px; color:#B8480E">boiling</div>
    <div class="cl-lab" id="cl-boil2" style="left:560px; top:600px; width:280px; white-space:normal; font-weight:700; font-size:34px; color:#33434F">heat snaps hydrogen bonds</div>
  </div>
  <script>
    (() => {
      const k = window.Kitchen(document.getElementById("cl-svg"), "cl");
      const D = %%D%%, M = %%MARKS%%;
      // the curve redraws from cold, so the flat part reads as the answer
      const render = t => k.update(t, { u: Math.min(1, 0.15 + 0.85 * Math.min(1, t / 1.6)), boil: 1, flame: 1, flicker: true });
      const tl = gsap.timeline({ paused: true });
      const clock = { t: 0 };
      tl.fromTo(clock, { t: 0 }, { t: D, duration: D, ease: "none", onUpdate: () => render(clock.t) }, 0);
      tl.fromTo("#cl-boil", { opacity: 0, filter: "blur(6px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.16, ease: "power4.out" }, M.boiling);
      tl.fromTo("#cl-boil2", { opacity: 0, filter: "blur(6px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.18, ease: "power4.out" }, M.frees);
      tl.fromTo("#cl-warm", { opacity: 0, filter: "blur(6px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.16, ease: "power4.out" }, M.warming);
      render(0);
      window.__timelines["claim"] = tl;
    })();
  </script>
</template>
"""


# ------------------------------------------------------------------ captions (one host, every group written out)
COLOR = {"electrons": "#FFE08A", "hydrogen": "#9ED3FF", "bonds": "#9ED3FF", "heat": "#FF9A5A", "temperature": "#FF9A5A",
         "hundred": "#FF9A5A", "degrees": "#FF9A5A", "climbs": "#FF9A5A", "negative": "#FFFFFF", "positive": "#FFFFFF"}
def caption_groups():
    groups = []
    for vid in ["hook", "zoom", "molecule", "charge", "hbonds", "heat", "stop", "free", "payoff", "claim"]:
        ws = LINES[vid]["words"]; cur = []
        for i, w in enumerate(ws):
            cur.append(w)
            chars = sum(len(x["text"]) for x in cur)
            brk = re.search(r"[,.;:?!]$", w["text"]) or len(cur) >= 3 or (len(cur) == 2 and chars > 16)
            if brk or i == len(ws) - 1: groups.append(cur); cur = []
    out = []
    for gi, g in enumerate(groups):
        start = g[0]["start"] - 0.05
        nxt = groups[gi + 1][0]["start"] - 0.05 if gi + 1 < len(groups) else FILM
        end = min(nxt, g[-1]["end"] + 0.35)
        out.append((round(start, 3), round(end, 3), g))
    return out


def captions_html():
    gs = caption_groups(); divs, tw = [], []
    for n, (a, b, g) in enumerate(gs):
        words = []
        for w in g:
            key = re.sub(r"[^a-z]", "", w["text"].lower())
            col = COLOR.get(key)
            txt = html.escape(w["text"])
            words.append(f'<span style="color:{col}">{txt}</span>' if col else txt)
        divs.append(f'    <div class="cap" id="cap{n}">{" ".join(words)}</div>')
        tw.append(f'      show("#cap{n}", {a}, {b});')
    return f"""<template>
  <style>
    #root {{ position: absolute; inset: 0; pointer-events: none; }}
    .cap {{ position: absolute; left: 0; width: 1080px; top: 1196px; padding: 0 90px; text-align: center; font-family: Inter; font-weight: 900;
           font-size: 72px; line-height: 1.12; color: #FFFFFF; paint-order: stroke fill; -webkit-text-stroke: 14px #0B1620; letter-spacing: -0.01em; }}
  </style>
  <div id="root" data-composition-id="captions" data-width="1080" data-height="1920">
{chr(10).join(divs)}
  </div>
  <script>
    (() => {{
      const tl = gsap.timeline({{ paused: true }});
      const show = (sel, a, b) => {{
        tl.set(sel, {{ opacity: 0, visibility: "hidden" }}, 0);
        tl.set(sel, {{ visibility: "visible" }}, a);
        tl.fromTo(sel, {{ opacity: 0, scale: 0.94, transformOrigin: "540px 1240px" }}, {{ opacity: 1, scale: 1, duration: 0.1, ease: "expo.out" }}, a);
        tl.to(sel, {{ opacity: 0, duration: 0.08, ease: "power2.in" }}, b - 0.08);
        tl.set(sel, {{ opacity: 0, visibility: "hidden" }}, b);
      }};
{chr(10).join(tw)}
      window.__timelines["captions"] = tl;
    }})();
  </script>
</template>
"""


# ------------------------------------------------------------------ index
def host(cid, a, b, track, kind="graphics"):
    return (f'      <div id="{cid}" data-composition-id="{cid}" data-composition-src="compositions/{cid}.html" data-start="{a}" '
            f'data-duration="{round(b - a, 3)}" data-track-index="{track}" data-track-kind="{kind}" data-width="1080" data-height="1920"></div>')


def audio(aid, src, start, d, vol, track, extra=""):
    return f'      <audio id="{aid}" src="{src}" data-start="{round(start, 3)}" data-duration="{round(d, 3)}" data-volume="{vol}" data-track-index="{track}"{extra}></audio>'


def index_html(audio_lines):
    hosts = [host(k, *SC[k], 1) for k in ["hook", "zoom", "world", "payoff", "claim"]] + [host("captions", 0, FILM, 2, "captions")]
    return f"""<!doctype html>
<html lang="en" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="lib/gsap.min.js"></script>
    <script src="lib/water2d.js"></script>
    <script src="lib/kitchen.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1080px; height: 1920px; overflow: hidden; background: #E8EDF1; }}
      #root {{ width: 100%; height: 100%; font-family: Inter, sans-serif; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{FILM}" data-width="1080" data-height="1920">
{chr(10).join(hosts)}
{chr(10).join(audio_lines)}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
"""


if __name__ == "__main__":
    W0 = SC["world"][0]
    wm = dict(
        oxygen=word("molecule", "oxygen"), hydrogens=word("molecule", "hydrogens"), sharing=word("molecule", "sharing"),
        electrons=word("molecule", "electrons"), pulls=word("charge", "pulls"), harder=word("charge", "harder"),
        negative=word("charge", "negative"), positive=word("charge", "positive"),
        pull0=LINES["hbonds"]["start"] - 0.25, hb=word("hbonds", "hydrogen") - 0.1, attract=word("hbonds", "attract"),
        heat=LINES["heat"]["start"], hundred=word("stop", "hundred"), stops=word("stop", "stops"),
        free0=LINES["free"]["start"], snap=word("free", "snapping") - 0.1, free=word("free", "setting"),
    )
    wm["intact"] = wm["free"] - 0.9
    wm = {k: round(v - W0, 3) for k, v in wm.items()}
    P0 = SC["payoff"][0]
    pm = {k: round(v - P0, 3) for k, v in dict(one=word("payoff", "one"), becomes=word("payoff", "becomes"), sixteen=word("payoff", "sixteen")).items()}
    C0 = SC["claim"][0]
    cm = {k: round(v - C0, 3) for k, v in dict(boiling=word("claim", "boiling"), frees=word("claim", "frees"), warming=word("claim", "warming")).items()}
    files = dict(hook=fill(HOOK, D=dur("hook")), zoom=fill(ZOOM, D=dur("zoom")),
                 world=fill(WORLD, D=dur("world"), MARKS=json.dumps(wm)),
                 payoff=fill(PAYOFF, D=dur("payoff"), MARKS=json.dumps(pm)),
                 claim=fill(CLAIM, D=dur("claim"), MARKS=json.dumps(cm)), captions=captions_html())
    for k, v in files.items(): open(f"{ROOT}/compositions/{k}.html", "w").write(v)
    aud = json.load(open(f"{ROOT}/audio_cues.json")) if len(sys.argv) > 2 and sys.argv[2] == "--audio" else []
    lines = [audio(a["id"], a["src"], a["start"], a["dur"], a["vol"], a["track"], a.get("extra", "")) for a in aud]
    open(f"{ROOT}/index.html", "w").write(index_html(lines))
    print("world marks", wm); print("payoff", pm, "claim", cm); print("captions", len(caption_groups()), "groups")
