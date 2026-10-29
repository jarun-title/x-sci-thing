// Shared drawing code for the molecule and atom scenes.
// Every draw is a pure function of the time it is given; all randomness is seeded.
(function () {
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, k) => a + (b - a) * k;
  function rng(s) { return () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  const R = rng(7);
  const gauss = () => { let u = 0, v = 0; while (!u) u = R(); while (!v) v = R(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
  const mixRGB = (a, b, k) => `rgb(${a.map((v, i) => Math.round(lerp(v, b[i], k))).join(',')})`;

  function sprite(r, stops) {
    const c = document.createElement('canvas'), s = Math.ceil(r * 4);
    c.width = c.height = s; const g = c.getContext('2d');
    const gr = g.createRadialGradient(s * .38, s * .36, s * .02, s / 2, s / 2, s / 2);
    stops.forEach(([o, col]) => gr.addColorStop(o, col));
    g.fillStyle = gr; g.beginPath(); g.arc(s / 2, s / 2, s / 2, 0, 7); g.fill(); return c;
  }
  function soft(rgb) {
    const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d');
    const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, `rgba(${rgb},0.9)`); gr.addColorStop(1, `rgba(${rgb},0)`);
    g.fillStyle = gr; g.fillRect(0, 0, 128, 128); return c;
  }
  const SPR = {
    O: sprite(22, [[0, '#ffc2b3'], [.35, '#e2584a'], [1, '#7a1d1a']]),
    OH: sprite(22, [[0, '#ffe2b8'], [.35, '#ff8a3c'], [1, '#8a3510']]),
    H: sprite(13, [[0, '#ffffff'], [.5, '#e8edf2'], [1, '#8a97a6']]),
    P: sprite(7, [[0, '#ffb3a6'], [.5, '#e2584a'], [1, '#8a2420']]),
    N: sprite(7, [[0, '#e9eef3'], [.5, '#9aa6b2'], [1, '#4d5866']]),
    glow: soft('255,140,50'),
  };

  // ---------- molecules (1280x720 design space, scaled to the canvas) ----------
  const SP = 92, HALF = 104.5 / 2 * Math.PI / 180, OH = 34, MOL = [];
  for (let row = -13; row <= 13; row++) for (let col = -22; col <= 22; col++) {
    const c = row === 0 && col === 0;
    MOL.push({
      bx: col * SP + (row & 1 ? SP / 2 : 0) + (c ? 0 : (R() - .5) * 36), by: row * SP * .87 + (c ? 0 : (R() - .5) * 36),
      a0: c ? -Math.PI / 2 : R() * Math.PI * 2, p: [R() * 7, R() * 7, R() * 7], fr: .7 + R() * .6,
      vx: (R() - .5) * 1.6, vy: -(.5 + R() * 1.1), spin: (R() - .5) * 2, c,
    });
  }
  MOL.forEach((m, i) => { let b = -1, bd = 1e9; MOL.forEach((n, j) => { if (i === j) return; const d = (m.bx - n.bx) ** 2 + (m.by - n.by) ** 2; if (d < bd) { bd = d; b = j; } }); m.nb = b; });
  const CENTER = MOL.findIndex(m => m.c);

  // tau: agitation clock. Heat speeds it up; integrated in closed form for a linear heat ramp
  function state(m, tau, h, v) {
    const amp = 4 + 16 * h, V = 1500 * Math.pow(v, 1.8);
    const x = m.bx + amp * Math.sin(tau * 1.7 * m.fr + m.p[0]) + m.vx * V;
    const y = m.by + amp * Math.cos(tau * 1.3 * m.fr + m.p[1]) + m.vy * V;
    const a = m.a0 + (.12 + .6 * h) * Math.sin(tau * 1.1 * m.fr + m.p[2]) + m.spin * v * v * 8;
    return { x, y, a, h1x: x + OH * Math.cos(a - HALF), h1y: y + OH * Math.sin(a - HALF), h2x: x + OH * Math.cos(a + HALF), h2y: y + OH * Math.sin(a + HALF) };
  }

  // opts: { tau, heat, vapor, zoom, bondAlpha }
  function drawMolecules(ctx, W, H, o) {
    const h = o.heat || 0, v = o.vapor || 0, s = W / 1280;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, W, H);
    ctx.setTransform(s, 0, 0, s, 0, 0);
    const c = state(MOL[CENTER], o.tau, h, 0);
    ctx.save(); ctx.translate(640, 360); ctx.scale(o.zoom, o.zoom); ctx.translate(-c.x, -c.y);
    const vw = 640 / o.zoom + 80, vh = 360 / o.zoom + 80;
    const st = MOL.map(m => state(m, o.tau, h, v));
    const ba = (o.bondAlpha == null ? 1 : o.bondAlpha) * (1 - .75 * h) * (1 - clamp(v * 3));
    if (ba > .01) {
      ctx.setLineDash([5, 6]); ctx.lineWidth = 2; ctx.strokeStyle = `rgba(150,215,245,${.5 * ba})`; ctx.beginPath();
      MOL.forEach((m, i) => { const a = st[i], n = st[m.nb]; if (Math.abs(a.x - c.x) > vw || Math.abs(a.y - c.y) > vh) return; ctx.moveTo(a.h1x, a.h1y); ctx.lineTo(n.x, n.y); });
      ctx.stroke(); ctx.setLineDash([]);
    }
    MOL.forEach((m, i) => {
      const a = st[i]; if (Math.abs(a.x - c.x) > vw || Math.abs(a.y - c.y) > vh) return;
      if (h > .05) { ctx.globalAlpha = .5 * h; ctx.drawImage(SPR.glow, a.x - 48, a.y - 48, 96, 96); ctx.globalAlpha = 1; }
      ctx.strokeStyle = 'rgba(230,236,243,0.5)'; ctx.lineWidth = 6; ctx.beginPath();
      ctx.moveTo(a.h1x, a.h1y); ctx.lineTo(a.x, a.y); ctx.lineTo(a.h2x, a.h2y); ctx.stroke();
      ctx.drawImage(SPR.H, a.h1x - 13, a.h1y - 13, 26, 26); ctx.drawImage(SPR.H, a.h2x - 13, a.h2y - 13, 26, 26);
      ctx.drawImage(SPR.O, a.x - 22, a.y - 22, 44, 44);
      if (h > 0) { ctx.globalAlpha = h; ctx.drawImage(SPR.OH, a.x - 22, a.y - 22, 44, 44); ctx.globalAlpha = 1; }
    });
    ctx.restore();
  }

  // screen position (in canvas px) of things around the centre molecule, for DOM labels
  function centerGeometry(W, tau) {
    const s = W / 1280, c = state(MOL[CENTER], tau, 0, 0), n = state(MOL[MOL[CENTER].nb], tau, 0, 0);
    const sx = x => (640 + (x - c.x)) * s, sy = y => (360 + (y - c.y)) * s;
    return { o: [sx(c.x), sy(c.y)], h1: [sx(c.h1x), sy(c.h1y)], h2: [sx(c.h2x), sy(c.h2y)], bondMid: [sx((c.h1x + n.x) / 2), sy((c.h1y + n.y) / 2)] };
  }

  // ---------- atom ----------
  const CLOUD = [];
  for (let i = 0; i < 420; i++) CLOUD.push([gauss() * 26, gauss() * 26, 0, R()]);
  for (let i = 0; i < 700; i++) { const r = 112 + gauss() * 24, th = R() * 7; CLOUD.push([r * Math.cos(th), r * Math.sin(th) * .96, 1, R()]); }
  [[0, 1], [Math.PI / 3, .78], [2 * Math.PI / 3, .55]].forEach(([ang, len]) => {
    for (let i = 0; i < 520; i++) { const d = (86 + gauss() * 26) * (R() < .5 ? -1 : 1) * len, w = gauss() * (18 + Math.abs(d) * .22);
      CLOUD.push([d * Math.cos(ang) - w * Math.sin(ang), d * Math.sin(ang) + w * Math.cos(ang), 2, R()]); }
  });
  const NUC = []; for (let i = 0; i < 16; i++) { const r = 5.2 * Math.sqrt(i + .5), th = i * 2.39996; NUC.push([r * Math.cos(th), r * Math.sin(th), i % 2 === 0]); }
  const KC = [[190, 235, 255], [120, 200, 245], [110, 160, 255]], HOT = [255, 170, 90];

  // opts: { t, heat, scale }
  function drawAtom(ctx, W, H, o) {
    const h = o.heat || 0, s = W / 1280, t = o.t;
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, W, H);
    ctx.setTransform(s, 0, 0, s, 0, 0);
    ctx.save(); ctx.translate(640, 360); ctx.scale(o.scale, o.scale); ctx.rotate(t * .12);
    ctx.globalCompositeOperation = 'lighter';
    const jit = 2 + 7 * h, ex = 1 + .12 * h;
    for (let i = 0; i < CLOUD.length; i++) {
      const p = CLOUD[i], f = .45 + .55 * Math.abs(Math.sin(p[3] * 50 + t * (5 + 10 * h)));
      ctx.fillStyle = mixRGB(KC[p[2]], HOT, h * .75).replace('rgb', 'rgba').replace(')', `,${.6 * f})`);
      ctx.fillRect(p[0] * ex + Math.sin(p[3] * 90 + t * 9) * jit, p[1] * ex + Math.cos(p[3] * 70 + t * 8) * jit, 2.2, 2.2);
    }
    ctx.globalCompositeOperation = 'source-over';
    const sh = 1.2 * h;
    NUC.forEach((n, i) => ctx.drawImage(n[2] ? SPR.P : SPR.N, n[0] - 7 + Math.sin(t * 30 + i) * sh, n[1] - 7 + Math.cos(t * 27 + i) * sh, 14, 14));
    ctx.restore();
  }

  window.H2O = { drawMolecules, drawAtom, centerGeometry, clamp, lerp, mixRGB };
})();
