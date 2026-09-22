# -*- coding: utf-8 -*-
"""`dress.track` ရဲ့ `avoid` — **၂ ခု နဲ့ ၄ ခု နှစ်မျိုးလုံး** ကိုင်ရမည်။

⚠️ ၂၀၂၆-၀၉-၂၂ (j_3929e0a70565): worker က `subject_box` ပေါ်လာပြီးနောက်
   `avoid=(y0, y1, sx0, sx1)` ၄ ခု ပို့သည် — ဒါပေမယ့် `track()` က
   `ay0, ay1 = avoid2` ဆိုပြီး **၂ ခု** ဖြုတ်သဖြင့်
   「too many values to unpack (expected 2)」နဲ့ ကျကာ **ဂရပ်ဖစ် လုံးဝ
   မထွက်**ခဲ့သည် (Zin: 「စောက်တလွဲ ဖြစ်နေတာလဲ」)。
⚠️ ဘေးမှာ ချသော/အနားသတ်သာ template တွေက `avoid2=None` ဖြစ်သဖြင့်
   **တချို့ render မှာသာ** ကျသည် ⇒ ဖုံးနေခဲ့သည်。
"""
import os, sys, inspect, re

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))), "core"))
import dress as DR

OK = FAIL = 0
def ck(name, cond, extra=""):
    global OK, FAIL
    if cond: OK += 1; print(f"  ✓ {name}")
    else: FAIL += 1; print(f"  ✗ {name}  {extra}")

src = inspect.getsource(DR.track)
print("── ① `avoid` ကို ၂ ခု အတိအကျ ဖြုတ်တာ **မရှိရ** ──")
bad = re.findall(r"^\s*[a-z_]+\s*,\s*[a-z_]+\s*=\s*avoid2?\s*$", src, re.M)
ck("`x, y = avoid` ပုံစံ မရှိ", not bad, bad)
ck("index နဲ့ ယူထား", "avoid2[0]" in src and "avoid2[1]" in src)

print("\n── ② tuple ၂ ခု · ၄ ခု နှစ်မျိုးလုံး ဖြုတ်နိုင်ကြောင်း ──")
def take2(av):
    return float(av[0]), float(av[1])
for av in ((151, 664), (151, 664, 440, 1560), [151.0, 664.0],
           (151, 664, 440, 1560, 9)):
    try:
        a, b = take2(av)
        ck(f"len={len(av)} ⇒ ({a:.0f}, {b:.0f})", (a, b) == (151.0, 664.0))
    except Exception as e:
        ck(f"len={len(av)}", False, f"{type(e).__name__}: {e}")

print("\n── ③ `swap_fit` · `fits` လည်း ၄ ခု ကို ခံနိုင်ရမည် ──")
for fn in ("swap_fit", "fits"):
    f = getattr(DR, fn, None)
    if f is None: ck(f"{fn} ရှိ", False); continue
    s2 = inspect.getsource(f)
    b2 = re.findall(r"^\s*[a-z_]+\s*,\s*[a-z_]+\s*=\s*avoid\s*$", s2, re.M)
    ck(f"{fn} — `x, y = avoid` မရှိ", not b2, b2)

print("\n── ④ ကျဘမ်းဖြစ်လျှင် **အကြောင်းရင်း ပြရမည်** (worker) ──")
_w = open(os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "worker", "run.py"), encoding="utf-8").read()
i = _w.find("⚠️ ဂရပ်ဖစ် မရ:")
ck("ဂရပ်ဖစ် ကျဘမ်း handler မှာ traceback ပါ",
   i > 0 and "traceback.format_exc()" in _w[i:i+500])
ck("REPORT မှာ မှတ်ထား", i > 0 and 'REPORT["gfx_error"]' in _w[i:i+500])

print(f"\n  ⇒ အောင် {OK} · ကျ {FAIL}")
sys.exit(1 if FAIL else 0)
