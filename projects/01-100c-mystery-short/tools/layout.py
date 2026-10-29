"""Place the narration lines on the film timeline and derive the scene boundaries.
Writes timeline.json: line starts/ends, absolute word times, scene windows, film length."""
import json, sys
ROOT = sys.argv[1]
v = json.load(open(f"{ROOT}/voice.json"))
# air after each line (s): longer where the picture needs to land a beat
GAP = dict(hook=0.35, zoom=0.30, molecule=0.25, charge=0.40, hbonds=0.35, heat=0.30, stop=0.25, free=0.40, payoff=0.50, claim=2.00)
order = ["hook", "zoom", "molecule", "charge", "hbonds", "heat", "stop", "free", "payoff", "claim"]
t = 0.20
lines = {}
for vid in order:
    d = v[vid]["duration"]
    lines[vid] = dict(start=round(t, 3), end=round(t + d, 3),
                      words=[dict(text=w["text"], start=round(t + w["start"], 3), end=round(t + w["end"], 3)) for w in v[vid]["words"]])
    t += d + GAP[vid]
film = round(t, 2)
L = lambda k: lines[k]["start"]
# scene windows: each scene starts a little before its first line, so the picture is there when the word lands
scenes = dict(
    hook=(0.0, L("zoom") - 0.15),
    zoom=(L("zoom") - 0.15, L("molecule") - 0.10),
    world=(L("molecule") - 0.10, L("payoff") - 0.15),
    payoff=(L("payoff") - 0.15, L("claim") - 0.20),
    claim=(L("claim") - 0.20, film),
)
scenes = {k: (round(a, 3), round(b, 3)) for k, (a, b) in scenes.items()}
json.dump(dict(film=film, lines=lines, scenes=scenes), open(f"{ROOT}/timeline.json", "w"), indent=1)
for k in order: print(f"{k:9s} {lines[k]['start']:6.2f} → {lines[k]['end']:6.2f}")
print("scenes", scenes); print("film", film)
