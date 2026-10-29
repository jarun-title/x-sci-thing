# x-sci-thing

คลิปอธิบายวิทยาศาสตร์แนวตั้งสำหรับ Shorts / TikTok ที่สร้างด้วยโค้ดทั้งหมด ทั้งภาพ เสียงพากย์ ดนตรี และเอฟเฟกต์เสียง
งานชุดแรกเล่าเรื่องน้ำเดือด และลองมาแล้วหลายเครื่องมือ (Three.js, Manim, Remotion, HyperFrames, Blender)

> Vertical science explainers made entirely in code. First topic: boiling water.

## ผลงานล่าสุด

| ไฟล์ | คืออะไร |
|---|---|
| `renders/100c-mystery-short-v2.mp4` | **The 100 °C mystery** — 1080×1920, 50 วิ, พากย์อังกฤษ (HyperFrames) |
| `renders/glass-to-steam-all-3d.mp4` | แก้วน้ำ → โมเลกุล → อะตอม → ไอน้ำ แบบ 3D ทั้งคลิป (Blender + HyperFrames) |
| `renders/blender-molecules-*.png` | ภาพนิ่งโมเลกุลน้ำ 3D จาก Blender ตอนเย็นและตอนร้อน |

## โครงสร้าง

| โฟลเดอร์ | เนื้อหา |
|---|---|
| `docs/PREFERENCES.md` | **ความชอบและข้อกำหนดของเจ้าของงาน — อ่านก่อนทำคลิปใหม่** |
| `docs/SESSION_LOG.md` | ลำดับสิ่งที่ทำไปในเซสชันแรก และ feedback ที่ได้รับ |
| `docs/TOOLS.md` | เทียบเครื่องมือ บทเรียน และข้อจำกัดของเครื่องที่ใช้ทำ |
| `docs/SCIENCE.md` | ข้อเท็จจริงที่ตรวจแล้ว และข้อผิดพลาดที่ต้องเลี่ยง |
| `projects/01-100c-mystery-short` | คลิปล่าสุด (HyperFrames) — ดู README ข้างใน |
| `projects/02-first-versions` | เวอร์ชันแรก: HTML/Three.js, Manim, Remotion, Remotion plugin |
| `projects/03-hyperframes-water` | เวอร์ชัน HyperFrames แรก + สคริปต์สังเคราะห์เสียงเดือดและดนตรี |
| `projects/04-blender-hyperframes` | HyperFrames ที่ใช้ฟุตเทจจาก Blender |
| `projects/05-blender-scenes` | สคริปต์ Blender (bpy) ที่เรนเดอร์ฉาก 3D |
| `projects/06-audio` | ดนตรีจากโค้ด (Tone.js) และ TTS ในเครื่อง (Kokoro) |

## ไม่ได้ commit (ไฟล์ใหญ่ หรือสร้างใหม่ได้)

- `node_modules`, เฟรมที่เรนเดอร์จาก Blender, ฟุตเทจ `assets/video` ของ 04, mp4 เวอร์ชันกลางทาง
- โมเดล Kokoro (`kokoro-v1.0.int8.onnx`, `voices-v1.0.bin`) ให้ดาวน์โหลดจาก GitHub release ของ
  [thewh1teagle/kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx/releases) (model-files-v1.0)
- `mix.wav` ของคลิปล่าสุด สร้างใหม่ได้ด้วย `python3 tools/mix.py .`

สคริปต์หลายตัวยังอ้าง path เดิม `/home/claude/...` ของเครื่องที่ใช้ทำ ถ้าย้ายเครื่องต้องแก้ path ก่อน
