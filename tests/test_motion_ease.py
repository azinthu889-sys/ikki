# -*- coding: utf-8 -*-
"""ဂရပ်ဖစ် clip ရဲ့ **ဝင်/ထွက် ချိန်နဲ့ ease** — QC ဂိတ် အောင်ရမည်။

⚠️ ၂၀၂၆-၀၉-၂၃ တကယ့် render (Zin: 「ထုတ်လို့ မရပါ · QC မအောင်: motion_exit,
   motion_ease」) ရဲ့ တိုင်းချက်:
     ဝင် ၀.၂၆၇–၀.၇၀၀s ✓ · **ထွက် ၀.၁၀၀s ✗** (ဘောင် ၀.၁၃၃–၀.၂၆၇)
     **ease ၀.၁၅ ✗** (ဂိတ် ≥၀.၃၀)
   အကြောင်းရင်း — compositor က ဂရပ်ဖစ် clip တွေမှာ fade **လုံးဝ မတပ်**ခဲ့
   (`overlay=0:0` သာ) ⇒ template ရဲ့ ကိုယ်ပိုင် ၃ ဖရိမ်း (၀.၁၀s) မျဉ်းဖြောင့်
   ramp ကိုသာ ရသည်。
⚠️ **ဂိတ်ကို မလျှော့ရ** — `_ease_alpha()` နဲ့ ease-out alpha ramp တပ်ပြီး
   ဖြေရှင်းသည်။ ကိန်း (din=1.6 · pw=5 · dout=0.20) ကို ဖြစ်နိုင်ချေ ၂၀ မျိုး
   စမ်းပြီး ရွေးထားသည်။
⚠️ template ရဲ့ **ကိုယ်ပိုင် ramp ရှည်လျှင်** ကျွန်တော်တို့ curve ကို လွှမ်းမိုး၍
   ease ကျသည် (case ②) ⇒ din ရှည်ရမည် · clamp က `dur*0.55`。
⚠️ ffmpeg/PIL/numpy မရှိလျှင် ကျော်သည်။
"""
import os, shutil, subprocess, sys, tempfile

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, "core"))
sys.path.insert(0, os.path.join(_R, "worker"))

if not shutil.which("ffmpeg"):
    print("  ⊘ ffmpeg မရှိ — ကျော်သည်"); sys.exit(0)
try:
    import numpy as np
    from PIL import Image
except ImportError:
    print("  ⊘ numpy/PIL မရှိ — ကျော်သည်"); sys.exit(0)

import importlib.util as _iu
_sp = _iu.spec_from_file_location("wrun", os.path.join(_R, "worker", "run.py"))
W = _iu.module_from_spec(_sp)
try:
    _sp.loader.exec_module(W)
except Exception as e:          # worker က ပြင်ပ dependency လိုနိုင်သည်
    print(f"  ⊘ worker import မရ ({type(e).__name__}) — ကျော်သည်"); sys.exit(0)
import motmeas as MM

OK = FAIL = 0
def ck(name, cond, extra=""):
    global OK, FAIL
    if cond: OK += 1; print(f"  ✓ {name}")
    else: FAIL += 1; print(f"  ✗ {name}  {extra}")


def _clip(d, name, dur, ramp, fps=30, w=320, h=180):
    """template လို alpha clip — `ramp` ဖရိမ်း မျဉ်းဖြောင့် ဝင်/ထွက်။"""
    fd = os.path.join(d, "f_" + name)
    os.makedirs(fd, exist_ok=True)
    n = int(dur * fps)
    for i in range(n):
        if i < ramp: al = int(255 * (i + 1) / float(ramp))
        elif i >= n - ramp: al = int(255 * (n - i) / float(ramp))
        else: al = 255
        a = np.zeros((h, w, 4), np.uint8)
        a[40:120, 30:290, :3] = 230
        a[40:120, 30:290, 3] = al
        Image.fromarray(a).save(os.path.join(fd, "f%04d.png" % i))
    out = os.path.join(d, name + ".mov")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps),
                    "-i", os.path.join(fd, "f%04d.png"),
                    "-c:v", "qtrle", "-pix_fmt", "argb", out], check=True)
    return out


print("── ① ကိန်းများ ရှိကြောင်း ──")
ck("EASE_DIN · EASE_PW · EASE_DOUT ရှိ",
   all(hasattr(W, k) for k in ("EASE_DIN", "EASE_PW", "EASE_DOUT")))
ck("`_ease_alpha` ရှိ", hasattr(W, "_ease_alpha"))
_f = W._ease_alpha("0:v", "o", 0.0, 3.2)
ck("geq နဲ့ alpha ကို မြှောက်", "alpha(X,Y)*" in _f, _f[:80])
ck("ထွက်ချိန် fade ပါ", "fade=t=out" in _f)
# ⚠️ `-itsoffset` သုံးသဖြင့် T က timeline အချိန် ⇒ clip အစကို နုတ်ရမည်
_f2 = W._ease_alpha("0:v", "o", 10.0, 13.2)
ck("clip အစကို နုတ်ထား (T-a)", "(T-10.000)" in _f2, _f2[:110])

print("\n── ② **clip ဖိုင်ကိုယ်တိုင်** မှာ တပ်ထားကြောင်း ──")
# ⚠️ QC (`motmeas.summary`) က composite ထွက်ဖိုင် မဟုတ်ဘဲ **overlay clip .mov**
#    ကို တိုက်ရိုက် တိုင်းသည် ⇒ composite filter chain မှာ တပ်လျှင်
#    တိုင်းချက်ထဲ **ဘယ်တော့မှ မပါ** (၂၀၂၆-၀၉-၂၃ render ၂ ခါ ကျပြီးမှ တွေ့)။
_src = open(os.path.join(_R, "worker", "run.py"), encoding="utf-8").read()
ck("`_ease_clip` ရှိ", hasattr(W, "_ease_clip"))
ck("gmov clip တိုင်းကို `_ease_clip` နဲ့ ပြင်", "_ease_clip(m_" in _src)
ck("composite filter မှာ **မတပ်တော့** (နှစ်ထပ် မဖြစ်စေရန်)",
   '_ease_alpha(f"{n}:v"' not in _src)
ck("QC က clip .mov ကို တိုင်းကြောင်း", "[x[1] for x in (gmov or [])]" in _src)

print("\n── ③ တကယ် render ပြီး ဂိတ်နဲ့ တိုင်း ──")
print(f"     ဂိတ် — ဝင် {MM.ENTER_BAND} · ထွက် {MM.EXIT_BAND} · ease ≥{MM.EASE_MIN}")
_d = tempfile.mkdtemp(prefix="ikki_ease_")
try:
    CASES = [("ramp3", 3.2, 3, "ramp တို (၃ ဖရိမ်း)"),
             ("ramp10", 3.2, 10, "ramp ရှည် (၁၀ ဖရိမ်း)"),
             ("short", 1.6, 3, "clip တို ၁.၆s"),
             ("long", 6.0, 3, "clip ရှည် ၆.၀s")]
    for nm, dur, ramp, label in CASES:
        src = _clip(_d, nm, dur, ramp)
        # ⚠️ **worker ရဲ့ တကယ့် လမ်းကြောင်း** ကို စစ်ရမည် — filter string
        #    တစ်ခုတည်း စစ်လျှင် 「composite မှာ တပ်မိပြီး QC မမြင်」ဆိုသော
        #    အမှားမျိုး ထပ်ဖြစ်နိုင်သည်။
        out = W._ease_clip(src, dur, log=None)
        if out == src:
            ck(label, False, "ease ramp မတပ်နိုင် (ဖိုင် မလဲ)"); continue
        m = MM.measure(out)
        if not m:
            ck(label, False, "မတိုင်းရ"); continue
        ein = MM.ENTER_BAND[0] <= (m["in_s"] or 0) <= MM.ENTER_BAND[1]
        eo = MM.EXIT_BAND[0] <= (m["out_s"] or 0) <= MM.EXIT_BAND[1]
        ez = (m["ease"] or 0) >= MM.EASE_MIN
        print(f"     {label}: ဝင် {m['in_s']} · ထွက် {m['out_s']} · ease {m['ease']}")
        ck(f"{label} — ဝင်ချိန် ဘောင်ထဲ", ein, m["in_s"])
        ck(f"{label} — ထွက်ချိန် ဘောင်ထဲ", eo, m["out_s"])
        ck(f"{label} — ease ≥ {MM.EASE_MIN}", ez, m["ease"])

    print("\n── ④ filter မတပ်လျှင် **ကျရမည်** (ဂိတ် တကယ် အလုပ်လုပ်ကြောင်း) ──")
    raw = _clip(_d, "baseline", 3.2, 3)      # ⚠️ `_ease_clip` က မူရင်းကို ဖျက်သည်
    m0 = MM.measure(raw)
    ck("မူရင်း ထွက်ချိန် ဘောင် အောက်",
       (m0["out_s"] or 0) < MM.EXIT_BAND[0], m0["out_s"])
    ck("မူရင်း ease မလုံလောက်",
       (m0["ease"] or 0) < MM.EASE_MIN, m0["ease"])
finally:
    shutil.rmtree(_d, ignore_errors=True)

print(f"\n  ⇒ အောင် {OK} · ကျ {FAIL}")
sys.exit(1 if FAIL else 0)
