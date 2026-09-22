# -*- coding: utf-8 -*-
"""`tmplfit` ကို `dress.track` ထဲ ချိတ်ထားကြောင်း — **Motion Kit အသုံးချမှု**。

⚠️ ၂၀၂၆-၀၉-၂၂ တိုင်းချက်: engine မှာ `ARGS` ၁၂ + `gfx_args.json` ၅၂ ပဲ
   ရှိသဖြင့် overlay template ၃၇၇ ခုထဲက **~၆၄ ခုသာ** ဖြည့်နိုင်ခဲ့သည်。
   log မှာ 「⊘ argument မဖြည့်နိုင်: … (ဂဏန်း/စာရင်း param လိုသည်)」ဟု
   တကယ် ပေါ်ခဲ့ပြီး ဂရပ်ဖစ် ရွေးထားတာတွေ ပယ်ခံခဲ့သည်。
⚠️ **အကြောင်းအရာ မတီထွင်ရ** — `items` မရှိလျှင် စာရင်း template ငြင်းရမည်。
"""
import os, sys, inspect

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, "core"))
import dress as DR
import gfxcat as G

OK = FAIL = 0
def ck(name, cond, extra=""):
    global OK, FAIL
    if cond: OK += 1; print(f"  ✓ {name}")
    else: FAIL += 1; print(f"  ✗ {name}  {extra}")

print("── ① ချိတ်ထားကြောင်း ──")
ck("`_tf_args` ရှိ", hasattr(DR, "_tf_args"))
src = inspect.getsource(DR.track)
ck("`track()` က `_tf_args` ကို ပြန်ဆုတ်လမ်း အဖြစ် ခေါ်", "_tf_args(" in src)
ck("`ARGS`/`_cargs` ပြီးမှ ခေါ် (အစားထိုး မဟုတ်)",
   src.index("_cargs(") < src.index("_tf_args("))

print("\n── ② အကြောင်းအရာ မရှိလျှင် ငြင်းရမည် ──")
ck("text · items မရှိ ⇒ None",
   DR._tf_args(dict(kind="kinetic.word_pop")) is None)
ck("kind မမှန် ⇒ None",
   DR._tf_args(dict(kind="nope.nope", text="စမ်း")) is None)

cat = G.catalog()
if not cat:
    print("  ⊘ motionkit မရှိ — ကျန် test ကျော်သည်")
    print(f"\n  ⇒ အောင် {OK} · ကျ {FAIL}")
    sys.exit(1 if FAIL else 0)

use = [e for e in cat if e.get("category") in G.USE]
TXT = "ဒီအစီအစဉ် ကာလကတော့ စက်တင်ဘာလ ၂၉ ရက်ထိ ဖြစ်ပါတယ်"
fill = []
for e in use:
    try:
        a = DR._tf_args(dict(kind=e["id"], text=TXT),
                        accent="#FFE000", ink="#FFFFFF", dim="#8B8B8B")
    except Exception:
        a = None
    if a: fill.append(e["id"])
print(f"\n── ③ စာသားတစ်ခုတည်းနဲ့ ဖြည့်နိုင်မှု ──")
print(f"     {len(fill)}/{len(use)} ({100*len(fill)/len(use):.0f}%)")
# ⚠️ ယခင် engine က ~၆၄ ⇒ အထူးတလည် တိုးရမည်
ck("၁၂၀ ခု အထက် ဖြည့်နိုင် (ယခင် ~၆၄)", len(fill) >= 120, len(fill))
ck("kwargs က dict", all(isinstance(DR._tf_args(dict(kind=t, text=TXT),
   accent="#FFE000", ink="#FFF", dim="#888"), dict) for t in fill[:5]))

print("\n── ④ စာရင်း ပါလျှင် ပိုရမည် ──")
fill2 = []
for e in use:
    try:
        a = DR._tf_args(dict(kind=e["id"], text=TXT,
                             items=["ဂျပန်မှာ အလုပ်", "ပညာသင်", "ဗီဇာ"]),
                        accent="#FFE000", ink="#FFFFFF", dim="#8B8B8B")
    except Exception:
        a = None
    if a: fill2.append(e["id"])
print(f"     {len(fill2)}/{len(use)} ({100*len(fill2)/len(use):.0f}%)")
ck("စာရင်းပါလျှင် ပို ဖြည့်နိုင်", len(fill2) > len(fill), (len(fill2), len(fill)))

print("\n── ⑤ render စစ်ပြီးသားနဲ့ ခြားနား ──")
try:
    ok = {x.strip() for x in open(os.path.join(_R, "assets", "gfx_ok.txt"),
                                  encoding="utf-8")
          if x.strip() and not x.lstrip().startswith("#")}
except OSError:
    ok = set()
_v = [t for t in fill if t in ok]
print(f"     ဖြည့်နိုင် ∩ စစ်ပြီး = {len(_v)}")
ck("စစ်ပြီးသား ၈၀ ခု အထက် ရနိုင်", len(_v) >= 80, len(_v))

print(f"\n  ⇒ အောင် {OK} · ကျ {FAIL}")
sys.exit(1 if FAIL else 0)
