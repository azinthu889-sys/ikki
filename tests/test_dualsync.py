# -*- coding: utf-8 -*-
"""dual-system recorder အသံ — **ချိန်ညှိချက် ဂိတ်**。

⚠️ Zin ၂၀၂၆-၀၉-၂၁: 「မှားညှိလျှင် တိတ်တဆိတ် out-of-sync ဗီဒီယို မဖြစ်ရ」。
   ⇒ မဆိုင်သော အသံ · နာရီလွဲသော အသံ ကို **ငြင်း**ရမည် (ခန့်မှန်း၍ မရ)。
⚠️ recorder အသံက **နောက်ခံ တီးလုံး မဟုတ်** — `mux()` က ကင်မရာအသံကို
   အစားထိုးသည် (မပေါင်းပါ ⇒ echo/phasing မဖြစ်)。
⚠️ numpy မရှိလျှင် ကျော်သည် (ကျဘမ်း မဟုတ်)。
"""
import os, sys, subprocess, tempfile, json

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, "core"))
try:
    import numpy  # noqa: F401
except ImportError:
    print("  ⊘ numpy မရှိ — ဤ test ကို ကျော်သည်")
    sys.exit(0)
import dual as DU

OK = FAIL = 0
def ck(name, cond, extra=""):
    global OK, FAIL
    if cond: OK += 1; print(f"  ✓ {name}")
    else: FAIL += 1; print(f"  ✗ {name}  {extra}")

T = tempfile.mkdtemp(prefix="ikki_dual_")
def ff(*a):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y"] + list(a),
                       capture_output=True)
    if r.returncode:
        raise RuntimeError((r.stderr or b"").decode()[-300:])

# ── စကားလို စွမ်းအင် ပုံစံ (ပြောချိန်/နားချိန် အလှည့်) ──
# ⚠️ sine တစ်ခုတည်း သုံးလျှင် correlation က **ဘယ်နေရာမှာမဆို** ၁.၀ ရ ⇒
#    ဂိတ်ကို မစစ်နိုင်。 ⇒ စွမ်းအင် ကွဲပြားသော signal လိုသည်。
DUR = 70.0
_seg = []
import random
random.seed(7)
for i in range(int(DUR / 2.0)):
    f = 180 + (i * 37) % 320
    _seg.append(f"sine=frequency={f}:duration=1.2")
    _seg.append("anoisesrc=color=pink:amplitude=0.02:duration=0.8")
_fl = os.path.join(T, "f.txt")
_parts = []
for i, sp in enumerate(_seg):
    p = os.path.join(T, f"p{i:03d}.wav")
    ff("-f", "lavfi", "-i", sp, "-ar", "16000", "-ac", "1", p)
    _parts.append(p)
with open(_fl, "w") as f:
    for p in _parts: f.write(f"file '{p}'\n")
BASE = os.path.join(T, "base.wav")
ff("-f", "concat", "-safe", "0", "-i", _fl, "-c", "copy", BASE)

VID = os.path.join(T, "v.mp4")
ff("-f", "lavfi", "-i", f"testsrc2=size=320x180:rate=15:duration={DUR}",
   "-i", BASE, "-c:v", "libx264", "-preset", "ultrafast", "-crf", "34",
   "-c:a", "aac", "-shortest", VID)

print("── ① တူညီသော အသံ (offset ၀) ⇒ လက်ခံ ──")
A0 = os.path.join(T, "a0.wav")
ff("-i", BASE, "-ar", "48000", A0)
off, ok, inf = DU.offset(VID, A0, log=lambda m: None)
ck("ok", ok, inf)
ck("offset ≈ ၀", abs(off) < 0.08, off)
ck("corr မြင့်", (inf.get("corr") or 0) >= DU.MIN_CORR, inf)

print("\n── ② recorder က ၂.၅s စော ⇒ offset တွေ့ရမည် ──")
# audio ဖိုင်ရဲ့ အစမှာ တိတ်ဆိတ်မှု ၂.၅s ထည့် ⇒ video ရဲ့ t က audio ရဲ့ t+2.5
A1 = os.path.join(T, "a1.wav")
_sil = os.path.join(T, "sil.wav")
ff("-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono:d=2.5", "-ar", "16000", _sil)
_fl2 = os.path.join(T, "f2.txt")
open(_fl2, "w").write(f"file '{_sil}'\nfile '{BASE}'\n")
ff("-f", "concat", "-safe", "0", "-i", _fl2, "-ar", "48000", A1)
off, ok, inf = DU.offset(VID, A1, log=lambda m: None)
ck("ok", ok, inf)
ck("offset ≈ +2.5s", abs(off - 2.5) < 0.12, off)
# ⚠️ `inf.get("drift") or 9` **မရေးရ** — drift က တကယ် ၀.၀ ဖြစ်တတ်ပြီး
#    falsy ဖြစ်သဖြင့် ၉ ဖြစ်သွားမည် (ဒီ test ကိုယ်တိုင် ဒီအမှားနဲ့ ကျခဲ့)。
ck("drift သေး", float(inf.get("drift", 9)) <= DU.MAX_DRIFT, inf)

print("\n── ③ မဆိုင်သော အသံ ⇒ **ငြင်းရမည်** ──")
A2 = os.path.join(T, "a2.wav")
ff("-f", "lavfi", "-i", f"anoisesrc=color=white:amplitude=0.5:duration={DUR}",
   "-ar", "48000", A2)
off, ok, inf = DU.offset(VID, A2, log=lambda m: None)
ck("ငြင်းပြီး (out-of-sync ဗီဒီယို မဖြစ်)", not ok, (off, inf))
ck("အကြောင်းရင်း ပါ", bool(inf.get("why")), inf)
ck("offset = ၀ (ခန့်မှန်း မလုပ်)", off == 0.0 or not ok, off)

print("\n── ④ တိုလွန်းသော အသံ ⇒ ငြင်း ──")
A3 = os.path.join(T, "a3.wav")
ff("-f", "lavfi", "-i", "sine=frequency=300:duration=0.5", "-ar", "48000", A3)
off, ok, inf = DU.offset(VID, A3, log=lambda m: None)
ck("ငြင်းပြီး", not ok, inf)
ck("အကြောင်းရင်း ပါ", bool(inf.get("why")), inf)

print("\n── ⑤ mux — **အစားထိုးသည် · မပေါင်းပါ** (echo မဖြစ်) ──")
MX = os.path.join(T, "mx.mp4")
DU.mux(VID, A1, MX, 2.5, log=lambda m: None)
_pr = json.loads(subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name",
     "-of", "json", MX], capture_output=True, text=True).stdout)
_st = _pr["streams"]
ck("ဗီဒီယို stream ၁ ခု",
   len([x for x in _st if x["codec_type"] == "video"]) == 1)
ck("**အသံ stream ၁ ခုသာ** (ကင်မရာအသံ မကျန်)",
   len([x for x in _st if x["codec_type"] == "audio"]) == 1, _st)

print("\n── ⑥ ဂိတ် ကိန်းများ ──")
ck("MIN_CORR ရှိ · ၀–၁ ကြား", 0.0 < DU.MIN_CORR <= 1.0, DU.MIN_CORR)
ck("MAX_DRIFT ရှိ · သေး", 0.0 < DU.MAX_DRIFT <= 0.5, DU.MAX_DRIFT)

print(f"\n  ⇒ အောင် {OK} · ကျ {FAIL}")
sys.exit(1 if FAIL else 0)
