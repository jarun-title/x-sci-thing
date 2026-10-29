"""Mix the whole soundtrack into one file: narration, a synthesized music bed that tracks the story,
sound effects on the visual beats, and pot bubbling. Music and bubbling duck under the voice.
Writes assets/mix.wav and audio_cues.json (one cue), deterministic (fixed seed)."""
import json, subprocess, sys
import numpy as np

ROOT = sys.argv[1]
SR = 48000
TL = json.load(open(f"{ROOT}/timeline.json"))
FILM = TL["film"]
N = int(FILM * SR)
rng = np.random.default_rng(7)
W0 = TL["scenes"]["world"][0]
P0 = TL["scenes"]["payoff"][0]
C0 = TL["scenes"]["claim"][0]
word = lambda line, w: next(x["start"] for x in TL["lines"][line]["words"] if x["text"].lower().strip(".,").startswith(w))


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def add(buf, sig, t, g=1.0):
    i = int(t * SR)
    if i >= len(buf): return
    sig = sig[: len(buf) - i]
    buf[i:i + len(sig)] += sig * g


def db(x): return 10 ** (x / 20)


def lp(x, fc):  # one-pole low-pass, applied twice
    from scipy.signal import lfilter
    a = np.exp(-2 * np.pi * fc / SR)
    for _ in range(2): x = lfilter([1 - a], [1, -a], x)
    return x


t = np.arange(N) / SR
voice = np.zeros(N); music = np.zeros(N); sfx = np.zeros(N); boil = np.zeros(N)

# ---- narration
for lid, L in TL["lines"].items():
    add(voice, load(f"{ROOT}/assets/voice/{lid}.wav"), L["start"], 1.0)

# ---- music bed: soft pad on a slow progression + a pulse that speeds up with the heat
def pad(f0, dur, amp):
    n = int(dur * SR); tt = np.arange(n) / SR
    env = np.minimum(1, tt / 0.8) * np.minimum(1, (dur - tt) / 0.8)
    s = sum(np.sin(2 * np.pi * f0 * m * tt + 0.3 * np.sin(2 * np.pi * 0.2 * tt)) / m ** 1.6 for m in (1, 2, 3, 4))
    return s * env * amp

A = 110.0
chords = [  # (start, dur, root multipliers): Am  F  C  G ... building, then resolve
    (0.0, 8.3, [1, 1.189, 1.498]), (8.3, 8.4, [0.794, 1, 1.189]), (16.7, 8.6, [0.891, 1.122, 1.335]),
    (25.3, 5.5, [1, 1.189, 1.498]), (30.8, 7.9, [0.944, 1.189, 1.414]), (38.7, 6.1, [0.794, 1, 1.189]),
    (44.8, FILM - 44.8, [0.891, 1.122, 1.335]),
]
for st, du, mults in chords:
    for m in mults:
        add(music, pad(A * m * 2, du + 0.8, 0.05), st)
music = lp(music, 1800)

# pulse: soft low "tick" whose rate tracks temperature during the heat line, then locks at 100 °C
heat0, hund = W0 + 17.42, W0 + 22.447
tick = lambda f, a: np.sin(2 * np.pi * f * np.arange(int(0.12 * SR)) / SR) * np.exp(-np.arange(int(0.12 * SR)) / SR * 35) * a
x = 0.6
while x < FILM - 3:
    if x < heat0: rate = 2.0
    elif x < hund: rate = 2.0 + 4.0 * (x - heat0) / (hund - heat0)   # 2 → 6 per second while the temperature climbs
    elif x < P0: rate = 6.0                                           # stuck: same rate, flat
    else: rate = 3.0
    add(music, tick(65, 0.22) + tick(130, 0.06), x)
    x += 1 / rate

# ---- bubbling: low blips (≤ 700 Hz) + lowpassed rumble; on in the hook, then from the 100 °C lock on
def blip(f, dur, a):
    n = int(dur * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * (f + 120 * tt / dur) * tt) * np.exp(-tt * 28) * np.minimum(1, tt * 400) * a
boil_env = np.zeros(N)
def env_on(a, b, lvl, fade=0.5):
    m = (t >= a - fade) & (t <= b + fade)
    e = np.clip(np.minimum((t - (a - fade)) / fade, ((b + fade) - t) / fade), 0, 1)
    np.maximum(boil_env, np.where(m, e * lvl, 0), out=boil_env)
env_on(0.0, TL["scenes"]["zoom"][0] + 0.6, 1.0)
env_on(hund - 0.3, P0 + 1.0, 0.75)
env_on(C0 + 0.2, FILM, 0.7, fade=1.2)
pos = 0.0
while pos < FILM:
    add(boil, blip(rng.uniform(260, 700), rng.uniform(0.05, 0.12), rng.uniform(0.04, 0.12)), pos)
    pos += rng.exponential(0.045)
boil += lp(rng.standard_normal(N) * 0.05, 300)
boil *= boil_env

# ---- sound effects on the visual beats
S = {k: load(f"{ROOT}/assets/sfx/{k}.mp3") for k in ["whoosh-cinematic", "whoosh-short", "riser", "impact-bass-1", "pop", "click-soft", "click"]}
add(sfx, S["whoosh-cinematic"], TL["scenes"]["zoom"][0] - 0.15, db(-8))
add(sfx, S["whoosh-short"], W0 - 0.05, db(-14))
for k, w in [("oxygen", 1.65), ("hydrogens", 2.79), ("h2", 2.87)]:
    add(sfx, S["pop"], W0 + w, db(-16))
for w in (9.291, 11.821, 11.901):                       # δ−, δ+, δ+
    add(sfx, S["pop"], W0 + w, db(-13))
att = word("hbonds", "attract")
for i in range(4): add(sfx, S["pop"], att + i * 0.06, db(-18))
add(sfx, S["click-soft"], W0 + 16.005 + 0.3, db(-12))  # hydrogen bond label
rz = S["riser"]; add(sfx, rz, hund - len(rz) / SR, db(-14))
add(sfx, S["impact-bass-1"], hund, db(-8))
snap = W0 + 26.811
for i, dt in enumerate([0, 0.33, 0.61, 0.95, 1.22, 1.6, 1.9]):
    add(sfx, S["click"], snap + dt, db(-15 - i))
add(sfx, S["whoosh-short"], P0 - 0.05, db(-12))
add(sfx, S["impact-bass-1"], P0 + 4.24, db(-12))        # × 1,600
add(sfx, S["whoosh-short"], C0 - 0.05, db(-14))

# ---- ducking: music and bubbles drop ~9 dB under speech, with smooth attack/release
lvl = np.sqrt(np.convolve(voice ** 2, np.ones(int(0.05 * SR)) / int(0.05 * SR), mode="same"))
speaking = (lvl > 0.01).astype(float)
# hold + smooth: dilate by 0.15 s then smooth 0.12 s
k = int(0.15 * SR); speaking = np.convolve(speaking, np.ones(2 * k) , mode="same") > 0
duck = np.convolve(speaking.astype(float), np.ones(int(0.12 * SR)) / int(0.12 * SR), mode="same")
g = 1 - duck * (1 - db(-9))

mix = voice * db(0) + music * g * db(-2) + boil * g * db(-3) + sfx
# end: fade the last 1.2 s
fade = np.clip((FILM - t) / 1.2, 0, 1); mix *= fade
peak = np.max(np.abs(mix)); mix *= min(1.0, 0.89 / peak)
pcm = (mix * 32767).astype(np.int16)
import wave
with wave.open(f"{ROOT}/assets/mix_raw.wav", "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(pcm.tobytes())
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{ROOT}/assets/mix_raw.wav", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", str(SR), "-ac", "2", f"{ROOT}/assets/mix.wav"], check=True)
json.dump([dict(id="mix", src="assets/mix.wav", start=0, dur=FILM, vol=1, track=3)], open(f"{ROOT}/audio_cues.json", "w"), indent=1)
print("ok", FILM, "peak", round(float(peak), 3))
