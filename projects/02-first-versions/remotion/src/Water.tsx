import React from 'react';
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, random, Easing } from 'remotion';

const W = 1280, H = 720;
const C = { bg: '#0a0f1c', water: '#3f9fd6', deep: '#0f3d63', o: '#e2584a', h: '#f2f4f7', hot: '#ff9a3c', ink: '#e8eef4', mute: '#8da0b3' };
const clamp = { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' } as const;
const io = Easing.inOut(Easing.cubic);
const mix = (a: string, b: string, k: number) => {
  const p = (s: string) => [1, 3, 5].map(i => parseInt(s.slice(i, i + 2), 16));
  const x = p(a), y = p(b);
  return `rgb(${x.map((v, i) => Math.round(v + (y[i] - v) * k)).join(',')})`;
};

// ---------- molecules ----------
const HALF = (104.5 / 2) * Math.PI / 180, OH = 34;
type Mol = { bx: number; by: number; a0: number; ph: number[]; vx: number; vy: number; spin: number; c: boolean };
const MOLS: Mol[] = [];
for (let r = -6; r <= 6; r++) for (let c = -10; c <= 10; c++) {
  const ctr = r === 0 && c === 0, s = `${r}:${c}`;
  MOLS.push({
    bx: c * 100 + (r & 1 ? 50 : 0) + (ctr ? 0 : (random('x' + s) - .5) * 36),
    by: r * 88 + (ctr ? 0 : (random('y' + s) - .5) * 36),
    a0: ctr ? -Math.PI / 2 : random('a' + s) * Math.PI * 2,
    ph: [0, 1, 2].map(i => random(`p${i}${s}`) * 7),
    vx: (random('vx' + s) - .5) * 1.6, vy: -(.5 + random('vy' + s)), spin: (random('sp' + s) - .5) * 2, c: ctr,
  });
}

const Molecule: React.FC<{ m: Mol; t: number; h: number; v: number }> = ({ m, t, h, v }) => {
  const amp = 4 + 16 * h, tau = t * (1 + 3 * h);
  const V = 1500 * Math.pow(v, 1.8);
  const x = m.bx + amp * Math.sin(tau * 1.7 + m.ph[0]) + m.vx * V;
  const y = m.by + amp * Math.cos(tau * 1.3 + m.ph[1]) + m.vy * V;
  const a = m.a0 + (.12 + .6 * h) * Math.sin(tau * 1.1 + m.ph[2]) + m.spin * v * v * 8;
  const h1 = [OH * Math.cos(a - HALF), OH * Math.sin(a - HALF)], h2 = [OH * Math.cos(a + HALF), OH * Math.sin(a + HALF)];
  return (
    <g transform={`translate(${x} ${y})`}>
      {h > .05 && <circle r={46} fill="url(#glow)" opacity={h * .6} />}
      <line x1={0} y1={0} x2={h1[0]} y2={h1[1]} stroke="#c9d3dd" strokeWidth={7} strokeLinecap="round" />
      <line x1={0} y1={0} x2={h2[0]} y2={h2[1]} stroke="#c9d3dd" strokeWidth={7} strokeLinecap="round" />
      <circle cx={h1[0]} cy={h1[1]} r={13} fill="url(#gH)" />
      <circle cx={h2[0]} cy={h2[1]} r={13} fill="url(#gH)" />
      <circle r={22} fill={h > 0 ? mix(C.o, C.hot, h) : C.o} />
      <circle r={22} fill="url(#shade)" />
    </g>
  );
};

// ---------- glass ----------
const Glass: React.FC<{ t: number; level: number; steam: number; grow: number }> = ({ t, level, steam, grow }) => {
  const wl = 250 + level * 230;
  const hw = (y: number) => 140 + (112 - 140) * (y - 160) / 400;
  return (
    <g transform={`translate(640 560) scale(1 ${grow}) translate(-640 -560)`}>
      <ellipse cx={640} cy={566} rx={210} ry={24} fill={C.water} opacity={.12} />
      <path d={`M${640 - hw(wl) + 6} ${wl} L${640 + hw(wl) - 6} ${wl} L${640 + 106} ${544} L${640 - 106} ${544} Z`} fill="url(#gWater)" />
      <ellipse cx={640} cy={wl} rx={hw(wl) - 6} ry={11} fill="#9ad8f7" opacity={.6} />
      <path d={`M${640 - hw(wl) + 10} ${wl + 2} Q 640 ${wl + 16 + Math.sin(t * 4) * 4} ${640 + hw(wl) - 10} ${wl + 2}`} stroke="#d8f1ff" strokeWidth={2} fill="none" opacity={.7} />
      <path d="M500 160 L528 560 L752 560 L780 160" stroke="#dbe9f3" strokeWidth={4} fill="none" opacity={.75} strokeLinejoin="round" />
      <ellipse cx={640} cy={160} rx={140} ry={14} stroke="#dbe9f3" strokeWidth={2.5} fill="none" opacity={.65} />
      <path d="M516 190 L538 520" stroke="#fff" strokeWidth={10} opacity={.12} strokeLinecap="round" />
      {steam > 0 && [0, 1, 2, 3, 4].map(i => {
        const s = ((t * .35 + i * .2) % 1), x0 = 560 + i * 40;
        const d = `M${x0} ${wl - 20 - s * 260} q ${20 + i * 3} -40 0 -80 q ${-20 - i * 2} -40 0 -80`;
        return <path key={i} d={d} stroke="#eef4f8" strokeWidth={10 + s * 14} strokeLinecap="round" fill="none" opacity={steam * .5 * Math.sin(Math.PI * s)} filter="url(#blur)" />;
      })}
    </g>
  );
};

// ---------- atom ----------
const Atom: React.FC<{ t: number; h: number; s: number }> = ({ t, h, s }) => {
  const speed = 1 + 4 * h, col = mix('#7fd0f5', C.hot, h);
  return (
    <g transform={`translate(640 360) scale(${s})`}>
      <circle r={300} fill="url(#atomHalo)" />
      {[0, 60, 120].map((rot, i) => {
        const a = t * speed * (1.2 + i * .25) + i * 2;
        const ex = 240 * Math.cos(a), ey = 80 * Math.sin(a);
        const r = rot * Math.PI / 180;
        const x = ex * Math.cos(r) - ey * Math.sin(r), y = ex * Math.sin(r) + ey * Math.cos(r);
        return (
          <g key={rot}>
            <ellipse rx={240} ry={80} transform={`rotate(${rot})`} fill="none" stroke={col} strokeWidth={2.5} opacity={.55} />
            <circle cx={x} cy={y} r={11} fill={col} />
            <circle cx={x} cy={y} r={22} fill={col} opacity={.25} />
          </g>
        );
      })}
      {Array.from({ length: 16 }).map((_, i) => {
        const r = 6.5 * Math.sqrt(i + .5), th = i * 2.39996, sh = 2.5 * h;
        return <circle key={i} cx={r * Math.cos(th) + Math.sin(t * 30 + i) * sh} cy={r * Math.sin(th) + Math.cos(t * 27 + i) * sh} r={9} fill={i % 2 ? '#9aa6b2' : C.o} />;
      })}
    </g>
  );
};

// ---------- kinetic type ----------
const Kicker: React.FC<{ from: number; to: number; n: string; title: string; sub: string }> = ({ from, to, n, title, sub }) => {
  const f = useCurrentFrame(), { fps } = useVideoConfig();
  if (f < from || f > to) return null;
  const inS = spring({ frame: f - from, fps, config: { damping: 14, stiffness: 120 } });
  const out = interpolate(f, [to - 10, to], [1, 0], clamp);
  return (
    <div style={{ position: 'absolute', left: 56, bottom: 52, opacity: out, fontFamily: 'Inter, "DejaVu Sans", sans-serif' }}>
      <div style={{ fontFamily: '"DejaVu Sans Mono", monospace', fontSize: 15, color: '#5fb8e6', transform: `translateY(${(1 - inS) * 20}px)`, opacity: inS }}>{n} / 07</div>
      <div style={{ overflow: 'hidden' }}>
        <div style={{ fontSize: 46, fontWeight: 800, color: C.ink, letterSpacing: -1, transform: `translateY(${(1 - inS) * 60}px)` }}>{title}</div>
      </div>
      <div style={{ fontSize: 20, color: C.mute, opacity: interpolate(f - from, [8, 20], [0, 1], clamp) }}>{sub}</div>
    </div>
  );
};

const BigWord: React.FC<{ text: string; from: number; to: number; color: string }> = ({ text, from, to, color }) => {
  const f = useCurrentFrame(), { fps } = useVideoConfig();
  if (f < from || f > to) return null;
  const s = spring({ frame: f - from, fps, config: { damping: 200 } });
  const out = interpolate(f, [to - 12, to], [1, 0], clamp);
  return (
    <div style={{ position: 'absolute', right: 40, top: 10, fontSize: 220, fontWeight: 900, fontFamily: 'Inter, "DejaVu Sans", sans-serif', color: 'transparent', WebkitTextStroke: `2px ${color}`, opacity: .35 * s * out, transform: `translateX(${(1 - s) * 120}px)`, letterSpacing: -6 }}>{text}</div>
  );
};

// ---------- composition ----------
export const Water: React.FC = () => {
  const f = useCurrentFrame(), { fps } = useVideoConfig();
  const t = f / fps;
  const heat = interpolate(f, [450, 720], [0, 1], { ...clamp, easing: io });
  const vap = interpolate(f, [700, 820], [0, 1], clamp);
  const temp = 20 + 80 * heat;

  // view weights
  const glassA = f < 200 ? interpolate(f, [150, 175], [1, 0], clamp) : interpolate(f, [800, 830], [0, 1], clamp);
  const atomA = f < 450 ? interpolate(f, [340, 362], [0, 1], clamp) : interpolate(f, [500, 525], [1, 0], clamp);
  const molA = f < 400 ? Math.min(interpolate(f, [150, 175], [0, 1], clamp), interpolate(f, [340, 362], [1, 0], clamp)) : Math.min(interpolate(f, [500, 525], [0, 1], clamp), interpolate(f, [800, 830], [1, 0], clamp));

  // cameras
  const grow = spring({ frame: f, fps, config: { damping: 12, stiffness: 90 } });
  const gz = f < 400 ? Math.exp(Math.log(60) * interpolate(f, [80, 175], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) })) : Math.exp(Math.log(6) * interpolate(f, [805, 870], [1, 0], { ...clamp, easing: io }));
  const gty = f < 400 ? 430 : interpolate(f, [805, 870], [260, 370], { ...clamp, easing: io });
  const mz = f < 400
    ? Math.exp(Math.log(.35) * interpolate(f, [150, 200], [1, 0], { ...clamp, easing: Easing.out(Easing.cubic) })) * Math.exp(Math.log(7) * interpolate(f, [300, 362], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) }))
    : Math.exp(Math.log(7) * interpolate(f, [500, 545], [1, 0], { ...clamp, easing: Easing.out(Easing.cubic) })) * interpolate(f, [700, 820], [1, .6], clamp);
  const az = f < 450 ? interpolate(f, [340, 420], [.6, 1], { ...clamp, easing: Easing.out(Easing.cubic) }) : interpolate(f, [495, 525], [1, .5], clamp);

  const c = MOLS.find(m => m.c)!;
  const tau = t * (1 + 3 * heat);
  const cx = c.bx + (4 + 16 * heat) * Math.sin(tau * 1.7 + c.ph[0]), cy = c.by + (4 + 16 * heat) * Math.cos(tau * 1.3 + c.ph[1]);
  const molBg = mix(mix(C.deep, '#3a1f18', heat), '#080c14', Math.min(1, vap * 1.4));
  const tc = mix('#5fb8e6', C.hot, heat);

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} style={{ position: 'absolute' }}>
        <defs>
          <radialGradient id="gH" cx=".38" cy=".36"><stop offset="0" stopColor="#fff" /><stop offset="1" stopColor="#8a97a6" /></radialGradient>
          <radialGradient id="shade" cx=".38" cy=".36"><stop offset="0" stopColor="#fff" stopOpacity=".55" /><stop offset=".45" stopColor="#fff" stopOpacity="0" /><stop offset="1" stopColor="#000" stopOpacity=".45" /></radialGradient>
          <radialGradient id="glow"><stop offset="0" stopColor={C.hot} stopOpacity=".8" /><stop offset="1" stopColor={C.hot} stopOpacity="0" /></radialGradient>
          <radialGradient id="atomHalo"><stop offset="0" stopColor={mix('#3f9fd6', C.hot, heat)} stopOpacity=".35" /><stop offset="1" stopColor="#000" stopOpacity="0" /></radialGradient>
          <linearGradient id="gWater" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#4fb0e4" stopOpacity=".75" /><stop offset="1" stopColor="#1b5d8f" stopOpacity=".9" /></linearGradient>
          <radialGradient id="vign" cx=".5" cy=".5" r=".75"><stop offset=".55" stopColor="#000" stopOpacity="0" /><stop offset="1" stopColor="#000" stopOpacity=".55" /></radialGradient>
          <filter id="blur"><feGaussianBlur stdDeviation="6" /></filter>
        </defs>

        {glassA > 0 && (
          <g opacity={glassA}>
            <rect width={W} height={H} fill="#0a1220" />
            <g transform={`translate(640 360) scale(${gz}) translate(-640 ${-gty})`}>
              <rect x={-3000} y={560} width={7000} height={3000} fill="#0c121b" />
              <Glass t={t} level={f > 400 ? interpolate(f, [800, 900], [.15, .3], clamp) : 0} steam={f > 400 ? interpolate(f, [810, 860], [0, 1], clamp) : 0} grow={f < 400 ? grow : 1} />
            </g>
          </g>
        )}

        {molA > 0 && (
          <g opacity={molA}>
            <rect width={W} height={H} fill={molBg} />
            <g transform={`translate(640 360) scale(${mz}) translate(${-cx} ${-cy})`}>
              {MOLS.map((m, i) => <Molecule key={i} m={m} t={t} h={heat} v={vap} />)}
            </g>
          </g>
        )}

        {atomA > 0 && (
          <g opacity={atomA}>
            <rect width={W} height={H} fill="#05080f" />
            <Atom t={t} h={heat} s={az} />
          </g>
        )}
        <rect width={W} height={H} fill="url(#vign)" />
      </svg>

      <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to top, rgba(4,7,13,.85), rgba(4,7,13,0) 34%)' }} />
      <BigWord text="H₂O" from={185} to={330} color="#5fb8e6" />
      <BigWord text="O" from={370} to={500} color="#7fd0f5" />
      <BigWord text={`${Math.round(temp)}°`} from={540} to={800} color={tc} />
      <BigWord text="GAS" from={830} to={900} color="#eef4f8" />

      <Kicker from={10} to={150} n="01" title="A glass of water" sub="About 250 mL at 20 °C" />
      <Kicker from={185} to={330} n="02" title="Water molecules" sub="H₂O · oxygen red, hydrogen white" />
      <Kicker from={370} to={500} n="03" title="An oxygen atom" sub="8 protons · 8 neutrons · 8 electrons" />
      <Kicker from={540} to={690} n="04" title="Heating up" sub="Molecules move faster and faster" />
      <Kicker from={700} to={805} n="05" title="Bonds break" sub="Molecules escape as vapor" />
      <Kicker from={830} to={900} n="06" title="Steam" sub="Liquid becomes gas at 100 °C" />

      <div style={{ position: 'absolute', right: 56, bottom: 56, textAlign: 'right', fontFamily: '"DejaVu Sans Mono", monospace' }}>
        <div style={{ fontSize: 13, color: C.mute, letterSpacing: 2 }}>TEMPERATURE</div>
        <div style={{ fontSize: 40, fontWeight: 700, color: tc, fontVariantNumeric: 'tabular-nums' }}>{Math.round(temp)} °C</div>
        <div style={{ width: 200, height: 5, background: 'rgba(255,255,255,.12)', marginTop: 6, marginLeft: 'auto' }}>
          <div style={{ width: `${heat * 100}%`, height: '100%', background: tc }} />
        </div>
      </div>
    </AbsoluteFill>
  );
};
