# -*- coding: utf-8 -*-
"""စာတန်း အရွယ် — **ပြောင်းပြန် မဖြစ်ရ** · သုံးစွဲသူ ရွေးချက် မလွှမ်းရ。

⚠️ ၂၀၂၆-၀၉-၂၂ (j_a43a8d335c34 · `cap=xl`): အလျားလိုက် format မှာ
   `pct > 0.06` ဆိုလျှင် `0.045` ဖြစ်စေခဲ့သဖြင့် —
     xs 0.043→0.043 · s 0.053→0.053 · m 0.065→**0.045** ·
     l 0.080→**0.045** · xl 0.095→**0.045**
   ⇒ `xl` ရွေးထားပါလျက် `s` ထက် **သေး**သည် (Zin: 「စာတန်း သေးနေတယ်」)。
⚠️ မျက်နှာ ဖုံးမှုက တကယ့် ကန့်သတ်ချက် (၂၀၂၆-၀၉-၁၇) ⇒ **ceiling** သာ ဖြစ်ရမည်。
"""
import os, re, sys

_R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_R, "core"))
import recipes as RC

OK = FAIL = 0
def ck(name, cond, extra=""):
    global OK, FAIL
    if cond: OK += 1; print(f"  ✓ {name}")
    else: FAIL += 1; print(f"  ✗ {name}  {extra}")

W = open(os.path.join(_R, "worker", "run.py"), encoding="utf-8").read()

print("── ① ceiling ကိန်း ရှိရမည် (အစားထိုး မဟုတ်) ──")
ck("`CAP_H_MAX` ရှိ", "CAP_H_MAX" in W)
m = re.search(r"CAP_H_MAX\s*=\s*([0-9.]+)", W)
cap = float(m.group(1)) if m else None
ck("တန်ဖိုး ၀.၀၅–၀.၀၈ ကြား", cap is not None and 0.05 <= cap <= 0.08, cap)
ck("`pct = 0.045` အတိအကျ သတ်မှတ်ချက် မရှိ",
   not re.search(r"pct\s*=\s*0\.045", W))
ck("ceiling နဲ့ ကန့်သတ်", re.search(r"pct\s*=\s*CAP_H_MAX", W) is not None)

print("\n── ② အရွယ် အစဉ် **တက်လာရမည်** ──")
prev, bad = -1.0, []
for k, v in RC.CAPSIZE.items():
    got = min(v[0], cap)
    if got < prev - 1e-9: bad.append((k, got, prev))
    prev = got
ck("ပြောင်းပြန် မရှိ", not bad, bad)

print("\n── ③ ကြီးတာ ရွေးလျှင် သေးတာထက် မငယ်ရ ──")
sz = {k: min(v[0], cap) for k, v in RC.CAPSIZE.items()}
ck("xl ≥ s", sz["xl"] >= sz["s"], (sz["xl"], sz["s"]))
ck("l ≥ s", sz["l"] >= sz["s"])
ck("m ≥ s", sz["m"] >= sz["s"])
ck("xl က ယခင် ၀.၀၄၅ ထက် ကြီး", sz["xl"] > 0.045, sz["xl"])

print("\n── ④ မျက်နှာ ဖုံးမှု ကန့်သတ်ချက် ဆက်တည်ရမည် ──")
ck("ဘယ်ရွေးချက်မှ ceiling မကျော်", all(v <= cap + 1e-9 for v in sz.values()), sz)

print("\n── ⑤ ဖောင့် — သုံးစွဲသူ ရွေးထားလျှင် မလွှမ်းရ ──")
i = W.find('rc["mmf"] = "Pyidaungsu-Bold"')
ck("ရွေးမထားမှသာ သတ်မှတ်",
   i > 0 and 'if not (job.get("font") or "").strip():' in W[max(0, i-260):i])

print(f"\n  ⇒ အောင် {OK} · ကျ {FAIL}")
sys.exit(1 if FAIL else 0)
