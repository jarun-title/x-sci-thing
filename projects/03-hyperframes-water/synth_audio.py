"""Procedural audio for the glass-to-steam film.

boil.wav : 12.5 s, starts at film t=17.5. Bubble pops (Minnaert-style upward chirps)
           whose rate follows the on-screen temperature, a low rumble, and a steam hiss
           in the final scene.
bed.wav  : 30 s ambient pad. Cool minor chords, brightening to major as the water boils.
Everything is seeded so the files are reproducible.
"""
import numpy as np, wave, sys

SR = 48000
rng = np.random.default_rng(42)


def write(path, x):
    x = np.clip(x, -1, 1)
    st = np.stack([x, x], 1) if x.ndim == 1 else x
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.empty_like(x); s = 0.0
    for i in range(len(x)):
        s = (1 - a) * x[i] + a * s; y[i] = s
    return y


def lp_fast(x, fc):  # vectorised-ish one-pole via scipy-free recursion on blocks
    return onepole_lp(x, fc)


# ---------------- boiling ----------------
def boil():
    D = 12.5; n = int(D * SR); t = np.arange(n) / SR
    out = np.zeros((n, 2))
    io = lambda x: np.where(x < .5, 4 * x ** 3, 1 - (-2 * x + 2) ** 3 / 2)
    # heat in the heat scene: 0.25 -> 1 over 4.2 s, then stays boiling
    heat = 0.25 + 0.75 * io(np.clip(t / 4.2, 0, 1))
    # bubble rate per second: a few at 40 °C, a rolling boil at 100 °C
    rate = 2 + 140 * heat ** 3
    # steam scene (t >= 7) keeps boiling, a touch quieter under the closing line
    lvl = np.where(t < 7, 1.0, 0.85)
    cum = np.cumsum(rate) / SR
    k = 0; nxt = rng.exponential(1.0)
    times = []
    while nxt < cum[-1]:
        times.append(np.searchsorted(cum, nxt)); nxt += rng.exponential(1.0)
    for idx in times:
        h = heat[idx]
        r_mm = rng.lognormal(np.log(3.2 - 0.8 * h), 0.4)           # bubble radius, mm (rolling-boil bubbles are big)
        f0 = np.clip(3260 / r_mm, 250, 1200)                         # Minnaert resonance ~3.26 kHz / r(mm); kept below the speech band
        dur = np.clip(0.012 + 0.03 * r_mm / 2, 0.01, 0.07)
        m = int(dur * 3 * SR); tt = np.arange(m) / SR
        f = f0 * (1 + 0.12 * (1 - np.exp(-tt / dur)) * (1 + rng.random()))     # rising chirp as the bubble surfaces
        ph = 2 * np.pi * np.cumsum(f) / SR
        env = np.exp(-tt / dur) * (1 - np.exp(-tt / 0.0008))
        amp = (0.05 + 0.10 * rng.random()) * (0.6 + 0.6 * h) * lvl[idx] * (r_mm / 3.2) ** 0.5
        s = amp * np.sin(ph) * env
        pan = rng.uniform(-.6, .6)
        end = min(n, idx + m); s = s[:end - idx]
        out[idx:end, 0] += s * (1 - pan) * .5 * 2 ** .5
        out[idx:end, 1] += s * (1 + pan) * .5 * 2 ** .5
    # low rumble of a rolling boil
    noise = rng.standard_normal(n)
    rum = lp_fast(lp_fast(noise, 160), 160) * 6
    rum *= (0.02 + 0.10 * heat ** 2) * lvl
    out += rum[:, None]
    # steam hiss once we pull back to the glass (t >= 7 local), filtered noise high band
    hn = rng.standard_normal(n)
    hiss = hn - lp_fast(hn, 2500)
    hiss = lp_fast(hiss, 9000)
    henv = np.clip((t - 6.8) / 1.2, 0, 1) * (0.8 + 0.2 * np.sin(2 * np.pi * 0.37 * t)) * 0.02
    out[:, 0] += hiss * henv; out[:, 1] += np.roll(hiss, 311) * henv
    # fade in from silence, short fade at the very end
    fi = np.clip(t / 0.6, 0, 1); fo = np.clip((D - t) / 1.2, 0, 1)
    out *= (fi * fo)[:, None]
    # duck under the narration (boil-local seconds): heat line 0.4-5.18, steam line 8.4-10.21
    duck = np.ones(n)
    for a, b in ((0.4, 5.18), (8.4, 10.21)):
        ramp_in = np.clip((t - (a - 0.25)) / 0.25, 0, 1); ramp_out = np.clip(((b + 0.3) - t) / 0.3, 0, 1)
        duck -= 0.8 * np.minimum(ramp_in, ramp_out)
    out *= duck[:, None]
    return out


# ---------------- ambient bed ----------------
def bed():
    D = 30.0; n = int(D * SR); t = np.arange(n) / SR
    mid = lambda m: 440 * 2 ** ((m - 69) / 12)
    # (start, notes) — D minor colour while things are cool, Bb/C lift as heat arrives, D major at 100 °C
    chords = [
        (0.0,  [38, 50, 57, 62, 65, 69]),      # Dm(add9 feel)
        (5.5,  [34, 46, 53, 58, 62, 65]),      # Bb maj
        (12.5, [31, 43, 50, 55, 58, 62]),      # Gm
        (17.5, [36, 48, 55, 60, 64, 67]),      # C
        (21.7, [38, 50, 57, 62, 66, 69, 74]),  # D major — boiling
    ]
    out = np.zeros((n, 2))
    for ci, (st, notes) in enumerate(chords):
        en = chords[ci + 1][0] if ci + 1 < len(chords) else D
        a = int(st * SR); b = min(n, int((en + 2.5) * SR))   # overlap 2.5 s for crossfade
        tt = np.arange(b - a) / SR; L = en - st
        env = np.clip(tt / 1.8, 0, 1) * np.clip((L + 2.5 - tt) / 2.5, 0, 1)
        for j, m in enumerate(notes):
            f = mid(m)
            for det, pan in ((-0.004, -0.5), (0.004, 0.5)):
                ph = 2 * np.pi * f * (1 + det) * tt + rng.random() * 6.28
                v = np.sin(ph) + 0.45 * np.sin(2 * ph) + 0.22 * np.sin(3 * ph) + 0.1 * np.sin(4 * ph)
                g = (0.07 if j == 0 else 0.13) / len(notes)
                out[a:b, 0] += v * env * g * (1 - pan) * .5
                out[a:b, 1] += v * env * g * (1 + pan) * .5
    # slow tremolo-free shimmer: a high octave that only enters with the heat
    sh = np.zeros(n)
    for m in (74, 78, 81):
        sh += np.sin(2 * np.pi * mid(m) * t + rng.random() * 6) * 0.02
    shenv = np.clip((t - 18) / 4, 0, 1) * np.clip((30 - t) / 3, 0, 1)
    out[:, 0] += sh * shenv; out[:, 1] += np.roll(sh, 97) * shenv
    # soft lowpass to keep it warm, opening slightly with the heat
    for c in range(2):
        out[:, c] = lp_fast(out[:, c], 4000)
    fi = np.clip(t / 1.2, 0, 1); fo = np.clip((D - t) / 2.0, 0, 1)
    out *= (fi * fo)[:, None]
    return out


if __name__ == "__main__":
    dest = sys.argv[1]
    b = boil(); b /= max(1e-9, np.abs(b).max()); write(f"{dest}/boil.wav", b * 0.89)
    p = bed(); p /= max(1e-9, np.abs(p).max()); write(f"{dest}/bed.wav", p * 0.89)
    print("ok")
