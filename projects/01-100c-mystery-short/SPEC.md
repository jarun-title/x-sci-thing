# SPEC — The 100 °C mystery (vertical short)

GOAL:    The viewer leaves knowing why boiling water stays at 100 °C: past that point the heat goes into
         snapping hydrogen bonds between molecules, not into raising the temperature.
OUTPUT:  HyperFrames, 1080 × 1920, 30 fps, MP4
TIME:    ~40–46 s (the voice is the clock; scene lengths come from the narration + 0.3–0.6 s air)

## Script (Kokoro am_michael, en-us, speed 1.05) — every line checked
| id        | line                                                                                                  | fact behind it |
|-----------|-------------------------------------------------------------------------------------------------------|----------------|
| hook      | The flame is still on. So why is this water stuck at exactly one hundred degrees?                     | boiling point of water at 1 atm (sea level) |
| zoom      | Zoom in a few hundred million times.                                                                  | ~10 cm pot / ~0.3 nm molecule ≈ 3 × 10⁸ |
| molecule  | Each molecule is one oxygen and two hydrogens, sharing electrons.                                     | H₂O, two covalent O–H bonds (shared pairs) |
| charge    | Oxygen pulls the shared electrons harder, so it turns slightly negative, and the hydrogens slightly positive. | O is more electronegative: δ− on O, δ+ on H |
| hbonds    | Opposites attract. Neighbors cling together with hydrogen bonds.                                      | δ+ H of one molecule ↔ δ− O of the next |
| heat      | Heat makes them jiggle faster and faster, and the temperature climbs.                                 | temperature tracks the molecules' kinetic energy |
| stop      | But at one hundred degrees, the heat stops raising the temperature.                                   | boiling plateau at 1 atm |
| free      | It goes into snapping hydrogen bonds, and setting molecules free.                                     | latent heat of vaporisation; O–H bonds stay intact |
| payoff    | Free molecules spread out. One cup of water becomes about sixteen hundred cups of steam.              | 958.4 / 0.598 kg/m³ ≈ 1,603× at 100 °C |
| claim     | That's boiling: heat that frees water instead of warming it.                                          | — |

On screen, never the spoken sentence as a title: captions carry the words; titles carry numbers and labels only.

## LOOK
- Medium: a science-museum diagram brought to life — flat shapes with one soft shading pass, crisp labels, real units.
- Kitchen world (hook, claim): wall #E8EDF1, stovetop #1B1F24, steel pot (linear #9AA6B0 → #DDE3E8 → #8C97A1), blue gas flame #3D8BFF core / #8FC4FF edge.
- Water world (zoom → payoff): ground linear #0F4C75 (top) → #0A3150 (bottom) with moving caustic bands at 5% white.
  Air (above the surface in "free" and "payoff"): #CFE3F1.
- Atoms: O disc #E5484D, H disc #F3F6F8, both with one radial highlight at 30%/30%; O radius 1.6 × H radius.
  Electron density (molecule close-up only): a translucent #9ED3FF shape at 22% opacity hugging all three atoms, thicker around O.
  Shared pairs: two dots (#FFE08A, r 9 px) on each O–H bond; lone pairs: two pairs on O's outer side.
- Accent (heat only): #FF7A2F — flame glow at the bottom edge, heat arrows, temperature ≥ 90 °C, bonds as they snap. Nowhere else.
- Type: League Gothic for the temperature and the 1,600× (300–420 px, tracking 0);
  Inter 900 for captions (66–78 px, white, 7 px #0B1620 stroke painted under the fill);
  Inter 700 for labels (40–46 px). Nothing read under 32 px.
- Safe band (TikTok/Shorts UI): every word between y = 168 and 1330, nothing under the right action rail (x > 920 below y 900).
  Captions centred at y ≈ 1180–1300.

## OBJECTS (must read without a label)
- Pot: steel, two side handles, water line, bubbles rising, sitting on a burner grate, flame ring under it.
- Thermometer: a digital probe in the water, readout panel above the pot.
- Heating curve: axes "temperature" vs "time", the line climbs then goes flat at 100 °C.
- Water molecule: V shape at 104.5°, O big and red, two small white H.
- Hydrogen bond: dashed line from an H of one molecule to the O of another (never between atoms of the same molecule).
- Cup: a plain mug silhouette; 1,600 tiny mugs in a 40 × 40 grid for the payoff.

## MOTION
- Arrivals: expo.out 0.4–0.6 s; camera moves: power2.inOut; zoom-throughs: power3.in.
- Labels: per-word blur-in 0.13 s, 0.067 s stagger; land and hold dead still.
- Molecule jiggle amplitude ∝ √T (Kelvin), so the motion grows with temperature, from 293 K to 373 K.
- Snapping bonds: dash line splits at its midpoint and both halves retract in 0.25 s with a 0.1 s orange flash on the break point (no glow).
- One hero move per shot; secondary moves start 0.1–0.2 s later and travel 50–70% as far.

## SHOTS (times fixed after the voice is generated)
1. hook — kitchen: pot on flame, readout 100.0 °C, heating curve drawing flat. Title: "100 °C" big. Footnote: "at sea level".
2. zoom — a magnifier circle on the water grows to fill the frame (object becomes the world); scale tag "× 300,000,000".
3. molecule — one H₂O fills ~55% of the frame width; electron cloud and shared pairs fade in on "sharing electrons".
4. charge — the shared pairs slide toward O; δ− lands on O, δ+ on each H on the words "negative" / "positive".
5. hbonds — pull back: four neighbours arrive; dashed hydrogen bonds draw H→O on "hydrogen bonds"; then the wider network.
6. heat — orange heat from the bottom edge; jiggle grows; readout climbs 20 → 100 °C in time with "temperature climbs".
7. stop — readout hits 100 °C and holds still; a "heat in" arrow keeps pumping; label "temperature: stuck".
8. free — hydrogen bonds snap one by one; molecules leave through the surface into air; label on one molecule:
   "O–H bonds stay intact".
9. payoff — one mug → grid of 1,600 mugs fills the frame; "× 1,600" lands.
10. claim — back to the kitchen heating curve: plateau labelled "boiling: heat → breaking hydrogen bonds", warming part labelled "warming".

## SOUND
Bed: low pulse (sine 55 Hz + soft click) at 84 bpm that rises to 112 bpm across the heat shot, holds on "stop".
Effects: whoosh on the zoom-through; soft pop on δ− / δ+ landing; riser into "one hundred degrees" + bass hit on the lock;
small clicks on bond snaps (rotate 2–3 variants); bubbling under the hook and claim. Voice on top: bed ~ −14 dB under voice,
mix ≈ −16 LUFS, peaks ≤ −1 dBTP.

## BANNED
Dark navy void with floating dots; glow/bloom/lens flare; molecules that emit light; electron clouds that "heat up";
"bonds break" without saying which bonds; white plume called steam; titles repeating the narration;
everything fading-and-sliding up; text that moves while read; a lone oxygen atom shown out of its molecule.

## QA
- t ≈ 1 s: kitchen readable in one glance, "100 °C" and the question legible at phone size.
- molecule shot: exactly 1 O + 2 H, angle opens away from O, shared pairs on the bonds, lone pairs on O.
- charge shot: δ− on O, δ+ on both H, timed to the words.
- hbonds shot: every dashed line joins H of one molecule to O of another.
- stop shot: readout held at 100 °C while the heat arrow keeps moving.
- free shot: no molecule splits; the label "O–H bonds stay intact" is on a molecule that just escaped.
- payoff: 1,600 = 40 × 40, "× 1,600" legible.
- every caption inside the safe band; nothing under 32 px.
