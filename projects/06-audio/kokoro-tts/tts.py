import time, soundfile as sf, numpy as np
from kokoro_onnx import Kokoro
t0 = time.time(); k = Kokoro("kokoro-v1.0.int8.onnx", "voices-v1.0.bin"); print("load %.1fs" % (time.time() - t0))
print("voices:", len(k.get_voices()), " ".join(sorted(k.get_voices())[:60]))
text = "This is a glass of water. Zoom in a hundred million times, and you find molecules: one oxygen, two hydrogens, constantly jostling. Add heat, and they move faster and faster, until at one hundred degrees the bonds break, and the water escapes as steam."
for voice in ["af_heart", "am_michael", "bf_emma"]:
    t0 = time.time(); s, sr = k.create(text, voice=voice, speed=1.0, lang="en-us" if voice[0] == "a" else "en-gb")
    dt = time.time() - t0; sf.write(f"{voice}.wav", s, sr); print(f"{voice}: {len(s)/sr:.1f}s of audio in {dt:.1f}s ({len(s)/sr/dt:.1f}x realtime)")
