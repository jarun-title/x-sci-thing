// Liquid water in 2D, in ångström units. Everything is a pure function of time; randomness is seeded.
// - every molecule is a full H2O: O + two H at 104.5°, O–H 0.96 Å
// - neighbours sit ~2.8 Å apart (O to O), as in liquid water
// - each hydrogen bond runs from an H of one molecule to the O of another; an O accepts at most two
(function () {
  const TAU = Math.PI * 2, HALF = (104.5 / 2) * Math.PI / 180, OH = 0.96, RO = 0.62, RH = 0.36;
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, k) => a + (b - a) * k;
  const smooth = x => x * x * (3 - 2 * x);
  function rng(s) { return () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  const R = rng(1729);
  const dir = a => [Math.cos(a), Math.sin(a)];
  const deg = d => d * Math.PI / 180;
  const SURFACE = -9.0;

  // ---------- layout ----------
  const mols = [];
  const add = (x, y, bis, fixed) => mols.push({ x, y, bis, fixed: !!fixed });
  // the hero molecule: V opening downward (screen y grows downward)
  add(0, 0, deg(90), true);
  const d1 = dir(deg(90) - HALF), d2 = dir(deg(90) + HALF);
  add(2.8 * d1[0], 2.8 * d1[1], deg(90), false);   // receives hero's H1
  add(2.8 * d2[0], 2.8 * d2[1], deg(90), false);   // receives hero's H2
  // two neighbours on the lone-pair side, each pointing one H at the hero's O
  const l1 = dir(deg(215)), l2 = dir(deg(325));
  add(2.8 * l1[0], 2.8 * l1[1], deg(35 + 52.25), true);
  add(2.8 * l2[0], 2.8 * l2[1], deg(145 - 52.25), true);
  // fill the rest of the liquid (Poisson disc, min 2.65 Å)
  for (let tries = 0; tries < 9000 && mols.length < 230; tries++) {
    const x = lerp(-14, 14, R()), y = lerp(SURFACE + 0.5, 19, R());
    if (mols.every(m => (m.x - x) ** 2 + (m.y - y) ** 2 > 2.65 * 2.65)) add(x, y, R() * TAU, false);
  }
  const N = mols.length;
  const hpos = (m, bis, k) => { const a = bis + (k === 0 ? -HALF : HALF); return [m.x + OH * Math.cos(a), m.y + OH * Math.sin(a)]; };
  // pick each free molecule's orientation so its two H point at neighbouring O atoms
  function aimScore(i, bis, accepted) {
    let s = 0, targets = [];
    for (let k = 0; k < 2; k++) {
      const a = bis + (k === 0 ? -HALF : HALF); let best = null, be = 1e9;
      for (let j = 0; j < N; j++) {
        if (j === i || (accepted[j] || 0) >= 2 || targets.includes(j)) continue;
        const dx = mols[j].x - mols[i].x, dy = mols[j].y - mols[i].y, d = Math.hypot(dx, dy);
        if (d < 2.3 || d > 3.4) continue;
        let e = Math.abs(((Math.atan2(dy, dx) - a) % TAU + TAU + Math.PI) % TAU - Math.PI) * 180 / Math.PI;
        if (e < 30 && e < be) { be = e; best = j; }
      }
      if (best !== null) { s += 1 - be / 30; targets.push(best); } else targets.push(null);
    }
    return { s, targets };
  }
  const accepted = {}, hb = [];
  const order = [...Array(N).keys()].sort((a, b) => (mols[a].fixed ? -1 : 0) - (mols[b].fixed ? -1 : 0) || a - b);
  for (const i of order) {
    let bestBis = mols[i].bis, best = aimScore(i, mols[i].bis, accepted);
    if (!mols[i].fixed) for (let c = 0; c < 72; c++) { const b = c * TAU / 72, r = aimScore(i, b, accepted); if (r.s > best.s + 1e-6) { best = r; bestBis = b; } }
    mols[i].bis = bestBis;
    best.targets.forEach((j, k) => { if (j !== null) { hb.push({ i, k, j, ph: R() * TAU, s: R(), hero: i === 0 || j === 0 }); accepted[j] = (accepted[j] || 0) + 1; } });
  }
  mols.forEach(m => { m.ph = [R() * TAU, R() * TAU, R() * TAU]; m.fr = 0.75 + 0.5 * R(); m.spin = (R() - 0.5) * 2.2; m.lat = (R() - 0.5) * 1.6; });

  // escapers: molecules within ~6 Å of the surface, released top-first across the "free" window
  const esc = mols.map((m, i) => i).filter(i => i > 4 && mols[i].y < SURFACE + 6.2 && Math.abs(mols[i].x) < 10.5);
  esc.sort((a, b) => mols[a].y - mols[b].y || Math.abs(mols[a].x) - Math.abs(mols[b].x));
  const release = {};
  // hero escapee for the "O–H bonds stay intact" label: the escaper nearest the frame centre line
  const showcase = esc.slice().sort((a, b) => Math.abs(mols[a].x) - Math.abs(mols[b].x))[0];

  // ---------- state at time t ----------
  // P: { tau, T (°C), relStart, relEnd } — tau: agitation clock, T drives amplitude, release window in the same clock as t
  function setRelease(t0, t1) {
    esc.forEach((i, n) => { release[i] = lerp(t0, t1, n / Math.max(1, esc.length - 1)) + (R() - 0.5) * 0.15; });
    release[showcase] = t0 + 0.15;
  }
  function pose(i, t, P) {
    const m = mols[i], amp = (0.035 + 0.22 * clamp((P.T - 20) / 80)) * (i === 0 ? P.heroCalm : 1);
    let x = m.x + amp * Math.sin(P.tau * 1.7 * m.fr + m.ph[0]), y = m.y + amp * Math.cos(P.tau * 1.3 * m.fr + m.ph[1]);
    let bis = m.bis + (0.05 + 0.25 * clamp((P.T - 20) / 80)) * Math.sin(P.tau * 1.1 * m.fr + m.ph[2]) * (i === 0 ? P.heroCalm : 1);
    const r = release[i];
    if (r !== undefined && t > r) {
      const u = t - r;
      if (i === showcase) { y -= 1.4 * u; x += 0.25 * u; bis += 0.5 * u; }  // slower, so its label can be read
      else { y -= 3.2 * u + 2.2 * u * u; x += m.lat * u; bis += m.spin * u; }
    }
    return { x, y, bis, h1: hposXY(x, y, bis, 0), h2: hposXY(x, y, bis, 1) };
  }
  const hposXY = (x, y, bis, k) => { const a = bis + (k === 0 ? -HALF : HALF); return [x + OH * Math.cos(a), y + OH * Math.sin(a)]; };

  // bond visibility: 1 = drawn, 0 = gone; snapping returns k in (0,1)
  function bondState(b, t, P) {
    const ri = release[b.i], rj = release[b.j];
    const r = Math.min(ri === undefined ? 1e9 : ri, rj === undefined ? 1e9 : rj) - 0.12;
    if (t > r) return { alpha: 0, snap: t < r + 0.3 ? (t - r) / 0.3 : -1 };
    let alpha = P.bondAlpha;
    if (!b.hero) {  // the network breaks and re-forms more often as it heats
      const thr = lerp(1.3, 0.35, clamp((P.T - 20) / 80) * P.flicker);
      alpha *= 1 - smooth(clamp((Math.sin(P.tau * 0.9 + b.ph) - thr) / 0.18 + 0.5));
    }
    return { alpha, snap: -1 };
  }

  // ---------- drawing ----------
  const COL = { O: "#E5484D", Ohi: "#FF8E8A", Olo: "#A9262B", H: "#F3F6F8", Hhi: "#FFFFFF", Hlo: "#B9C4CC", hb: "#9ED3FF", pair: "#FFE08A", heat: "#FF7A2F" };
  function ball(ctx, x, y, r, base, hi, lo) {
    const g = ctx.createRadialGradient(x - 0.35 * r, y - 0.35 * r, 0.05 * r, x, y, r);
    g.addColorStop(0, hi); g.addColorStop(0.55, base); g.addColorStop(1, lo);
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill();
  }
  // cam: { cx, cy, s } with s in px per Å; screen centre at (540, 960)
  const W = 1080, H = 1920;
  const sx = (cam, x) => 540 + (x - cam.cx) * cam.s, sy = (cam, y) => 960 + (y - cam.cy) * cam.s;

  function drawGround(ctx, cam, t, P) {
    const ys = sy(cam, SURFACE + (P.surfWave || 0) * 0);
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, "#0F4C75"); g.addColorStop(1, "#0A3150");
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    // caustic light bands, 5% white, drifting
    ctx.save(); ctx.globalAlpha = 0.05; ctx.fillStyle = "#FFFFFF";
    for (let k = 0; k < 6; k++) {
      const x0 = ((k * 230 + t * 18) % 1500) - 300;
      ctx.beginPath(); ctx.moveTo(x0, 0); ctx.lineTo(x0 + 90, 0); ctx.lineTo(x0 + 90 - 520, H); ctx.lineTo(x0 - 520, H); ctx.fill();
    }
    ctx.restore();
    if (P.air !== false && ys > -40) {  // air above the surface
      const ga = ctx.createLinearGradient(0, 0, 0, Math.max(1, ys));
      ga.addColorStop(0, "#E4EFF7"); ga.addColorStop(1, "#C6DDEE");
      ctx.fillStyle = ga; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(W, 0);
      for (let x = W; x >= 0; x -= 20) ctx.lineTo(x, ys + Math.sin(x * 0.012 + t * 2.1) * 6 * (1 + 2 * (P.boil || 0)));
      ctx.closePath(); ctx.fill();
      ctx.strokeStyle = "rgba(255,255,255,0.85)"; ctx.lineWidth = 3; ctx.beginPath();
      for (let x = 0; x <= W; x += 20) { const yy = ys + Math.sin(x * 0.012 + t * 2.1) * 6 * (1 + 2 * (P.boil || 0)); x ? ctx.lineTo(x, yy) : ctx.moveTo(x, yy); }
      ctx.stroke();
    }
  }

  function drawHeat(ctx, t, k) {  // heat coming in from the burner below: a warm edge and rising chevrons
    if (k <= 0) return;
    const g = ctx.createLinearGradient(0, H, 0, H - 420);
    g.addColorStop(0, `rgba(255,122,47,${0.42 * k})`); g.addColorStop(1, "rgba(255,122,47,0)");
    ctx.fillStyle = g; ctx.fillRect(0, H - 420, W, 420);
    ctx.save(); ctx.fillStyle = COL.heat;
    for (let c = 0; c < 7; c++) for (let r = 0; r < 3; r++) {
      const per = 1.4, ph = ((t / per + r / 3 + c * 0.13) % 1);
      const x = 90 + c * 150, y = H - 40 - ph * 360;
      ctx.globalAlpha = k * 0.8 * Math.sin(Math.PI * ph);
      ctx.beginPath(); ctx.moveTo(x - 22, y + 14); ctx.lineTo(x, y - 10); ctx.lineTo(x + 22, y + 14); ctx.lineTo(x + 14, y + 14); ctx.lineTo(x, y + 2); ctx.lineTo(x - 14, y + 14); ctx.closePath(); ctx.fill();
    }
    ctx.restore();
  }

  function drawBonds(ctx, cam, t, P, poses) {
    ctx.save(); ctx.lineCap = "round";
    for (const b of hb) {
      const st = bondState(b, t, P);
      const pi = poses[b.i], pj = poses[b.j]; if (!pi || !pj) continue;
      const h = b.k === 0 ? pi.h1 : pi.h2;
      // start at the H surface, end at the O surface
      let dx = pj.x - h[0], dy = pj.y - h[1], d = Math.hypot(dx, dy); if (d > 3.6 && st.snap < 0) continue;
      dx /= d; dy /= d;
      const a = [h[0] + dx * RH, h[1] + dy * RH], o = [pj.x - dx * RO, pj.y - dy * RO];
      const A = [sx(cam, a[0]), sy(cam, a[1])], B = [sx(cam, o[0]), sy(cam, o[1])];
      const lw = Math.max(2, 0.06 * cam.s * P.bondScale);
      ctx.lineWidth = lw; ctx.setLineDash([lw * 1.6, lw * 1.8]); ctx.strokeStyle = COL.hb;
      if (st.snap >= 0) {  // snap: both halves pull back from the midpoint, brief orange tick where it broke
        const k = st.snap, M = [(A[0] + B[0]) / 2, (A[1] + B[1]) / 2];
        ctx.globalAlpha = 1 - k;
        ctx.beginPath(); ctx.moveTo(A[0], A[1]); ctx.lineTo(lerp(M[0], A[0], k), lerp(M[1], A[1], k));
        ctx.moveTo(B[0], B[1]); ctx.lineTo(lerp(M[0], B[0], k), lerp(M[1], B[1], k)); ctx.stroke();
        if (k < 0.35) { ctx.setLineDash([]); ctx.strokeStyle = COL.heat; ctx.globalAlpha = 1; ctx.lineWidth = lw * 1.2;
          const s = 10 + 0.08 * cam.s; ctx.beginPath(); ctx.moveTo(M[0] - s, M[1] - s); ctx.lineTo(M[0] + s, M[1] + s); ctx.moveTo(M[0] + s, M[1] - s); ctx.lineTo(M[0] - s, M[1] + s); ctx.stroke(); }
      } else if (st.alpha > 0.01) {
        ctx.globalAlpha = st.alpha * (b.hero ? P.heroBondAlpha : 1);
        ctx.beginPath(); ctx.moveTo(A[0], A[1]); ctx.lineTo(B[0], B[1]); ctx.stroke();
      }
    }
    ctx.restore();
  }

  function drawMolecule(ctx, cam, p, alpha) {
    if (alpha <= 0) return;
    ctx.save(); ctx.globalAlpha = alpha;
    const ox = sx(cam, p.x), oy = sy(cam, p.y);
    [p.h1, p.h2].forEach(h => ball(ctx, sx(cam, h[0]), sy(cam, h[1]), RH * cam.s, COL.H, COL.Hhi, COL.Hlo));
    ball(ctx, ox, oy, RO * cam.s, COL.O, COL.Ohi, COL.Olo);
    ctx.restore();
  }

  // the hero close-up: electron density shared between the three atoms; k = how far oxygen has pulled it
  const off = document.createElement("canvas"); off.width = W; off.height = H; const octx = off.getContext("2d");
  function drawCloud(ctx, cam, p, a, k) {
    if (a <= 0) return;
    octx.clearRect(0, 0, W, H); octx.fillStyle = "#9ED3FF";
    const ro = (1.17 + 0.14 * k) * cam.s, rh = (0.78 - 0.16 * k) * cam.s;
    octx.beginPath(); octx.arc(sx(cam, p.x), sy(cam, p.y), ro, 0, TAU); octx.fill();
    [p.h1, p.h2].forEach(h => { octx.beginPath(); octx.arc(sx(cam, h[0]), sy(cam, h[1]), rh, 0, TAU); octx.fill(); });
    // the bridge between the clouds, so it reads as one shared cloud
    [p.h1, p.h2].forEach(h => {
      const ax = sx(cam, p.x), ay = sy(cam, p.y), bx = sx(cam, h[0]), by = sy(cam, h[1]);
      const nx = -(by - ay), ny = bx - ax, L = Math.hypot(nx, ny), w = 0.62 * cam.s;
      octx.beginPath(); octx.moveTo(ax + nx / L * w, ay + ny / L * w); octx.lineTo(bx + nx / L * w * 0.8, by + ny / L * w * 0.8);
      octx.lineTo(bx - nx / L * w * 0.8, by - ny / L * w * 0.8); octx.lineTo(ax - nx / L * w, ay - ny / L * w); octx.fill();
    });
    ctx.save(); ctx.globalAlpha = 0.2 * a; ctx.drawImage(off, 0, 0);
    // denser around oxygen as it pulls the electrons in
    ctx.globalAlpha = 0.16 * a * k; ctx.fillStyle = "#9ED3FF"; ctx.beginPath(); ctx.arc(sx(cam, p.x), sy(cam, p.y), 0.95 * ro, 0, TAU); ctx.fill();
    ctx.restore();
  }
  // shared pairs on each O–H bond (slide toward O as k grows) and two lone pairs on O
  function drawPairs(ctx, cam, p, a, k) {
    if (a <= 0) return;
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = COL.pair; ctx.strokeStyle = "rgba(60,40,0,0.5)"; ctx.lineWidth = 2;
    const r = 0.042 * cam.s, sep = 0.085 * cam.s;
    const dot = (x, y) => { ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill(); ctx.stroke(); };
    [0, 1].forEach(n => {
      const h = n === 0 ? p.h1 : p.h2, f = lerp(0.52, 0.30, k) / OH;  // fraction along O→H
      const bx = lerp(p.x, h[0], f * OH), by = lerp(p.y, h[1], f * OH);
      const ux = (h[1] - p.y) / OH, uy = -(h[0] - p.x) / OH;  // perpendicular
      dot(sx(cam, bx) + ux * sep, sy(cam, by) + uy * sep); dot(sx(cam, bx) - ux * sep, sy(cam, by) - uy * sep);
    });
    [-1, 1].forEach(sgn => {
      const ang = p.bis + Math.PI + sgn * deg(55), rr = RO + 0.16;
      const cx = p.x + rr * Math.cos(ang), cy = p.y + rr * Math.sin(ang), ux = -Math.sin(ang), uy = Math.cos(ang);
      dot(sx(cam, cx) + ux * sep, sy(cam, cy) + uy * sep); dot(sx(cam, cx) - ux * sep, sy(cam, cy) - uy * sep);
    });
    ctx.restore();
  }

  function render(ctx, cam, t, P) {
    const poses = mols.map((m, i) => pose(i, t, P));
    drawGround(ctx, cam, t, P);
    drawHeat(ctx, t, P.heat || 0);
    if (P.tile > 0) {  // far out, the liquid repeats so the frame is full of water (period 28 x 27.5 Å)
      ctx.save(); ctx.globalAlpha = P.tile;
      for (const ox of [-28, 0, 28]) for (const oy of [-27.5, 0, 27.5]) {
        if (!ox && !oy) continue;
        const shifted = poses.map(p => ({ x: p.x + ox, y: p.y + oy, bis: p.bis, h1: [p.h1[0] + ox, p.h1[1] + oy], h2: [p.h2[0] + ox, p.h2[1] + oy] }));
        drawBonds(ctx, cam, t, P, shifted);
        shifted.forEach(p => { const X = sx(cam, p.x), Y = sy(cam, p.y); if (X > -60 && X < W + 60 && Y > -60 && Y < H + 60) drawMolecule(ctx, cam, p, P.crowd); });
      }
      ctx.restore();
    }
    drawBonds(ctx, cam, t, P, poses);
    if (P.cloud > 0) drawCloud(ctx, cam, poses[0], P.cloud, P.pull);
    poses.forEach((p, i) => {
      // molecules other than the hero fade in as the camera pulls back
      const a = i === 0 ? 1 : P.crowd;
      const X = sx(cam, p.x), Y = sy(cam, p.y), m = 1.6 * cam.s;
      if (X < -m || X > W + m || Y < -m || Y > H + m) return;
      drawMolecule(ctx, cam, p, a);
    });
    if (P.pairs > 0) drawPairs(ctx, cam, poses[0], P.pairs, P.pull);
    return poses;
  }

  window.Water2D = { render, mols, hb, esc, showcase, setRelease, release, SURFACE, RO, RH, OH, HALF, sx, sy, clamp, lerp, smooth };
})();
