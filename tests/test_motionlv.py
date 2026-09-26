# -*- coding: utf-8 -*-
"""Visuals & Motion **အဆင့်** — QC ဂိတ်ကို မထိဘဲ rate ပြောင်းရမည်。

⚠️ Zin: 「ဂိတ် မလျှော့ရ」⇒ `gfx_share` (QC က ဒီဘောင်နဲ့ စစ်သည်) နဲ့
   `sfx_per_min` ceiling ကို **လုံးဝ မရွှေ့ရ**。
⚠️ တိုင်းချက် အခြေခံ: coverage တူပေမယ့် ကတ် ၈ vs ၁၆ က လုံးဝ မတူ ⇒
   **rate** က တကယ့် လက်ကိုင် (「ကြာချိန်နဲ့ ဖြည့်လျှင် slideshow」)。
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))), "core"))
import recipes as RC
import qc as QC

OK = FAIL = 0
def ck(name, cond, extra=""):
    global OK, FAIL
    if cond: OK += 1; print(f"  ✓ {name}")
    else: FAIL += 1; print(f"  ✗ {name}  {extra}")

print("── ① ဂိတ် မရွှေ့ကြောင်း — recipe အားလုံးမှာ ──")
_styles = [k for k in RC.R if k not in RC.HIDDEN]
_bad_share, _bad_ceil, _bad_cap = [], [], []
for st in _styles:
    base = RC.get(st)
    for lv in RC.LEVELS:
        r = RC.motion(base, lv)
        if r.get("gfx_share") != base.get("gfx_share"):
            _bad_share.append((st, lv))
        if r.get("sfx_per_min") is not None and \
           float(r["sfx_per_min"]) > RC.SFX_CEIL + 1e-9:
            _bad_ceil.append((st, lv, r["sfx_per_min"]))
        for k in ("cap_pct", "cap_base", "lufs", "cap_cover", "stroke_w"):
            if base.get(k) is not None and r.get(k) != base.get(k):
                _bad_cap.append((st, lv, k))
ck(f"gfx_share (coverage ဘောင်) မထိ · style {len(_styles)}", not _bad_share, _bad_share[:3])
ck("sfx_per_min က QC ceiling မကျော်", not _bad_ceil, _bad_ceil[:3])
ck("စာတန်း · LUFS ဂိတ်များ မထိ", not _bad_cap, _bad_cap[:3])
ck("SFX_CEIL = qc.SFX_MAX_PER_MIN", RC.SFX_CEIL == QC.SFX_MAX_PER_MIN,
   (RC.SFX_CEIL, QC.SFX_MAX_PER_MIN))

print("\n── ② auto · balanced = recipe ရဲ့ ပုံသေ ──")
b = RC.get("knowledge-v1")   # gfx ပါသော နမူနာ (v2 က engine ပိုင်၍ gfx=0)
for lv in ("auto", "balanced"):
    r = RC.motion(b, lv)
    ck(f"{lv} — gfx · sfx · zoom မပြောင်း",
       r.get("gfx") == b.get("gfx") and r.get("sfx_per_min") == b.get("sfx_per_min")
       and r.get("zoom_amt") == b.get("zoom_amt"))

print("\n── ③ minimal က လျှော့ · high က တင် ──")
mn, hi = RC.motion(b, "minimal"), RC.motion(b, "high")
ck("minimal gfx < ပုံသေ", mn["gfx"] < b["gfx"], (mn["gfx"], b["gfx"]))
ck("minimal punch-in = ၀ (ရုပ် မလှုပ်)", mn.get("zoom_amt") == 0.0, mn.get("zoom_amt"))
ck("minimal SFX < ပုံသေ", mn["sfx_per_min"] < b["sfx_per_min"])
ck("high gfx > ပုံသေ", hi["gfx"] > b["gfx"], (hi["gfx"], b["gfx"]))
ck("high gfx ≤ GFX_CEIL", hi["gfx"] <= RC.GFX_CEIL, hi["gfx"])
ck("high punch-in ≤ ZOOM_CEIL", hi.get("zoom_amt", 0) <= RC.ZOOM_CEIL)
ck("minimal ⇒ စာတန်း မလျှော့ (ဖတ်ရလွယ်မှု ညှိနှိုင်းမရ)",
   mn.get("cap_pct") == b.get("cap_pct"))

print("\n── ④ မသိသော level ⇒ ပုံသေ (ကျဘမ်း မဖြစ်ရ) ──")
for junk in ("", None, "nonsense", "1.0"):
    r = RC.motion(b, junk)
    ck(f"«{junk}» ⇒ gfx မပြောင်း", r.get("gfx") == b.get("gfx"))
# ⚠️ စာလုံးအကြီး/အကွက် ကို **ပုံမှန်ပြုပြီး လက်ခံ**သည် (API က တင်ကြို
#    စစ်ပြီးသားမို့ ဒီမှာ ကျဘမ်း မလုပ်ဘဲ သန့်စင်တာ ပိုကောင်းသည်)。
ck("«HIGH » ⇒ high အဖြစ် ပုံမှန်ပြု", RC.motion(b, "HIGH ")["gfx"] == RC.motion(b, "high")["gfx"])

print("\n── ⑤ မူရင်း recipe ကို မဖျက်စီးရ ──")
_g0 = b["gfx"]; RC.motion(b, "high")
ck("base dict မထိ", b["gfx"] == _g0, (b["gfx"], _g0))

print("\n── ⑥ တီးလုံး ပိတ်ခြင်း — **ရှိပြီးသား** override နဲ့ ──")
# ⚠️ knob အသစ် မဆောက်ရ: `BOUNDS["music"]` ရဲ့ choice ထဲ `None` ပါပြီးသား。
ck("BOUNDS['music'] choice ထဲ None ပါ", None in (RC.BOUNDS["music"][1] or []))
ck("music=None ⇒ လက်ခံ", RC.clean({"music": None}) == {"music": None})
ck("apply ⇒ music = None (တီးလုံး မရှိ)",
   RC.apply("knowledge", {"music": None}).get("music") is None)
ck("music ဘောင်ပြင် ⇒ ပယ်", "music" not in RC.clean({"music": "junk"}))
ck("music_off ဆိုသော knob **မရှိရ** (ထပ်ဆောက်မိတာ)",
   "music_off" not in RC.BOUNDS)

print("\n── ⑦ 「အနည်းဆုံး」ရွေးထားလျှင် **ပြန်မတိုးရ** ──")
# ⚠️ ၂၀၂၆-၀၉-၂၂ audit: အလျားလိုက် format မှာ `gfx < 10` ဆိုလျှင် ၁၀ ဆီ
#    ပြန်တင်သော floor ရှိသည် — `motion("minimal")` က တစ်ဝက် လျှော့ပြီးမှ
#    ဒီ floor က ပြန်တင်လျှင် သုံးစွဲသူ ရွေးချက်က **အလကား** ဖြစ်သည်。
import os as _os
_W = open(_os.path.join(_os.path.dirname(_os.path.dirname(
    _os.path.abspath(__file__))), "worker", "run.py"), encoding="utf-8").read()
ck("floor က `motion_lv != \"minimal\"` နဲ့ ကာထား",
   'if _g0 and _g0 < 10 and motion_lv != "minimal":' in _W)
ck("minimal ဆိုလျှင် အတိုင်း ထားကြောင်း log ရေး",
   "floor 10 မတင်ပါ" in _W)
_mn = RC.motion(RC.get("knowledge-v1"), "minimal")
ck("minimal ⇒ gfx < 10 ဖြစ်နိုင် (floor နဲ့ ပြိုမည်)", _mn["gfx"] < 10, _mn["gfx"])

print(f"\n  ⇒ အောင် {OK} · ကျ {FAIL}")
sys.exit(1 if FAIL else 0)
