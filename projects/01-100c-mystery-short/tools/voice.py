"""Generate the narration (Kokoro am_michael) and estimate word timings for captions.

This Kokoro export has no duration output, so word times are estimated per line:
1. find pauses (>= 110 ms under -38 dB) inside the line's speech;
2. split the words into phrases at punctuation and map phrases to the pause-delimited segments when the
   counts agree (otherwise the whole line is one segment);
3. inside each segment, spread words by syllable weight, then snap each boundary to the quietest
   10 ms frame within +-90 ms.
Output: assets/voice/<id>.wav and voice.json {id: {duration, words: [{text, start, end}]}}
"""
import json, re, sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

ROOT = sys.argv[1]
LINES = [
    ("hook", "The flame is still on. So why is this water stuck at exactly one hundred degrees?"),
    ("zoom", "Zoom in a few hundred million times."),
    ("molecule", "Each molecule is one oxygen and two hydrogens, sharing electrons."),
    ("charge", "Oxygen pulls the shared electrons harder, so it turns slightly negative, and the hydrogens slightly positive."),
    ("hbonds", "Opposites attract. Neighbors cling together with hydrogen bonds."),
    ("heat", "Heat makes them jiggle faster and faster, and the temperature climbs."),
    ("stop", "But at one hundred degrees, the heat stops raising the temperature."),
    ("free", "It goes into snapping hydrogen bonds, and setting molecules free."),
    ("payoff", "Free molecules spread out. One cup of water becomes about sixteen hundred cups of steam."),
    ("claim", "That's boiling: heat that frees water instead of warming it."),
]
k = Kokoro("/home/claude/kokoro/kokoro-v1.0.int8.onnx", "/home/claude/kokoro/voices-v1.0.bin")


def syllables(w):
    w = re.sub(r"[^a-z]", "", w.lower())
    if not w: return 1
    n = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and not w.endswith(("le", "ee")) and n > 1: n -= 1
    return max(1, n)


def envelope_db(x, sr, hop=0.01):
    h = int(sr * hop); n = len(x) // h
    fr = x[: n * h].reshape(n, h)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9), hop


out = {}
for vid, text in LINES:
    audio, sr = k.create(text, voice="am_michael", speed=1.05, lang="en-us")
    audio = audio / max(1e-9, np.abs(audio).max()) * 0.89
    sf.write(f"{ROOT}/assets/voice/{vid}.wav", audio, sr)
    db, hop = envelope_db(audio, sr)
    loud = db > -38
    idx = np.where(loud)[0]; s0, s1 = idx[0], idx[-1] + 1
    # pauses inside speech
    pauses, i = [], s0
    while i < s1:
        if not loud[i]:
            j = i
            while j < s1 and not loud[j]: j += 1
            if (j - i) * hop >= 0.11: pauses.append((i, j))
            i = j
        else: i += 1
    segs, prev = [], s0
    for a, b in pauses: segs.append((prev, a)); prev = b
    segs.append((prev, s1))
    words = text.split()
    phrases, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[,.;:?!]$", w): phrases.append(cur); cur = []
    if cur: phrases.append(cur)
    if len(phrases) != len(segs):
        # fall back: merge segments by keeping the len(phrases)-1 longest pauses
        keep = sorted(sorted(pauses, key=lambda p: p[1] - p[0], reverse=True)[: len(phrases) - 1])
        segs, prev = [], s0
        for a, b in keep: segs.append((prev, a)); prev = b
        segs.append((prev, s1))
        if len(segs) != len(phrases): segs, phrases = [(s0, s1)], [words]
    timed = []
    for (a, b), ph in zip(segs, phrases):
        wts = np.array([syllables(w) + 0.35 for w in ph], float)
        edges = a + (b - a) * np.concatenate([[0], np.cumsum(wts) / wts.sum()])
        for e in range(1, len(edges) - 1):  # snap inner boundaries to the quietest nearby frame
            c = int(round(edges[e])); lo, hi = max(a + 1, c - 9), min(b - 1, c + 9)
            if hi > lo: edges[e] = lo + int(np.argmin(db[lo:hi]))
        for w, e0, e1 in zip(ph, edges[:-1], edges[1:]):
            timed.append(dict(text=w, start=round(float(e0) * hop, 3), end=round(float(e1) * hop, 3)))
    out[vid] = dict(duration=round(len(audio) / sr, 3), words=timed)
    print(f"{vid:9s} {len(audio)/sr:5.2f}s  segs {len(segs)}  phrases {len(phrases)}")
json.dump(out, open(f"{ROOT}/voice.json", "w"), indent=1)
