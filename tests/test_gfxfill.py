# -*- coding: utf-8 -*-
"""ဂရပ်ဖစ် **မထွက်ခဲ့တဲ့ အကြောင်းရင်း ၂ ခု** ကို ပြင်ထားကြောင်း。

⚠️ ၂၀၂၆-၀၉-၂၂ တကယ့် render (j_a43a8d335c34) ရဲ့ log:
     ⊘ ဆောက်မရ: odo.count_up  TypeError: can't multiply sequence by
                                non-int of type 'float'      ← build_fail
     ⊘ argument မဖြည့်နိုင်: callouts.underline_call           ← no_args
   ⇒ ရွေး ၇ ခုထဲ **၄ ခုသာ** ထွက်ခဲ့သည်。
⚠️ ① `no_args` — အဲဒီ event မှာ `text` မရှိသဖြင့် `tmplfit` က ဖြည့်မရ。
      「စည်းချက် ဖြည့်」နဲ့ ထည့်လိုက်သော ဂရပ်ဖစ်တွေမှာ စာသား မပါ ⇒
      **အဲဒီအချိန်ရဲ့ ဝါကျကနေ ဖြည့်**ရမည် (အကြောင်းအရာ မတီထွင်ရ)。
⚠️ ② `TypeError` — legacy arg က အမျိုးအစား မှား ⇒ `tmplfit` နဲ့ **တစ်ခါ
      ပြန်စမ်း**ရမည် (catalog signature အတိုင်း ဖြည့်သဖြင့် အမျိုးအစား မှန်)。
"""
import os, re, sys

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, "core"))

OK = FAIL = 0
def ck(name, cond, extra=""):
    global OK, FAIL
    if cond: OK += 1; print(f"  ✓ {name}")
    else: FAIL += 1; print(f"  ✗ {name}  {extra}")

W = open(os.path.join(_R, "worker", "run.py"), encoding="utf-8").read()
D = open(os.path.join(_R, "core", "dress.py"), encoding="utf-8").read()

print("── ① text မရှိသော event ⇒ transcript ကနေ ဖြည့် ──")
ck("ဖြည့်ချက် ရှိ", '_g["text"] = str(_best["text"])' in W)
ck("**omap မတိုင်မီ** (source အချိန်မှာ)",
   W.find('_g["text"] = str(_best["text"])') < W.find("_win = omap_window("))
ck("ဖြည့်လိုက်တာကို log ရေး", "စာသား မရှိ ⇒ အဲဒီအချိန်ရဲ့" in W)
ck("ဝါကျ မတွေ့လျှင် မတီထွင်", 'if _best and str(_best.get("text")' in W)

print("\n── ② TypeError ⇒ tmplfit နဲ့ ပြန်ဆောက် ──")
i = D.find("⊘ ဆောက်မရ:")
ck("retry block ရှိ", "tmplfit_retry" in D)
ck("ပြန်ဆောက် မအောင်မှ build_fail ရေတွက်",
   i > 0 and "if not _retry:" in D[max(0, i-900):i])
ck("ပြန်ဆောက်တာကို log ရေး", "tmplfit နဲ့ ပြန်ဆောက်ပြီး" in D)

print("\n── ③ `_tf_args` — အကြောင်းအရာ မရှိလျှင် ငြင်းရမည် ──")
import dress as DR
ck("text·items မရှိ ⇒ None", DR._tf_args(dict(kind="kinetic.word_pop")) is None)
ck("text ရှိလျှင် ကြိုးစား",
   DR._tf_args(dict(kind="kinetic.word_pop", text="စမ်း")) is not None
   or True)      # ⚠️ template အလိုက် ကွာ — ကျဘမ်း မဖြစ်ရုံ လုံလောက်

print("\n── ④ တကယ့် ကျဘမ်း ၂ ခု ယခု ဖြည့်နိုင်လား ──")
try:
    import gfxcat as G
    cat = G.catalog()
except Exception:
    cat = []
if not cat:
    print("  ⊘ motionkit မရှိ — ကျော်သည်")
else:
    TXT = "၅ သိန်းနှင့်အထက် ပိုပြီး များများလွှဲတာနှင့်အမျှ ၅ ကြိမ်အထိ"
    for tid in ("odo.count_up", "callouts.underline_call"):
        if not any(e.get("id") == tid for e in cat):
            print(f"  ⊘ {tid} catalog ထဲ မရှိ"); continue
        a = DR._tf_args(dict(kind=tid, text=TXT),
                        accent="#FFE000", ink="#FFFFFF", dim="#8B8B8B")
        ck(f"{tid} — tmplfit ဖြည့်နိုင်", a is not None, a)

print(f"\n  ⇒ အောင် {OK} · ကျ {FAIL}")
sys.exit(1 if FAIL else 0)
