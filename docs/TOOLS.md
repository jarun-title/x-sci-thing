# เครื่องมือที่ลองแล้ว และบทเรียน

## เทียบเครื่องมือทำภาพ

| เครื่องมือ | ใช้ทำอะไรในเซสชันนี้ | ข้อดี | ข้อจำกัด |
|---|---|---|---|
| HTML + Three.js | เวอร์ชันแรก (`02-first-versions/html`) | เร็ว ดูในเบราว์เซอร์ได้ทันที | ต้องหาทางอัดเป็นวิดีโอเอง |
| Manim | `02-first-versions/manim` | เหมาะกับสมการ/กราฟแบบ 3Blue1Brown | สไตล์ค่อนข้างตายตัว |
| Remotion (React) | `02-first-versions/remotion`, `remotion-plugin` | ระบบนิเวศใหญ่ มี plugin ของ Claude Code | concurrency ต้อง ≤ 2 บนเครื่องนี้; `remotion.media` ถูกบล็อก |
| **HyperFrames** (HTML → วิดีโอ) | `03`, `04`, `01` (คลิปล่าสุด) | `check` / `snapshot` / lint ให้ feedback ละเอียด (ข้อความทับกัน, contrast, safe zone, เสียงเงียบ) ทำให้ AI แก้งานเองได้ดี | ต้อง deterministic; ห้ามวัด DOM ใน `onUpdate` |
| **Blender** (bpy, headless) | `05-blender-scenes`, ฟุตเทจของ `04` | สวยที่สุด แสง/เงา/วัสดุจริง | เรนเดอร์ช้ามากบน CPU 2 คอร์; ต้องเขียนสคริปต์ให้เรนเดอร์ต่อจากเฟรมที่ค้างได้ |

ข้อสรุปสำหรับ Shorts แนวอธิบาย: ใช้ **HyperFrames** เป็นตัวหลัก (ข้อความ ซับ กราฟ จังหวะตามเสียงพากย์)
แล้วค่อยใช้ Blender ทำช็อต 3D สวย ๆ มาใส่เป็นฟุตเทจเมื่อคุ้มเวลาเรนเดอร์

## เสียง

| งาน | วิธี |
|---|---|
| เสียงพากย์ | Kokoro-onnx 0.6.1 รันในเครื่อง (`06-audio/kokoro-tts`) เสียง `am_michael`, `speed=1.05`, `lang="en-us"` |
| เวลาของแต่ละคำ | Kokoro ไม่ให้ duration มา จึงประมาณจากช่วงเงียบ + น้ำหนักพยางค์ + จุดพลังงานต่ำ (`01/tools/voice.py`) |
| ดนตรี | สังเคราะห์ด้วย numpy (pad + pulse ที่เร่งตามอุณหภูมิ) หรือ Tone.js ในเบราว์เซอร์ (`06-audio/tone-js`) |
| เสียงเดือด | blip ความถี่ต่ำ ≤ 700 Hz + rumble ผ่าน low-pass — **ห้ามมีเสียงแหลม** |
| มิกซ์ | `01/tools/mix.py`: วางเสียงพากย์ตาม timeline, SFX ตามจังหวะภาพ, ducking −9 dB ขณะพูด, `loudnorm=I=-16:TP=-1.5` |

## ขั้นตอนทำคลิปล่าสุด (01)

```bash
cd projects/01-100c-mystery-short
python3 tools/voice.py .        # เสียงพากย์ทีละบรรทัด → assets/voice/*.wav + voice.json
python3 tools/layout.py .       # วางบรรทัดบนไทม์ไลน์ → timeline.json
python3 tools/mix.py .          # มิกซ์เสียงทั้งหมด → assets/mix.wav + audio_cues.json
python3 tools/build.py . --audio  # สร้าง compositions/*.html + index.html
export HYPERFRAMES_NO_TELEMETRY=1 HYPERFRAMES_NO_UPDATE_CHECK=1
npx hyperframes check --json
npx hyperframes snapshot --at 3,14,22,31,43,48 --no-end
npx hyperframes render -o out.mp4 -q standard -w 2 --no-browser-gpu
```

## ข้อจำกัดของเครื่องที่ใช้ทำ (cloud container)

- เน็ตออกได้เฉพาะบางโดเมน: GitHub release ดาวน์โหลดได้, HuggingFace และ `remotion.media` ถูกบล็อก
- คำสั่ง background รันได้ไม่เกิน 2 ชม. และ container รีสตาร์ทได้ → งานเรนเดอร์ยาวต้องทำแบบ resume ได้ (`05/queue.sh`, `resume.sh`)
- Chromium headless ใช้ swiftshader (ไม่มี GPU)
