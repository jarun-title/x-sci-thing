import soundfile as sf, numpy as np, json
from kokoro_onnx import Kokoro
k = Kokoro("kokoro-v1.0.int8.onnx", "voices-v1.0.bin")
# (id, scene start, scene length, line)
lines = [
    ("vo-glass", 0.0, 5.5, "This is a glass of water."),
    ("vo-molecules", 5.5, 7.0, "Zoom in a hundred million times, and you find molecules. One oxygen, two hydrogens."),
    ("vo-atom", 12.5, 5.0, "Inside each one, an oxygen atom, wrapped in a cloud of electrons."),
    ("vo-heat", 17.5, 7.0, "Add heat, and everything moves faster. At one hundred degrees, the bonds break."),
    ("vo-steam", 24.5, 5.5, "And the water escapes, as steam."),
]
meta = []
for vid, start, length, text in lines:
    s, sr = k.create(text, voice="am_michael", speed=1.05, lang="en-us")
    s = s / max(1e-9, np.abs(s).max()) * 0.89
    sf.write(f"/home/claude/hf-water/water/assets/audio/{vid}.wav", s, sr)
    d = len(s) / sr; meta.append((vid, start, length, round(d, 2)))
    print(f"{vid}: {d:.2f}s spoken, scene {length}s, spare {length - d:.2f}s")
json.dump(meta, open("vo_meta.json", "w"))
