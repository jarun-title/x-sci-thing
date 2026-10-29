// The kitchen stage: a steel pot on a gas flame, a digital thermometer with its probe in the water,
// and the heating curve it draws. One function builds it into an <svg>; update(t, o) moves it.
(function () {
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const lerp = (a, b, k) => a + (b - a) * k;
  // heating curve in graph space: u in [0,1] across, warming until u = 0.42 then flat at 100 °C
  const U_BOIL = 0.42;
  const tempAt = u => u < U_BOIL ? 20 + 80 * (1 - Math.pow(1 - u / U_BOIL, 1.6)) : 100;
  const G = { x0: 150, x1: 960, yTop: 498, yBot: 718 };   // axes box
  const gx = u => lerp(G.x0 + 8, G.x1, u), gy = T => lerp(G.yBot - 14, G.yTop + 26, (T - 20) / 80);

  function Kitchen(svg, p) {
    const id = s => `${p}-${s}`;
    svg.setAttribute("viewBox", "0 0 1080 1920"); svg.setAttribute("width", "1080"); svg.setAttribute("height", "1920");
    let flames = "";
    for (let i = 0; i < 13; i++) flames += `<path id="${id("f" + i)}" fill="url(#${id("flame")})" />`;
    svg.innerHTML = `
      <defs>
        <linearGradient id="${id("steel")}" x1="0" x2="1"><stop offset="0" stop-color="#7E8A94"/><stop offset=".28" stop-color="#DDE3E8"/><stop offset=".55" stop-color="#A7B2BB"/><stop offset="1" stop-color="#6F7B85"/></linearGradient>
        <linearGradient id="${id("flame")}" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#2F6FE0"/><stop offset=".55" stop-color="#5EA2FF"/><stop offset="1" stop-color="#BFE0FF" stop-opacity=".2"/></linearGradient>
        <linearGradient id="${id("flame2")}" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#1E4FD0"/><stop offset=".5" stop-color="#9FD0FF"/><stop offset="1" stop-color="#FFFFFF" stop-opacity=".0"/></linearGradient>
        <radialGradient id="${id("glow")}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#FF9A4A" stop-opacity=".85"/><stop offset=".45" stop-color="#FF7A2F" stop-opacity=".35"/><stop offset="1" stop-color="#FF7A2F" stop-opacity="0"/></radialGradient>
        <radialGradient id="${id("bglow")}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#6FB0FF" stop-opacity=".55"/><stop offset="1" stop-color="#6FB0FF" stop-opacity="0"/></radialGradient>
        <radialGradient id="${id("water")}" cx=".45" cy=".4"><stop offset="0" stop-color="#3D86BA"/><stop offset="1" stop-color="#1E5A86"/></radialGradient>
      </defs>
      <rect width="1080" height="1920" fill="#E8EDF1"/>
      <rect y="1196" width="1080" height="724" fill="#1B1F24"/>
      <rect y="1196" width="1080" height="4" fill="#3A424B"/>
      <g fill="#2A3038" stroke="#3E4751" stroke-width="4">
        <circle cx="300" cy="1560" r="54"/><circle cx="540" cy="1560" r="54"/><circle cx="780" cy="1560" r="54"/>
      </g>
      <circle cx="540" cy="1560" r="68" fill="none" stroke="#FF7A2F" stroke-width="6" opacity=".9"/>
      <text x="540" y="1668" text-anchor="middle" font-family="Inter" font-weight="900" font-size="34" fill="#FF7A2F" letter-spacing="4">HIGH</text>
      <g stroke="#C9D1D8" stroke-width="8" stroke-linecap="round">
        <path d="M300 1560 L300 1518"/><path d="M540 1560 L578 1530"/><path d="M780 1560 L780 1518"/>
      </g>
      <!-- thermometer: display, cable, probe -->
      <rect x="230" y="196" width="620" height="240" rx="28" fill="#0E1A24"/>
      <text x="268" y="250" font-family="Inter" font-weight="700" font-size="34" fill="#9FB0BD">water temperature</text>
      <text id="${id("temp")}" x="540" y="414" text-anchor="middle" font-family="League Gothic" font-size="190" fill="#F4F7FA">20.0 °C</text>
      <path d="M790 436 C 800 560, 900 600, 880 700 S 820 780, 790 812" fill="none" stroke="#2A333C" stroke-width="7"/>
      <rect x="784" y="790" width="12" height="150" rx="5" fill="#C9D1D8" stroke="#6F7B85" stroke-width="2"/>
      <!-- heating curve -->
      <g id="${id("graph")}">
        <path d="M${G.x0} ${G.yTop} V${G.yBot} H${G.x1}" fill="none" stroke="#4A5B68" stroke-width="4" stroke-linecap="round"/>
        <path d="M${G.x0 - 10} ${gy(100)} H${G.x1}" stroke="#9AAAB6" stroke-width="2" stroke-dasharray="8 10"/>
        <text x="${G.x0 - 18}" y="${gy(100) + 12}" text-anchor="end" font-family="Inter" font-weight="700" font-size="34" fill="#4A5B68">100°</text>
        <text x="${G.x0 - 18}" y="${gy(20) + 12}" text-anchor="end" font-family="Inter" font-weight="700" font-size="34" fill="#4A5B68">20°</text>
        <text x="${G.x1}" y="${G.yBot + 48}" text-anchor="end" font-family="Inter" font-weight="700" font-size="34" fill="#4A5B68">time →</text>
        <path id="${id("curve")}" fill="none" stroke="#FF7A2F" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>
        <circle id="${id("dot")}" r="15" fill="#FF7A2F" stroke="#FFFFFF" stroke-width="5"/>
      </g>
      <!-- flame under the pot, then the pot -->
      <ellipse id="${id("bg")}" cx="540" cy="1130" rx="420" ry="120" fill="url(#${id("bglow")})"/>
      <!-- heat rising past the pot -->
      <g id="${id("heat")}" fill="none" stroke="#FF7A2F" stroke-width="6" stroke-linecap="round"></g>
      <!-- burner, grate posts, flames -->
      <ellipse cx="540" cy="1180" rx="250" ry="16" fill="#0D0F12"/>
      <rect x="262" y="1168" width="556" height="14" rx="6" fill="#2A3038"/>
      <g id="${id("flames")}">${flames}</g>
      <g id="${id("flames2")}">${flames.replace(/f(\d+)"/g, 'g$1"').replace(/flame\)/g, "flame2)")}</g>
      <rect x="210" y="1080" width="18" height="118" rx="4" fill="#0D0F12"/><rect x="852" y="1080" width="18" height="118" rx="4" fill="#0D0F12"/>
      <rect x="196" y="1080" width="688" height="12" rx="4" fill="#0D0F12"/>
      <ellipse cx="540" cy="1080" rx="300" ry="26" fill="#5F6A74"/>
      <path d="M232 830 V1050 Q232 1082 268 1082 H812 Q848 1082 848 1050 V830 Z" fill="url(#${id("steel")})"/>
      <ellipse id="${id("hot")}" cx="540" cy="1074" rx="330" ry="46" fill="url(#${id("glow")})"/>
      <rect x="168" y="846" width="78" height="26" rx="13" fill="#3A424B"/>
      <rect x="834" y="846" width="78" height="26" rx="13" fill="#3A424B"/>
      <ellipse cx="540" cy="830" rx="308" ry="42" fill="#B9C3CB" stroke="#7E8A94" stroke-width="4"/>
      <ellipse id="${id("surface")}" cx="540" cy="836" rx="288" ry="32" fill="url(#${id("water")})"/>
      <g id="${id("bubbles")}" fill="none" stroke="#CFE7F8" stroke-width="3"></g>
      <rect x="784" y="790" width="12" height="60" rx="5" fill="#C9D1D8" stroke="#6F7B85" stroke-width="2"/>
      <g id="${id("labels")}"></g>`;
    const $ = s => svg.querySelector("#" + id(s));
    const flameEls = [...Array(13)].map((_, i) => $("f" + i)), innerEls = [...Array(13)].map((_, i) => $("g" + i));
    const heatG = $("heat"), hot = $("hot"), bg = $("bg");
    const heatEls = [...Array(8)].map(() => { const e = document.createElementNS("http://www.w3.org/2000/svg", "path"); heatG.appendChild(e); return e; });
    const bubbleG = $("bubbles"), NS = "http://www.w3.org/2000/svg";
    const bubbles = [...Array(18)].map((_, i) => { const c = document.createElementNS(NS, "ellipse"); bubbleG.appendChild(c); return c; });
    const temp = $("temp"), curve = $("curve"), dot = $("dot");

    function update(t, o) {
      // flame: 13 tongues across the burner, each flickering on its own phase
      const F = o.flame == null ? 1 : o.flame, B = 1170;
      flameEls.forEach((el, i) => {
        // tongues rise from the burner ring and lick the pot bottom (their tips go behind the pot)
        const x = 290 + i * 41.7, lean = (x - 540) / 250 * 22;
        const h = F * (104 + 18 * Math.sin(t * 9.1 + i * 1.7) + 10 * Math.sin(t * 15.3 + i * 0.9)), w = 20;
        el.setAttribute("d", `M${x - w} ${B} Q${x - w * 1.1} ${B - h * 0.55} ${x + lean} ${B - h} Q${x + w * 1.1} ${B - h * 0.55} ${x + w} ${B} Z`);
        const h2 = h * 0.55, w2 = 9;
        innerEls[i].setAttribute("d", `M${x - w2} ${B} Q${x - w2} ${B - h2 * 0.55} ${x + lean * 0.5} ${B - h2} Q${x + w2} ${B - h2 * 0.55} ${x + w2} ${B} Z`);
      });
      const fl = 0.85 + 0.15 * Math.sin(t * 11.3) * Math.sin(t * 4.1);
      hot.setAttribute("opacity", (F * fl).toFixed(3)); bg.setAttribute("opacity", (F * fl).toFixed(3));
      // heat shimmer: wavy strokes rising up both sides of the pot and fading out
      heatEls.forEach((el, i) => {
        const side = i % 2 ? 1 : -1, k = Math.floor(i / 2), per = 1.6, a = ((t / per) + k * 0.25) % 1;
        const x0 = 540 + side * (350 + 26 * (k % 2)), y0 = 1060 - a * 260, len = 110;
        let d = ""; for (let j = 0; j <= 10; j++) { const yy = y0 - j * len / 10; d += (j ? " L" : "M") + (x0 + 9 * Math.sin(yy / 22 + t * 6 + k)).toFixed(1) + " " + yy.toFixed(1); }
        el.setAttribute("d", d); el.setAttribute("opacity", (F * 0.55 * Math.sin(Math.PI * a)).toFixed(3));
      });
      // bubbles reaching the surface: more and bigger when boiling
      const boil = o.boil || 0;
      bubbles.forEach((c, i) => {
        const per = 0.7 + (i % 5) * 0.17, a = (t / per + i * 0.137) % 1;
        const x = 540 + Math.sin(i * 12.9898) * 250, y = 836 + Math.cos(i * 7.233) * 22;
        const r = (6 + (i % 4) * 4) * (0.5 + a) * boil;
        c.setAttribute("cx", x.toFixed(1)); c.setAttribute("cy", y.toFixed(1));
        c.setAttribute("rx", r.toFixed(1)); c.setAttribute("ry", (r * 0.45).toFixed(1));
        c.setAttribute("opacity", (boil * (1 - a)).toFixed(3));
      });
      // readout and curve
      const u = clamp(o.u == null ? 1 : o.u);
      const T = o.temp != null ? o.temp : tempAt(u);
      temp.textContent = (o.flicker ? T - (Math.sin(t * 3.7) > 0.6 ? 0.1 : 0) : T).toFixed(1) + " °C";
      temp.setAttribute("fill", T >= 90 ? "#FF7A2F" : "#F4F7FA");
      let d = ""; const n = 80;
      for (let k = 0; k <= n; k++) { const uu = u * k / n; d += (k ? " L" : "M") + gx(uu).toFixed(1) + " " + gy(tempAt(uu)).toFixed(1); }
      curve.setAttribute("d", d); dot.setAttribute("cx", gx(u)); dot.setAttribute("cy", gy(tempAt(u)));
    }
    return { update, el: $, G, gx, gy, U_BOIL };
  }
  window.Kitchen = Kitchen;
})();
